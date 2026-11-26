# Regras do sistema de pedidos

1. **Carrinho:** adicionar o mesmo SKU mais de uma vez soma as quantidades. A quantidade de cada adição deve ser positiva, senão é `ValueError`.
2. **Remoção:** remover uma quantidade reduz o item. Se a quantidade chegar a zero ou abaixo, o item sai do carrinho.
3. **Desconto sobre o subtotal:**
   - subtotal menor que 200: sem desconto (0%);
   - subtotal maior ou igual a 200: 5%;
   - subtotal maior ou igual a 500: 10%.
4. **Pedido:** fechar um pedido com carrinho vazio é `ValueError`.
5. **Arredondamento:** subtotal, desconto e total do resultado são arredondados para 2 casas decimais com arredondamento comercial, em que a metade sobe (0,125 vira 0,13; 0,124 vira 0,12).
