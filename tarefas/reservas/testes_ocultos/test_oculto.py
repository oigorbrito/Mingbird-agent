"""Testes ocultos: não são entregues ao agente. Validam fronteiras das regras
de RULES.md que os testes visíveis não cobrem."""
import os
import sys

import pytest

PROJETO = os.environ.get("PROJETO_DIR") or os.path.join(os.path.dirname(__file__), "..", "projeto")
sys.path.insert(0, PROJETO)

from cancelamento import taxa_cancelamento  # noqa: E402
from preco import valor_reserva  # noqa: E402
from reservas import Agenda  # noqa: E402


def test_reservas_encostadas_em_ordem_invertida_nao_conflitam():
    # RULES.md 2: 10-11 e depois 9-10 na mesma sala também são compatíveis
    a = Agenda()
    a.reservar("S1", 10, 11)
    assert a.reservar("S1", 9, 10) == 2


def test_cancelamento_exatamente_24h_sem_taxa():
    # RULES.md 4: 24 horas ou mais não tem taxa
    assert taxa_cancelamento(24) == 0.0


def test_cancelamento_exatamente_2h_taxa_de_50():
    # RULES.md 4: de 2 a menos de 24 horas tem 50%
    assert taxa_cancelamento(2) == 0.5


def test_desconto_comeca_em_4_horas():
    # RULES.md 3: 4 horas ou mais ganham 10%
    assert valor_reserva(4) == pytest.approx(108.0)
