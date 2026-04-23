"""Base do Repository Pattern.

Responsabilidades desta camada:
    - Ler/escrever em abas do Google Sheets via `gspread`.
    - Preencher campos de auditoria (`criado_em`, `criado_por`, ...) e `ativo`.
    - Aplicar filtro de soft delete (`ativo = True`) nas leituras.

Nunca importar `streamlit` aqui exceto para `st.cache_data` e `st.user`.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import gspread
import streamlit as st

from app.config import get_worksheet


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def current_user_email() -> str:
    """Email do usuário logado (para campos de auditoria)."""
    email = getattr(st.user, "email", None)
    if not email:
        # Em testes ou quando sem login (não deveria acontecer por causa do auth guard).
        return "system"
    return email


def preencher_auditoria_criacao(row: dict[str, Any]) -> dict[str, Any]:
    agora = now_iso()
    email = current_user_email()
    row.setdefault("criado_em", agora)
    row.setdefault("criado_por", email)
    row["atualizado_em"] = agora
    row["atualizado_por"] = email
    row.setdefault("ativo", True)
    return row


def preencher_auditoria_atualizacao(row: dict[str, Any]) -> dict[str, Any]:
    row["atualizado_em"] = now_iso()
    row["atualizado_por"] = current_user_email()
    return row


def _coerce_ativo(v: Any) -> bool:
    """Sheets retorna booleano como string 'TRUE'/'FALSE' ou 'SIM'/'NÃO'. Normaliza."""
    if isinstance(v, bool):
        return v
    if v is None:
        return True  # default: ativo, para linhas legadas sem a coluna preenchida
    s = str(v).strip().lower()
    return s in {"true", "sim", "yes", "1", "t", "y"}


def read_all_records(sheet_name: str, *, only_ativo: bool = True) -> list[dict[str, Any]]:
    """Lê a aba inteira (1 request). Filtra ativo=True por default.

    A coluna `ativo` é OBRIGATÓRIA em todas as abas transacionais.
    Para a aba `membros` (sem coluna `ativo`, usa `status`), passe only_ativo=False.
    """
    ws = get_worksheet(sheet_name)
    records = ws.get_all_records()
    if only_ativo:
        records = [r for r in records if _coerce_ativo(r.get("ativo"))]
    return records


def append_row(sheet_name: str, row: dict[str, Any]) -> None:
    """Acrescenta uma linha respeitando a ordem dos cabeçalhos da planilha."""
    ws = get_worksheet(sheet_name)
    headers = ws.row_values(1)
    values = [_to_sheet_value(row.get(h, "")) for h in headers]
    ws.append_row(values, value_input_option="USER_ENTERED")


def update_row_by_id(
    sheet_name: str,
    id_column: str,
    id_value: str,
    updates: dict[str, Any],
) -> None:
    """Atualiza uma única linha identificada por `id_column = id_value`.

    Faz 2 requests: 1 leitura (all_values) + 1 batch_update. Ajusta apenas
    as colunas em `updates`, preservando as demais.
    """
    ws = get_worksheet(sheet_name)
    all_values = ws.get_all_values()
    if not all_values:
        raise ValueError(f"Aba '{sheet_name}' vazia.")
    headers = all_values[0]
    try:
        id_col_idx = headers.index(id_column)
    except ValueError as e:
        raise ValueError(f"Coluna '{id_column}' não existe em '{sheet_name}'.") from e

    row_number = None
    for i, row in enumerate(all_values[1:], start=2):
        if len(row) > id_col_idx and row[id_col_idx] == id_value:
            row_number = i
            break
    if row_number is None:
        raise LookupError(f"{id_column}={id_value} não encontrado em '{sheet_name}'.")

    data = []
    for col, val in updates.items():
        if col not in headers:
            raise ValueError(f"Coluna '{col}' não existe em '{sheet_name}'.")
        col_idx = headers.index(col)
        a1 = gspread.utils.rowcol_to_a1(row_number, col_idx + 1)
        data.append({"range": a1, "values": [[_to_sheet_value(val)]]})

    if data:
        ws.batch_update(data, value_input_option="USER_ENTERED")


def append_rows(sheet_name: str, rows: list[dict[str, Any]]) -> None:
    """Acrescenta várias linhas em 1 request (batch). Usado pela geração lazy."""
    if not rows:
        return
    ws = get_worksheet(sheet_name)
    headers = ws.row_values(1)
    values = [[_to_sheet_value(r.get(h, "")) for h in headers] for r in rows]
    ws.append_rows(values, value_input_option="USER_ENTERED")


def _to_sheet_value(v: Any) -> Any:
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if v is None:
        return ""
    return v


def clear_reads_cache() -> None:
    """Invalida o cache de leituras após uma escrita."""
    st.cache_data.clear()


__all__ = [
    "now_iso",
    "current_user_email",
    "preencher_auditoria_criacao",
    "preencher_auditoria_atualizacao",
    "read_all_records",
    "append_row",
    "append_rows",
    "update_row_by_id",
    "clear_reads_cache",
]
