from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

TipoComprador = Literal["atleta", "associado", "externo"]


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
    valor_pago: float = 0.0
    custo_unitario: float = 0.0
    id_produto: str = ""
    categoria: str = ""
    tipo_comprador: TipoComprador = "externo"
    id_membro: str = ""
    comprador: str = ""
    contato_comprador: str = ""
    link_comprovante: str = ""
    observacoes: str = ""
    ativo: bool = True

    @property
    def lucro_total(self) -> float:
        return round((self.valor_unitario - self.custo_unitario) * self.quantidade, 2)

    @property
    def saldo(self) -> float:
        return round(max(self.valor_total - self.valor_pago, 0.0), 2)

    @property
    def status_pagamento(self) -> str:
        if self.valor_pago >= self.valor_total and self.valor_total > 0:
            return "pago"
        if self.valor_pago > 0:
            return "parcial"
        return "pendente"

    @property
    def links_comprovantes(self) -> list[str]:
        """Múltiplos comprovantes (parcelas) ficam separados por ' | ' no campo."""
        if not self.link_comprovante:
            return []
        return [s.strip() for s in self.link_comprovante.split("|") if s.strip()]

    @classmethod
    def from_row(cls, row: dict[str, object]) -> "Venda":
        qtd = _to_int(row.get("quantidade"), 1)
        v_unit = _to_float(row.get("valor_unitario"))
        v_total = _to_float(row.get("valor_total"), qtd * v_unit)
        tipo = str(row.get("tipo_comprador", "")).strip().lower() or "externo"
        if tipo not in {"atleta", "associado", "externo"}:
            tipo = "externo"
        return cls(
            id_venda=str(row.get("id_venda", "")).strip(),
            data=str(row.get("data", "")).strip(),
            produto=str(row.get("produto", "")).strip(),
            quantidade=qtd,
            valor_unitario=v_unit,
            valor_total=v_total,
            valor_pago=_to_float(row.get("valor_pago")),
            custo_unitario=_to_float(row.get("custo_unitario")),
            id_produto=str(row.get("id_produto", "")).strip(),
            categoria=str(row.get("categoria", "")).strip(),
            tipo_comprador=tipo,  # type: ignore[arg-type]
            id_membro=str(row.get("id_membro", "")).strip(),
            comprador=str(row.get("comprador", "")).strip(),
            contato_comprador=str(row.get("contato_comprador", "")).strip(),
            link_comprovante=str(row.get("link_comprovante", "")).strip(),
            observacoes=str(row.get("observacoes", "")).strip(),
            ativo=str(row.get("ativo", "TRUE")).strip().lower()
            in {"true", "sim", "yes", "1", "t", "y"},
        )
