"""Catálogo de produtos: SKU -> preço unitário."""
PRECOS = {"A1": 10.00, "B2": 0.05, "C3": 250.00}


def preco_unitario(sku):
    return PRECOS[sku]
