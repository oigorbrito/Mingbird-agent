"""Descontos sobre o subtotal."""


def taxa_desconto(subtotal):
    """Taxa de desconto aplicada ao subtotal (ver RULES.md)."""
    if subtotal > 500:
        return 0.10
    if subtotal > 200:
        return 0.05
    return 0.0
