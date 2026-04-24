"""Tela de gerenciamento de usuários autorizados — somente admin."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st  # noqa: E402

from app.auth import get_role, render_sidebar_user, require_login  # noqa: E402
from app.repositories import usuarios_repo  # noqa: E402
from app.repositories.base import clear_reads_cache  # noqa: E402

st.set_page_config(page_title="Usuários", page_icon="🔑", layout="wide")
require_login()
render_sidebar_user()

st.title("Usuários autorizados")

if get_role() != "admin":
    st.warning("Esta tela é restrita ao diretor financeiro (admin).")
    st.stop()

email_logado = getattr(st.user, "email", "").strip().lower()

ROLES = ["admin", "assistant"]
ROLE_LABEL = {"admin": "Admin (diretor)", "assistant": "Assistente"}

# ─── Tabela de usuários ──────────────────────────────────────────────
todos = usuarios_repo.listar_todos()
ativos = [r for r in todos if str(r.get("ativo", "TRUE")).strip().lower() in {"true", "sim", "yes", "1", "t", "y"}]
inativos = [r for r in todos if r not in ativos]

col_a, col_i = st.columns(2)
col_a.metric("Usuários ativos", len(ativos))
col_i.metric("Usuários inativos", len(inativos))

filtro = st.radio("Exibir", ["Ativos", "Inativos", "Todos"], horizontal=True)
lista = ativos if filtro == "Ativos" else (inativos if filtro == "Inativos" else todos)

if lista:
    for r in sorted(lista, key=lambda x: str(x.get("email", ""))):
        email = str(r.get("email", ""))
        role = str(r.get("role", "assistant"))
        ativo = str(r.get("ativo", "TRUE")).strip().lower() in {"true", "sim", "yes", "1", "t", "y"}
        e_voce = email.strip().lower() == email_logado

        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.markdown(f"**{email}**{'  _(você)_' if e_voce else ''}")
            c2.markdown(f"`{ROLE_LABEL.get(role, role)}`")

            if ativo:
                if not e_voce:
                    if c3.button("Desativar", key=f"des_{email}", type="secondary"):
                        try:
                            with st.spinner("Desativando..."):
                                usuarios_repo.desativar(email)
                                clear_reads_cache()
                            st.success(f"{email} desativado.")
                            st.rerun()
                        except Exception as ex:
                            st.error(f"Falha: {ex}")
                else:
                    c3.caption("_(não pode desativar a si mesmo)_")
            else:
                novo_role = c3.selectbox(
                    "Role", ROLES, key=f"role_{email}",
                    format_func=lambda r: ROLE_LABEL[r], label_visibility="collapsed"
                )
                if st.button("Reativar", key=f"reat_{email}"):
                    try:
                        with st.spinner("Reativando..."):
                            usuarios_repo.reativar(email, novo_role)
                            clear_reads_cache()
                        st.success(f"{email} reativado como {novo_role}.")
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Falha: {ex}")
else:
    st.info("Nenhum usuário nesta categoria.")

st.divider()

# ─── Adicionar usuário ───────────────────────────────────────────────
with st.expander("➕ Adicionar usuário"):
    with st.form("form_novo_usuario", clear_on_submit=True):
        novo_email = st.text_input(
            "Email Google",
            placeholder="nome@gmail.com",
            help="Deve ser exatamente o email da conta Google que a pessoa usa para fazer login.",
        )
        novo_role = st.selectbox("Papel", ROLES, format_func=lambda r: ROLE_LABEL[r])
        salvar = st.form_submit_button("Adicionar", type="primary")

    if salvar:
        novo_email = novo_email.strip().lower()
        if not novo_email or "@" not in novo_email:
            st.error("Informe um email válido.")
            st.stop()
        if usuarios_repo.email_existe(novo_email):
            st.error(f"`{novo_email}` já está cadastrado. Use Reativar se estiver inativo.")
            st.stop()
        try:
            with st.spinner("Salvando..."):
                usuarios_repo.criar({
                    "email": novo_email,
                    "role": novo_role,
                    "ativo": True,
                })
                clear_reads_cache()
            st.success(f"**{novo_email}** adicionado como {ROLE_LABEL[novo_role]}.")
            st.rerun()
        except Exception as ex:
            st.error(f"Falha ao salvar: {ex}")

st.divider()
st.info(
    "**Como funciona:** o app busca usuários autorizados nesta aba do Sheets. "
    "Se a aba estiver vazia ou inacessível, o app usa os emails do `secrets.toml` como fallback. "
    "Mudanças refletem em até 1 minuto (cache de sessão)."
)
