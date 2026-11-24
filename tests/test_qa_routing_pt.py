# -*- coding: utf-8 -*-
"""Roteamento pergunta/tarefa em português (v3.1.12).

Regressão: "Crie um arquivo hello.py ..." era classificado como pergunta porque
"hello" (saudação) casava com a palavra inteira no nome do arquivo, e a falta
de verbos imperativos em português deixava a tarefa sem nenhum sinal de tarefa.
Resultado: o modelo era impedido de chamar create_file e o turno terminava sem
arquivo nenhum. Perguntas e saudações genuínas têm de continuar como pergunta.
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


def _qa(text):
    return _mod._is_qa([{"role": "user", "content": text}])


def test_task_with_greeting_word_in_filename_is_task():
    assert _qa("Crie um arquivo hello.py que imprima 'oi'. Depois rode o arquivo e diga o resultado.") is False


def test_portuguese_imperatives_are_tasks():
    for t in ("Corrija o inventory.py para que os testes passem.",
              "Execute o script de testes e me diga o resultado.",
              "Altere o config.ini para debug=true.",
              "Gere um relatório com os totais."):
        assert _qa(t) is False, t


def test_real_greeting_stays_qa():
    assert _qa("oi, tudo bem?") is True


def test_real_question_stays_qa():
    assert _qa("o que é uma lista em Python?") is True
