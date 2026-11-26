"""Testes ocultos: não são entregues ao agente. Validam regras de RULES.md
que os testes visíveis não cobrem."""
import os
import sys

import pytest

# Caminho do projeto a validar: variável PROJETO_DIR (recomendado) ou ../projeto ao lado deste arquivo.
PROJETO = os.environ.get("PROJETO_DIR") or os.path.join(os.path.dirname(__file__), "..", "projeto")
sys.path.insert(0, PROJETO)

import catalogo  # noqa: E402
from carrinho import Carrinho  # noqa: E402
from desconto import taxa_desconto  # noqa: E402
from pedido import fechar_pedido  # noqa: E402


def test_arredondamento_comercial_meio_sobe(monkeypatch):
    # RULES.md 5: 0,125 vira 0,13 (round() do Python daria 0,12)
    monkeypatch.setitem(catalogo.PRECOS, "D4", 0.125)
    c = Carrinho()
    c.add("D4", 1)
    r = fechar_pedido(c)
    assert r["subtotal"] == 0.13
    assert r["total"] == 0.13


def test_desconto_de_10_por_cento_comeca_em_500():
    # RULES.md 3: subtotal >= 500 tem 10%
    assert taxa_desconto(500) == 0.10


def test_pedido_de_500_tem_10_por_cento():
    c = Carrinho()
    c.add("C3", 2)  # 2 x 250 = 500
    assert fechar_pedido(c) == {"subtotal": 500.0, "desconto": 50.0, "total": 450.0}


def test_remove_parcial_mantem_o_restante():
    # RULES.md 2: remover uma parte deixa o restante no carrinho
    c = Carrinho()
    c.add("B2", 3)
    c.remove("B2", 1)
    assert c.itens["B2"] == 2
