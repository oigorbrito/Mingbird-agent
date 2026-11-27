"""Preço de reservas."""

VALOR_HORA = 30.00


def valor_reserva(horas):
    total = VALOR_HORA * horas
    if horas > 4:
        total = total * 0.9
    return total
