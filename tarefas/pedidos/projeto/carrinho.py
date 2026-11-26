"""Carrinho de compras."""
from catalogo import preco_unitario


class Carrinho:
    def __init__(self):
        self.itens = {}

    def add(self, sku, qtd=1):
        if qtd <= 0:
            raise ValueError("quantidade deve ser positiva")
        preco_unitario(sku)  # valida o SKU
        self.itens[sku] = qtd

    def remove(self, sku, qtd=1):
        if sku not in self.itens:
            raise KeyError(sku)
        self.itens[sku] -= qtd
        if self.itens[sku] <= 0:
            del self.itens[sku]

    def subtotal(self):
        return sum(preco_unitario(s) * q for s, q in self.itens.items())
