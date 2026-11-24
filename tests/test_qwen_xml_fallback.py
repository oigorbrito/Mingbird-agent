# -*- coding: utf-8 -*-
"""Qwen XML tool calls left as text (v3.1.12).

Regression: with llama-cpp-python serving Qwen3.5-4B, the model answered with
<tool_call><function=read_file><parameter=path>notas.txt</parameter></function></tool_call>
inside the text and the server did not convert it, so the agent treated the
turn as having no tool call. try_parse_tool_calls must recover it.
"""
import importlib.util
import os
import sys

_spec = importlib.util.spec_from_file_location(
    "ollama_agent", os.path.join(os.path.dirname(__file__), "..", "ollama_agent.py"))
sys.argv = ["test"]
_mod = importlib.util.module_from_spec(_spec)
try:
    _spec.loader.exec_module(_mod)
except SystemExit:
    pass

# Verbatim shape of the model output captured in the cloud run.
REAL = ("O usuário quer ver o conteúdo do arquivo \"notas.txt\". Vou usar a função read_file.\n"
        "</think>\n\n<tool_call>\n<function=read_file>\n<parameter=path>\nnotas.txt\n</parameter>\n"
        "</function>\n</tool_call>")


def test_recovers_real_qwen_xml_call():
    assert _mod.try_parse_tool_calls(REAL) == [("read_file", {"path": "notas.txt"})]


def test_multi_parameter_and_multiline_values():
    txt = ("<tool_call>\n<function=edit_file>\n<parameter=path>\nconfig.ini\n</parameter>\n"
           "<parameter=old>\ndebug=false\n</parameter>\n<parameter=new>\ndebug=true\n</parameter>\n"
           "</function>\n</tool_call>")
    assert _mod.try_parse_tool_calls(txt) == [
        ("edit_file", {"path": "config.ini", "old": "debug=false", "new": "debug=true"})]


def test_plain_prose_is_not_a_tool_call():
    assert _mod.try_parse_tool_calls("Pronto, o arquivo foi criado.") is None


def test_existing_json_form_still_parses():
    assert _mod.try_parse_tool_calls('{"name": "read_file", "arguments": {"path": "a.txt"}}') == [
        ("read_file", {"path": "a.txt"})]
