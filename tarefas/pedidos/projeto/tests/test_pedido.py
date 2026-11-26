import pytest

from carrinho import Carrinho
from desconto import taxa_desconto
from pedido import fechar_pedido


def test_add_acumula_quantidade():
    c = Carrinho()
    c.add("B2", 2)
    c.add("B2", 3)
    assert c.itens["B2"] == 5


def test_remove_zera_e_apaga():
    c = Carrinho()
    c.add("B2", 2)
    c.remove("B2", 2)
    assert "B2" not in c.itens


def test_desconto_comeca_em_200():
    assert taxa_desconto(200) == 0.05


def test_sem_desconto_abaixo_de_200():
    assert taxa_desconto(199.99) == 0.0


def test_pedido_com_desconto_de_5_por_cento():
    c = Carrinho()
    c.add("C3", 1)
    r = fechar_pedido(c)
    assert r == {"subtotal": 250.0, "desconto": 12.5, "total": 237.5}


def test_carrinho_vazio_levanta_erro():
    with pytest.raises(ValueError):
        fechar_pedido(Carrinho())


def test_soma_flutuante_arredonda_total():
    c = Carrinho()
    c.add("B2", 6)  # 0,05 * 6 = 0,30000000000000004 na aritmética de ponto flutuante
    assert fechar_pedido(c)["total"] == 0.3
