"""Login via Google OIDC (`st.login()`) + whitelist de emails autorizados.

Fluxo:
    1. Usuário clica "Entrar com Google" → Streamlit redireciona ao Google.
    2. Google devolve o email autenticado em `st.user`.
    3. `require_login()` checa se o email está em `secrets["authorized_users"]`;
       se não, bloqueia com "acesso negado".

Chame `require_login()` no topo de toda página — sem exceção.
"""

from __future__ import annotations

import logging
from typing import Literal

import streamlit as st

logger = logging.getLogger(__name__)

Role = Literal["admin", "assistant"]


def _authorized_users() -> dict[str, str]:
    return dict(st.secrets.get("authorized_users", {}))


def _is_logged_in() -> bool:
    return bool(getattr(st.user, "is_logged_in", False))


def _current_email() -> str | None:
    if not _is_logged_in():
        return None
    return getattr(st.user, "email", None)


def get_role() -> Role | None:
    email = _current_email()
    if email is None:
        return None
    role = _authorized_users().get(email)
    return role  # type: ignore[return-value]


def require_login() -> None:
    """Auth guard. Exibe tela de login/erro e PARA a execução se não autorizado."""
    if not _is_logged_in():
        st.title("Furiosos Cheer — Financeiro")
        st.write("Acesso restrito à diretoria. Faça login com sua conta Google.")
        if st.button("Entrar com Google", type="primary"):
            st.login()
        st.stop()

    email = _current_email()
    if email not in _authorized_users():
        st.error(
            f"Acesso negado: o email `{email}` não está autorizado. "
            "Peça ao diretor financeiro para adicionar seu email à whitelist."
        )
        if st.button("Sair"):
            st.logout()
        st.stop()


def render_sidebar_user() -> None:
    """Mostra usuário logado + botão de logout na sidebar. Chamar após require_login."""
    email = _current_email()
    name = getattr(st.user, "name", None) or email
    with st.sidebar:
        st.caption(f"Logado como: **{name}**")
        st.caption(f"Papel: `{get_role()}`")
        if st.button("Sair", use_container_width=True):
            st.logout()
