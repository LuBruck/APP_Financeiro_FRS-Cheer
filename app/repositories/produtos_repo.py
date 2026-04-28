"""Acesso à aba `produtos` (catálogo de produtos para vendas)."""

from __future__ import annotations

import streamlit as st

from app.config import SHEET_PRODUTOS
from app.models.produto import Produto
from app.repositories.base import (
    append_row,
    preencher_auditoria_atualizacao,
    preencher_auditoria_criacao,
    read_all_records,
    update_row_by_id,
)
from app.utils.ids import proximo_id


@st.cache_data(ttl=300, show_spinner=False)
def listar_todos(incluir_inativos: bool = False) -> list[Produto]:
    rows = read_all_records(SHEET_PRODUTOS, only_ativo=not incluir_inativos)
    return [Produto.from_row(r) for r in rows if r.get("id_produto")]


def get_by_id(id_produto: str) -> Produto | None:
    for p in listar_todos(incluir_inativos=True):
        if p.id_produto == id_produto:
            return p
    return None


def categorias_existentes() -> list[str]:
    cats = {p.categoria for p in listar_todos(incluir_inativos=True) if p.categoria}
    return sorted(cats)


def proximo_id_produto() -> str:
    ids = [p.id_produto for p in listar_todos(incluir_inativos=True)]
    return proximo_id("P", ids, digitos=3)


def criar(produto: dict) -> str:
    novo = dict(produto)
    if not novo.get("id_produto"):
        novo["id_produto"] = proximo_id_produto()
    row = preencher_auditoria_criacao(novo)
    append_row(SHEET_PRODUTOS, row)
    return novo["id_produto"]


def atualizar(id_produto: str, updates: dict) -> None:
    payload = preencher_auditoria_atualizacao(dict(updates))
    update_row_by_id(SHEET_PRODUTOS, "id_produto", id_produto, payload)


def desativar(id_produto: str) -> None:
    atualizar(id_produto, {"ativo": False})
