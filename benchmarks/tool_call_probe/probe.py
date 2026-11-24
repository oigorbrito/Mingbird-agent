#!/usr/bin/env python3
"""Tool-call validity + speed probe for local Ollama models.

Stdlib only (runs on a stock Python 3.10+ install, no pip needed).

For each model it sends a fixed set of tasks through Ollama's /api/chat with a
small tool schema (the same tool names/args the agent uses), then checks each
returned tool call deterministically:
  - a tool call was emitted at all
  - the tool name is one of the offered tools
  - all required arguments are present with the right JSON type
  - the expected tool was chosen (where the task has one correct tool)
  - for edit_file / create_file the path matches the task

Speed comes from Ollama's own counters (eval_count / eval_duration), plus wall time.

Usage:
  python probe.py --models qwen3.5:4b qwen3.5:2b gemma3:4b --runs 3
  python probe.py --models qwen3.5:4b --host http://127.0.0.1:11434 --num-ctx 8192
  python probe.py --models qwen3.5:4b --out results.json

Reproducibility: temperature 0, think disabled, fixed prompts, fixed num_ctx.
Output: a per-model summary on stdout and a JSON file with every raw response.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
import urllib.error
import urllib.request

# ---- tool schema (mirrors the agent's core tools) -------------------------
def _fn(name, desc, props, required):
    return {"type": "function", "function": {
        "name": name, "description": desc,
        "parameters": {"type": "object", "properties": props, "required": required}}}

TOOLS = [
    _fn("read_file", "Read a file's content", {"path": {"type": "string"}}, ["path"]),
    _fn("create_file", "Create or overwrite a file",
        {"path": {"type": "string"}, "content": {"type": "string"}}, ["path", "content"]),
    _fn("edit_file", "Find-and-replace text in a file",
        {"path": {"type": "string"}, "old": {"type": "string"}, "new": {"type": "string"}},
        ["path", "old", "new"]),
    _fn("list_dir", "List a directory", {"path": {"type": "string"}}, ["path"]),
    _fn("run_bash", "Run a shell command (cwd = workspace)",
        {"command": {"type": "string"}}, ["command"]),
    _fn("finish", "Declare the task finished with a summary",
        {"summary": {"type": "string"}}, ["summary"]),
]
TOOL_NAMES = {t["function"]["name"] for t in TOOLS}

# ---- fixed tasks -----------------------------------------------------------
# expect: the tool that must be chosen; args: {key: required type or exact value}
TASKS = [
    {"id": "T1_read", "prompt": "Mostre o conteúdo do arquivo notas.txt.",
     "expect_tool": "read_file", "args": {"path": "notas.txt"}},
    {"id": "T2_create", "prompt": "Crie o arquivo hello.py contendo exatamente: print('oi')",
     "expect_tool": "create_file", "args": {"path": "hello.py", "content": "print('oi')"}},
    {"id": "T3_edit", "prompt": "No arquivo config.ini, troque o texto 'debug=false' por 'debug=true'.",
     "expect_tool": "edit_file", "args": {"path": "config.ini", "old": "debug=false", "new": "debug=true"}},
    {"id": "T4_list", "prompt": "Liste os arquivos da pasta src.",
     "expect_tool": "list_dir", "args": {"path": "src"}},
    {"id": "T5_bash", "prompt": "Rode o comando 'python -m pytest -q' na pasta do projeto.",
     "expect_tool": "run_bash", "args": {"command": "python -m pytest -q"}},
    {"id": "T6_choose", "prompt": "Diga que terminou, resumindo: 'tudo pronto'.",
     "expect_tool": "finish", "args": {"summary": "tudo pronto"}},
]

SYSTEM = ("Você é um agente que executa tarefas usando ferramentas. "
          "Sempre responda chamando exatamente UMA ferramenta com argumentos válidos.")

TYPE_MAP = {"string": str, "number": (int, float), "boolean": bool, "array": list, "object": dict}


def chat(host, model, prompt, num_ctx, timeout):
    body = {
        "model": model,
        "messages": [{"role": "system", "content": SYSTEM},
                     {"role": "user", "content": prompt}],
        "tools": TOOLS,
        "stream": False,
        "think": False,
        "options": {"temperature": 0, "num_ctx": num_ctx, "num_predict": 512},
    }
    req = urllib.request.Request(host.rstrip("/") + "/api/chat",
                                 data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read().decode("utf-8"))
    data["_wall_s"] = time.time() - t0
    return data


def check(task, resp):
    """Return (ok: bool, reason: str). Deterministic, no model judging."""
    msg = resp.get("message") or {}
    calls = msg.get("tool_calls") or []
    if not calls:
        return False, "no_tool_call"
    fn = calls[0].get("function") or {}
    name = fn.get("name")
    args = fn.get("arguments")
    if isinstance(args, str):  # some runners return arguments as a JSON string
        try:
            args = json.loads(args)
        except json.JSONDecodeError:
            return False, "arguments_not_json"
    if not isinstance(args, dict):
        return False, "arguments_not_object"
    if name not in TOOL_NAMES:
        return False, "unknown_tool"
    if name != task["expect_tool"]:
        return False, f"wrong_tool:{name}"
    schema = next(t for t in TOOLS if t["function"]["name"] == name)["function"]["parameters"]
    for req in schema["required"]:
        if req not in args:
            return False, f"missing_arg:{req}"
    for k, v in args.items():
        spec = schema["properties"].get(k)
        if spec is None:
            return False, f"extra_arg:{k}"
        if not isinstance(v, TYPE_MAP[spec["type"]]):
            return False, f"bad_type:{k}"
    # Value checks: paths and the core string must match what the task asked for.
    for k, want in task["args"].items():
        got = args.get(k)
        if k in ("path",):
            if got != want:
                return False, f"wrong_path:{got}"
        elif k in ("old", "new", "content", "command", "summary"):
            if got.strip() != want.strip():
                return False, f"wrong_value:{k}"
    return True, "ok"


def speed(resp):
    n = resp.get("eval_count") or 0
    d = resp.get("eval_duration") or 0
    tps = (n / (d / 1e9)) if d else None
    return tps, resp.get("_wall_s")


def run_model(host, model, runs, num_ctx, timeout):
    rows = []
    for run in range(runs):
        for task in TASKS:
            row = {"model": model, "run": run, "task": task["id"]}
            try:
                resp = chat(host, model, task["prompt"], num_ctx, timeout)
                ok, reason = check(task, resp)
                tps, wall = speed(resp)
                row.update(ok=ok, reason=reason, tokens_per_s=tps, wall_s=wall,
                           raw=resp)
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                row.update(ok=False, reason=f"transport:{type(e).__name__}",
                           tokens_per_s=None, wall_s=None, raw=str(e))
            rows.append(row)
            print(f"  {model} run{run} {task['id']}: "
                  f"{'OK' if row['ok'] else 'FAIL'} ({row['reason']})", flush=True)
    return rows


def summarize(rows):
    total = len(rows)
    ok = sum(r["ok"] for r in rows)
    reasons = {}
    for r in rows:
        if not r["ok"]:
            reasons[r["reason"]] = reasons.get(r["reason"], 0) + 1
    tps = [r["tokens_per_s"] for r in rows if r["tokens_per_s"]]
    walls = [r["wall_s"] for r in rows if r["wall_s"]]
    return {
        "valid_rate": ok / total if total else 0.0,
        "valid": ok, "total": total,
        "failures": reasons,
        "tokens_per_s_median": statistics.median(tps) if tps else None,
        "wall_s_median": statistics.median(walls) if walls else None,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--models", nargs="+", required=True)
    ap.add_argument("--host", default="http://127.0.0.1:11434")
    ap.add_argument("--runs", type=int, default=3, help="repetitions per task (temperature 0, so mostly a stability check)")
    ap.add_argument("--num-ctx", type=int, default=8192)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--out", default="probe_results.json")
    a = ap.parse_args(argv)

    all_rows, summary = [], {}
    for m in a.models:
        print(f"== {m}", flush=True)
        rows = run_model(a.host, m, a.runs, a.num_ctx, a.timeout)
        all_rows += rows
        summary[m] = summarize(rows)

    print("\nmodel                valid_rate  tok/s(med)  wall_s(med)  failures")
    for m, s in summary.items():
        tps = f"{s['tokens_per_s_median']:.1f}" if s["tokens_per_s_median"] else "-"
        wall = f"{s['wall_s_median']:.1f}" if s["wall_s_median"] else "-"
        print(f"{m:20s} {s['valid']:>3}/{s['total']:<3} {s['valid_rate']:.0%}   {tps:>10}  {wall:>11}  {s['failures']}")

    with open(a.out, "w", encoding="utf-8") as f:
        json.dump({"host": a.host, "num_ctx": a.num_ctx, "runs": a.runs,
                   "summary": summary, "rows": all_rows}, f, ensure_ascii=False, indent=2)
    print(f"\nraw results -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
