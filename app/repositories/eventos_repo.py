"""Acesso à aba `eventos`."""

from __future__ import annotations

import streamlit as st

from app.config import SHEET_EVENTOS
from app.models.evento import Evento
from app.repositories.base import (
    append_row,
    preencher_auditoria_criacao,
    preencher_auditoria_atualizacao,
    read_all_records,
    update_row_by_id,
)
from app.utils.ids import proximo_id


@st.cache_data(ttl=300, show_spinner=False)
def listar_todos() -> list[Evento]:
    rows = read_all_records(SHEET_EVENTOS, only_ativo=True)
    return [Evento.from_row(r) for r in rows if r.get("id_evento")]


def get_by_id(id_evento: str) -> Evento | None:
    for e in listar_todos():
        if e.id_evento == id_evento:
            return e
    return None


def proximo_id_evento() -> str:
    ids = [e.id_evento for e in listar_todos()]
    return proximo_id("E", ids, digitos=4)


def criar(evento: dict) -> None:
    novo = dict(evento)
    novo["id_evento"] = proximo_id_evento()
    row = preencher_auditoria_criacao(novo)
    append_row(SHEET_EVENTOS, row)


def atualizar(id_evento: str, updates: dict) -> None:
    payload = preencher_auditoria_atualizacao(dict(updates))
    update_row_by_id(SHEET_EVENTOS, "id_evento", id_evento, payload)


def excluir(id_evento: str) -> None:
    atualizar(id_evento, {"ativo": False})
