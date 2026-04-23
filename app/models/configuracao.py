from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Configuracoes:
    """Snapshot tipado da aba `configuracoes`.

    Os valores numéricos são coagidos a float/int; defaults seguem o PRD (Seção 6.2).
    """

    valor_mensalidade_atleta: float = 55.0
    valor_mensalidade_associado: float = 15.0
    valor_multa_atraso: float = 7.0
    dia_vencimento: int = 10
    nome_time: str = "Furiosos Cheer"

    def valor_mensalidade(self, tipo: str) -> float:
        if tipo == "atleta":
            return self.valor_mensalidade_atleta
        if tipo == "associado":
            return self.valor_mensalidade_associado
        raise ValueError(f"Tipo de membro desconhecido: {tipo!r}")
