from __future__ import annotations

from dataclasses import dataclass


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


def _to_int(v: object, default: int = 0) -> int:
    try:
        return int(v)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True, slots=True)
class Evento:
    id_evento: str
    nome: str
    data: str  # 'YYYY-MM-DD'
    receita_bruta: float = 0.0
    publico_estimado: int = 0
    observacoes: str = ""
    ativo: bool = True

    @classmethod
    def from_row(cls, row: dict[str, object]) -> "Evento":
        return cls(
            id_evento=str(row.get("id_evento", "")).strip(),
            nome=str(row.get("nome", "")).strip(),
            data=str(row.get("data", "")).strip(),
            receita_bruta=_to_float(row.get("receita_bruta")),
            publico_estimado=_to_int(row.get("publico_estimado")),
            observacoes=str(row.get("observacoes", "")).strip(),
            ativo=str(row.get("ativo", "TRUE")).strip().lower()
            in {"true", "sim", "yes", "1", "t", "y"},
        )
