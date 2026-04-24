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
class Venda:
    id_venda: str
    data: str  # 'YYYY-MM-DD'
    produto: str
    quantidade: int
    valor_unitario: float
    valor_total: float
    comprador: str = ""
    link_comprovante: str = ""
    observacoes: str = ""
    ativo: bool = True

    @classmethod
    def from_row(cls, row: dict[str, object]) -> "Venda":
        qtd = _to_int(row.get("quantidade"), 1)
        v_unit = _to_float(row.get("valor_unitario"))
        v_total = _to_float(row.get("valor_total"), qtd * v_unit)
        return cls(
            id_venda=str(row.get("id_venda", "")).strip(),
            data=str(row.get("data", "")).strip(),
            produto=str(row.get("produto", "")).strip(),
            quantidade=qtd,
            valor_unitario=v_unit,
            valor_total=v_total,
            comprador=str(row.get("comprador", "")).strip(),
            link_comprovante=str(row.get("link_comprovante", "")).strip(),
            observacoes=str(row.get("observacoes", "")).strip(),
            ativo=str(row.get("ativo", "TRUE")).strip().lower()
            in {"true", "sim", "yes", "1", "t", "y"},
        )
