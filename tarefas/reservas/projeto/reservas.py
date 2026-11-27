"""Agenda de reservas de salas."""


class Agenda:
    def __init__(self):
        self.reservas = []
        self._proximo_id = 1

    def _conflita(self, sala, inicio, fim):
        for r in self.reservas:
            if r["sala"] == sala and r["inicio"] <= fim and inicio <= r["fim"]:
                return True
        return False

    def reservar(self, sala, inicio, fim):
        if fim <= inicio:
            raise ValueError("fim deve ser maior que o início")
        if self._conflita(sala, inicio, fim):
            raise ValueError("conflito com outra reserva")
        rid = self._proximo_id
        self._proximo_id += 1
        self.reservas.append({"id": rid, "sala": sala, "inicio": inicio, "fim": fim})
        return rid

    def buscar(self, rid):
        for r in self.reservas:
            if r["id"] == rid:
                return r
        raise KeyError(rid)
