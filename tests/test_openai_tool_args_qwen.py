# -*- coding: utf-8 -*-
"""Tool-call history sent to an OpenAI-compatible local server (v3.1.12).

Regression: llama.cpp's Qwen chat template renders tool_call.arguments with
|items, which requires a mapping. Sending the standard JSON string made the
server answer 500 (TypeError: Can only get item pairs from a mapping), seen in
the cloud run with Qwen3.5-4B. The request must carry arguments as an object.
"""
import importlib.util
import io
import json
import os
import sys
from unittest import mock

_spec = importlib.util.spec_from_file_location(
    "ollama_agent", os.path.join(os.path.dirname(__file__), "..", "ollama_agent.py"))
sys.argv = ["test"]
_mod = importlib.util.module_from_spec(_spec)
try:
    _spec.loader.exec_module(_mod)
except SystemExit:
    pass


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _captured_body(messages):
    captured = {}

    def fake_urlopen(req, timeout=None):
        captured["body"] = json.loads(req.data.decode("utf-8"))
        return _Resp(json.dumps({"choices": [{"message": {"content": "ok"}}]}).encode())

    lb = {"type": "openai", "base_url": "http://127.0.0.1:8080/v1", "api_key": ""}
    with mock.patch.object(_mod.urllib.request, "urlopen", fake_urlopen):
        _mod._call_openai_local(lb, "m", messages, [], False, None, None)
    return captured["body"]


def test_history_tool_arguments_are_objects():
    messages = [
        {"role": "user", "content": "Liste src"},
        {"role": "assistant", "content": "",
         "tool_calls": [{"id": "c1", "type": "function",
                         "function": {"name": "list_dir", "arguments": {"path": "src"}}}]},
        {"role": "tool", "content": "a.py", "tool_call_id": "c1"},
    ]
    body = _captured_body(messages)
    sent = [m for m in body["messages"] if m.get("tool_calls")][0]["tool_calls"][0]
    assert sent["function"]["arguments"] == {"path": "src"}


def test_string_arguments_are_parsed_to_objects():
    messages = [
        {"role": "user", "content": "Liste src"},
        {"role": "assistant", "content": "",
         "tool_calls": [{"id": "c1", "type": "function",
                         "function": {"name": "list_dir", "arguments": '{"path": "src"}'}}]},
        {"role": "tool", "content": "a.py", "tool_call_id": "c1"},
    ]
    body = _captured_body(messages)
    sent = [m for m in body["messages"] if m.get("tool_calls")][0]["tool_calls"][0]
    assert sent["function"]["arguments"] == {"path": "src"}
