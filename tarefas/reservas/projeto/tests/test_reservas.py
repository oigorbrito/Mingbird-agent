import pytest

from cancelamento import taxa_cancelamento
from preco import valor_reserva
from reservas import Agenda


def test_reserva_basica_e_busca():
    a = Agenda()
    rid = a.reservar("S1", 9, 11)
    assert a.buscar(rid)["fim"] == 11


def test_conflito_de_horario_levanta_erro():
    a = Agenda()
    a.reservar("S1", 9, 11)
    with pytest.raises(ValueError):
        a.reservar("S1", 10, 12)


def test_salas_diferentes_nao_conflitam():
    a = Agenda()
    a.reservar("S1", 9, 11)
    a.reservar("S2", 9, 11)
    assert len(a.reservas) == 2


def test_fim_antes_do_inicio_levanta_erro():
    with pytest.raises(ValueError):
        Agenda().reservar("S1", 11, 9)


def test_preco_de_2_horas():
    assert valor_reserva(2) == 60.0


def test_preco_de_5_horas_com_desconto():
    assert valor_reserva(5) == pytest.approx(135.0)


def test_cancelamento_48h_sem_taxa():
    assert taxa_cancelamento(48) == 0.0


def test_cancelamento_10h_taxa_de_50():
    assert taxa_cancelamento(10) == 0.5


def test_cancelamento_1h_taxa_total():
    assert taxa_cancelamento(1) == 1.0


def test_reservas_encostadas_na_mesma_sala_sao_permitidas():
    a = Agenda()
    a.reservar("S1", 9, 10)
    assert a.reservar("S1", 10, 11) == 2
