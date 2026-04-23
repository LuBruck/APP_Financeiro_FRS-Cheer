"""Acesso à aba `membros` do Google Sheets."""

from __future__ import annotations

import streamlit as st

from app.config import SHEET_MEMBROS
from app.models.membro import Membro
from app.repositories.base import read_all_records


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
