"""Acesso à aba `membros` do Google Sheets."""

from __future__ import annotations

import streamlit as st

from app.config import SHEET_MEMBROS
from app.models.membro import Membro
from app.repositories.base import (
    append_row,
    read_all_records,
    update_row_by_id,
    preencher_auditoria_criacao,
    preencher_auditoria_atualizacao,
)
from app.utils.ids import proximo_id


@st.cache_data(ttl=300, show_spinner=False)
def listar_todos(incluir_inativos: bool = False) -> list[Membro]:
    """Lista membros cadastrados.

    A aba `membros` não tem coluna `ativo` — usa `status` ('ativo' | 'inativo').
    """
    rows = read_all_records(SHEET_MEMBROS, only_ativo=False)
    membros = [Membro.from_row(r) for r in rows if r.get("id_membro")]
    if not incluir_inativos:
        membros = [m for m in membros if m.status == "ativo"]
    return membros


@st.cache_data(ttl=300, show_spinner=False)
def get_by_id(id_membro: str) -> Membro | None:
    for m in listar_todos(incluir_inativos=True):
        if m.id_membro == id_membro:
            return m
    return None


def id_existe(id_membro: str) -> bool:
    return get_by_id(id_membro) is not None


def proximo_id_membro() -> str:
    ids = [m.id_membro for m in listar_todos(incluir_inativos=True)]
    return proximo_id("M", ids, digitos=3)


def criar(membro: dict) -> None:
    novo = dict(membro)
    if not novo.get("id_membro"):
        novo["id_membro"] = proximo_id_membro()
    row = preencher_auditoria_criacao(novo)
    append_row(SHEET_MEMBROS, row)


def atualizar(id_membro: str, updates: dict) -> None:
    payload = preencher_auditoria_atualizacao(dict(updates))
    update_row_by_id(SHEET_MEMBROS, "id_membro", id_membro, payload)
