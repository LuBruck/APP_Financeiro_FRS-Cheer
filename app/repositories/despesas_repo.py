"""Acesso à aba `despesas`."""

from __future__ import annotations

import streamlit as st

from app.config import SHEET_DESPESAS
from app.models.despesa import Despesa
from app.repositories.base import (
    append_row,
    preencher_auditoria_criacao,
    preencher_auditoria_atualizacao,
    read_all_records,
    update_row_by_id,
)
from app.utils.ids import proximo_id


@st.cache_data(ttl=300, show_spinner=False)
def listar_todos() -> list[Despesa]:
    rows = read_all_records(SHEET_DESPESAS, only_ativo=True)
    return [Despesa.from_row(r) for r in rows if r.get("id_despesa")]


def listar_por_evento(id_evento: str) -> list[Despesa]:
    return [d for d in listar_todos() if d.id_evento_relacionado == id_evento]


def get_by_id(id_despesa: str) -> Despesa | None:
    for d in listar_todos():
        if d.id_despesa == id_despesa:
            return d
    return None


def proximo_id_despesa() -> str:
    ids = [d.id_despesa for d in listar_todos()]
    return proximo_id("D", ids, digitos=4)


def criar(despesa: dict) -> None:
    novo = dict(despesa)
    novo["id_despesa"] = proximo_id_despesa()
    row = preencher_auditoria_criacao(novo)
    append_row(SHEET_DESPESAS, row)


def atualizar(id_despesa: str, updates: dict) -> None:
    payload = preencher_auditoria_atualizacao(dict(updates))
    update_row_by_id(SHEET_DESPESAS, "id_despesa", id_despesa, payload)


def excluir(id_despesa: str) -> None:
    atualizar(id_despesa, {"ativo": False})
