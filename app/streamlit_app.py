"""Entry point do app. Tela Home + auth guard.

Rodar com:
    streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Garante que `app.xxx` seja importável quando o Streamlit roda este script.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st  # noqa: E402

from app.auth import get_role, render_sidebar_user, require_login  # noqa: E402
from app.repositories import membros_repo  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

st.set_page_config(
    page_title="Furiosos Cheer — Financeiro",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

require_login()
render_sidebar_user()

st.title("Furiosos Cheer — Financeiro")
st.caption(f"Papel do usuário logado: **{get_role()}**")

st.markdown(
    """
    Bem-vindo(a) ao painel financeiro do **Furiosos Cheer**.
    Use o menu lateral para navegar entre as telas (Dashboard, Pagamentos, Cobranças, etc).

    *Sprint 1 em andamento — telas serão liberadas conforme os próximos sprints.*
    """
)

st.subheader("Validação end-to-end — membros cadastrados")
st.caption(
    "Esta lista vem direto da aba `membros` do Google Sheets. "
    "Se aparecer, login Google + Service Account + leitura da planilha estão funcionando."
)

try:
    membros = membros_repo.listar_todos(incluir_inativos=False)
except Exception as e:  # pragma: no cover - diagnóstico em tela
    st.error(f"Falha ao ler planilha: {e}")
    st.stop()

if not membros:
    st.info("Nenhum membro ativo encontrado. Cadastre membros na aba `membros` da planilha.")
else:
    st.success(f"{len(membros)} membro(s) ativo(s) encontrado(s).")
    st.dataframe(
        [
            {
                "ID": m.id_membro,
                "Nome": m.nome,
                "Tipo": m.tipo,
                "Email": m.email,
                "Semestre de entrada": m.semestre_entrada,
            }
            for m in membros
        ],
        use_container_width=True,
        hide_index=True,
    )
