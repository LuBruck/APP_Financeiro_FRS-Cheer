from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

StatusPagamento = Literal["pendente", "parcial", "pago", "cancelado"]


def _to_float(v: object, default: float = 0.0) -> float:
    if v is None or v == "":
        return default
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace("R$", "").replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return default


@dataclass(frozen=True, slots=True)
class Pagamento:
    id_pagamento: str
    id_membro: str
    mes_referencia: str  # 'YYYY-MM'
    data_vencimento: str  # 'YYYY-MM-DD'
    valor_original: float
    multa: float = 0.0
    valor_pago: float = 0.0
    status: StatusPagamento = "pendente"
    data_pagamento: str = ""  # vazio se pendente
    link_comprovante: str = ""
    observacoes: str = ""
    ativo: bool = True

    @property
    def valor_total(self) -> float:
        return self.valor_original + self.multa

    @property
    def saldo_devedor(self) -> float:
        return max(self.valor_total - self.valor_pago, 0.0)

    @classmethod
    def from_row(cls, row: dict[str, object]) -> "Pagamento":
        status = str(row.get("status") or "pendente").strip()
        return cls(
            id_pagamento=str(row.get("id_pagamento", "")).strip(),
            id_membro=str(row.get("id_membro", "")).strip(),
            mes_referencia=str(row.get("mes_referencia", "")).strip(),
            data_vencimento=str(row.get("data_vencimento", "")).strip(),
            valor_original=_to_float(row.get("valor_original")),
            multa=_to_float(row.get("multa")),
            valor_pago=_to_float(row.get("valor_pago")),
            status=status,  # type: ignore[arg-type]
            data_pagamento=str(row.get("data_pagamento", "")).strip(),
            link_comprovante=str(row.get("link_comprovante", "")).strip(),
            observacoes=str(row.get("observacoes", "")).strip(),
            ativo=str(row.get("ativo", "TRUE")).strip().lower()
            in {"true", "sim", "yes", "1", "t", "y"},
        )
