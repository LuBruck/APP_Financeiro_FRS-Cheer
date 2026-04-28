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


@dataclass(frozen=True, slots=True)
class Produto:
    id_produto: str
    nome: str
    categoria: str = ""
    custo_padrao: float = 0.0
    preco_padrao: float = 0.0
    ativo: bool = True

    @classmethod
    def from_row(cls, row: dict[str, object]) -> "Produto":
        return cls(
            id_produto=str(row.get("id_produto", "")).strip(),
            nome=str(row.get("nome", "")).strip(),
            categoria=str(row.get("categoria", "")).strip(),
            custo_padrao=_to_float(row.get("custo_padrao")),
            preco_padrao=_to_float(row.get("preco_padrao")),
            ativo=str(row.get("ativo", "TRUE")).strip().lower()
            in {"true", "sim", "yes", "1", "t", "y"},
        )
