"""Acesso à aba `usuarios` — lista de emails autorizados e seus roles."""

from __future__ import annotations

import streamlit as st

from app.config import SHEET_USUARIOS
from app.repositories.base import (
    append_row,
    preencher_auditoria_atualizacao,
    preencher_auditoria_criacao,
    read_all_records,
    update_row_by_id,
)

# TTL curto: mudanças de acesso devem refletir em até 1 minuto.
@st.cache_data(ttl=60, show_spinner=False)
def listar_todos() -> list[dict]:
    """Retorna todos os usuários (ativos e inativos)."""
    try:
        rows = read_all_records(SHEET_USUARIOS, only_ativo=False)
        return [r for r in rows if r.get("email")]
    except Exception:
        return []


def listar_ativos() -> dict[str, str]:
    """Retorna {email: role} dos usuários ativos. Usado pelo auth guard."""
    return {
        str(r["email"]).strip().lower(): str(r.get("role", "assistant")).strip()
        for r in listar_todos()
        if str(r.get("ativo", "TRUE")).strip().lower() in {"true", "sim", "yes", "1", "t", "y"}
    }


def get_by_email(email: str) -> dict | None:
    email_lower = email.strip().lower()
    for r in listar_todos():
        if str(r.get("email", "")).strip().lower() == email_lower:
            return r
    return None


def email_existe(email: str) -> bool:
    return get_by_email(email) is not None


def criar(usuario: dict) -> None:
    row = preencher_auditoria_criacao(dict(usuario))
    append_row(SHEET_USUARIOS, row)


def atualizar(email: str, updates: dict) -> None:
    payload = preencher_auditoria_atualizacao(dict(updates))
    update_row_by_id(SHEET_USUARIOS, "email", email, payload)


def desativar(email: str) -> None:
    atualizar(email, {"ativo": False})


def reativar(email: str, role: str) -> None:
    atualizar(email, {"ativo": True, "role": role})
