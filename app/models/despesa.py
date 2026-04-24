from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

CategoriaDespesa = Literal[
    "coach",
    "viagem_campeonato",
    "uniforme",
    "inscricao_campeonato",
    "evento",
    "outros",
]


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
class Despesa:
    id_despesa: str
    data: str  # 'YYYY-MM-DD'
    categoria: CategoriaDespesa
    descricao: str
    valor: float
    beneficiario: str = ""
    link_comprovante: str = ""
    id_evento_relacionado: str = ""
    observacoes: str = ""
    ativo: bool = True

    @classmethod
    def from_row(cls, row: dict[str, object]) -> "Despesa":
        cat = str(row.get("categoria") or "outros").strip()
        return cls(
            id_despesa=str(row.get("id_despesa", "")).strip(),
            data=str(row.get("data", "")).strip(),
            categoria=cat,  # type: ignore[arg-type]
            descricao=str(row.get("descricao", "")).strip(),
            valor=_to_float(row.get("valor")),
            beneficiario=str(row.get("beneficiario", "")).strip(),
            link_comprovante=str(row.get("link_comprovante", "")).strip(),
            id_evento_relacionado=str(row.get("id_evento_relacionado", "")).strip(),
            observacoes=str(row.get("observacoes", "")).strip(),
            ativo=str(row.get("ativo", "TRUE")).strip().lower()
            in {"true", "sim", "yes", "1", "t", "y"},
        )
