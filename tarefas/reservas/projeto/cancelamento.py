"""Taxa de cancelamento (fração do valor)."""


def taxa_cancelamento(horas_antecedencia):
    if horas_antecedencia > 24:
        return 0.0
    if horas_antecedencia > 2:
        return 0.5
    return 1.0
