"""Fechamento de pedido."""
from desconto import taxa_desconto


def fechar_pedido(carrinho):
    subtotal = carrinho.subtotal()
    if not carrinho.itens:
        raise ValueError("carrinho vazio")
    taxa = taxa_desconto(subtotal)
    desconto = subtotal * taxa
    total = round(subtotal - desconto, 2)
    return {"subtotal": round(subtotal, 2), "desconto": round(desconto, 2), "total": total}
