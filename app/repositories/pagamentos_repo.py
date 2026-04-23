"""Acesso à aba `pagamentos`."""

from __future__ import annotations

import streamlit as st

from app.config import SHEET_PAGAMENTOS
from app.models.pagamento import Pagamento
from app.repositories.base import (
    append_row,
    append_rows,
    preencher_auditoria_atualizacao,
    preencher_auditoria_criacao,
    read_all_records,
    update_row_by_id,
)


@st.cache_data(ttl=300, show_spinner=False)
def listar_todos() -> list[Pagamento]:
    rows = read_all_records(SHEET_PAGAMENTOS, only_ativo=True)
    return [Pagamento.from_row(r) for r in rows if r.get("id_pagamento")]


def listar_por_membro(id_membro: str) -> list[Pagamento]:
    return [p for p in listar_todos() if p.id_membro == id_membro]


def listar_por_mes(mes_referencia: str) -> list[Pagamento]:
    return [p for p in listar_todos() if p.mes_referencia == mes_referencia]


def get_por_membro_e_mes(id_membro: str, mes_referencia: str) -> Pagamento | None:
    for p in listar_todos():
        if p.id_membro == id_membro and p.mes_referencia == mes_referencia:
            return p
    return None


def get_by_id(id_pagamento: str) -> Pagamento | None:
    for p in listar_todos():
        if p.id_pagamento == id_pagamento:
            return p
    return None


def criar(pagamento: dict) -> None:
    """Insere uma nova linha de pagamento (já com campos de auditoria)."""
    row = preencher_auditoria_criacao(dict(pagamento))
    append_row(SHEET_PAGAMENTOS, row)


def criar_varios(pagamentos: list[dict]) -> None:
    """Insere várias linhas em 1 request (usado pela geração lazy)."""
    if not pagamentos:
        return
    rows = [preencher_auditoria_criacao(dict(p)) for p in pagamentos]
    append_rows(SHEET_PAGAMENTOS, rows)


def atualizar(id_pagamento: str, updates: dict) -> None:
    """Atualiza colunas de uma linha existente."""
    payload = preencher_auditoria_atualizacao(dict(updates))
    update_row_by_id(SHEET_PAGAMENTOS, "id_pagamento", id_pagamento, payload)
