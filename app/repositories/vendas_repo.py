"""Acesso à aba `vendas_produtos`."""

from __future__ import annotations

import streamlit as st

from app.config import SHEET_VENDAS
from app.models.venda import Venda
from app.repositories.base import (
    append_row,
    preencher_auditoria_criacao,
    preencher_auditoria_atualizacao,
    read_all_records,
    update_row_by_id,
)


@st.cache_data(ttl=300, show_spinner=False)
def listar_todos() -> list[Venda]:
    rows = read_all_records(SHEET_VENDAS, only_ativo=True)
    return [Venda.from_row(r) for r in rows if r.get("id_venda")]


def get_by_id(id_venda: str) -> Venda | None:
    for v in listar_todos():
        if v.id_venda == id_venda:
            return v
    return None


def criar(venda: dict) -> None:
    row = preencher_auditoria_criacao(dict(venda))
    append_row(SHEET_VENDAS, row)


def atualizar(id_venda: str, updates: dict) -> None:
    payload = preencher_auditoria_atualizacao(dict(updates))
    update_row_by_id(SHEET_VENDAS, "id_venda", id_venda, payload)


def excluir(id_venda: str) -> None:
    atualizar(id_venda, {"ativo": False})
