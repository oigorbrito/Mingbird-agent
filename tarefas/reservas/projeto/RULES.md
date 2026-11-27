# Regras do sistema de reservas de salas

1. **Duração:** uma reserva tem início e fim (em horas, como número). O fim deve ser maior que o início; senão é `ValueError`.
2. **Conflito:** não pode haver reserva com sobreposição na mesma sala. Os intervalos são semiabertos: uma reserva que termina às 10h não conflita com outra que começa às 10h.
3. **Preço:** R$ 30,00 por hora. Reservas de 4 horas ou mais ganham 10% de desconto sobre o total.
4. **Cancelamento** (horas de antecedência em relação ao início da reserva):
   - 24 horas ou mais: sem taxa (0%);
   - de 2 a menos de 24 horas: taxa de 50% do valor;
   - menos de 2 horas: taxa de 100% do valor.
5. **Valores em reais** são arredondados para 2 casas decimais.
