"""Helpers de formatação pt-BR (UI) <-> ISO/número (armazenamento).

Regra: **sempre** usar estas funções na UI — nunca formatar inline.
"""

from __future__ import annotations

from datetime import date, datetime


def formatar_brl(valor: float | int | str | None) -> str:
    """1234.56 -> 'R$ 1.234,56'. None/vazio -> 'R$ 0,00'."""
    if valor is None or valor == "":
        valor = 0
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return "R$ 0,00"
    # Usa formatação americana e troca separadores (evita dependência de locale).
    s = f"{v:,.2f}"
    s = s.replace(",", "_").replace(".", ",").replace("_", ".")
    return f"R$ {s}"


def parse_brl(texto: str) -> float:
    """'R$ 1.234,56' -> 1234.56. Aceita vários formatos com ou sem 'R$'."""
    t = texto.strip().replace("R$", "").strip()
    t = t.replace(".", "").replace(",", ".")
    return float(t)


def formatar_data_br(d: date | datetime | str | None) -> str:
    """Date/ISO -> 'DD/MM/YYYY'. Vazio -> ''."""
    if not d:
        return ""
    if isinstance(d, str):
        d = datetime.fromisoformat(d).date()
    elif isinstance(d, datetime):
        d = d.date()
    return d.strftime("%d/%m/%Y")


def data_iso(d: date | datetime | str) -> str:
    """Converte para string ISO 'YYYY-MM-DD' para armazenamento."""
    if isinstance(d, str):
        return datetime.fromisoformat(d).date().isoformat()
    if isinstance(d, datetime):
        return d.date().isoformat()
    return d.isoformat()


def mes_referencia(d: date | datetime | None = None) -> str:
    """Retorna 'YYYY-MM' da data (default: hoje)."""
    if d is None:
        d = date.today()
    if isinstance(d, datetime):
        d = d.date()
    return d.strftime("%Y-%m")
