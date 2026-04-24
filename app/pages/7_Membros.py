"""Tela de gerenciamento de membros — somente admin."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from app.auth import get_role, render_sidebar_user, require_login  # noqa: E402
from app.repositories import membros_repo  # noqa: E402
from app.repositories.base import clear_reads_cache  # noqa: E402

st.set_page_config(page_title="Membros", page_icon="👥", layout="wide")
require_login()
render_sidebar_user()

st.title("Membros")

# ─── Restrição de role ───────────────────────────────────────────────
role = get_role()
is_admin = role == "admin"

if not is_admin:
    st.warning("Esta tela é restrita ao diretor financeiro (admin).")
    st.stop()

TIPOS = ["atleta", "associado"]
SEMESTRES = [f"{ano}-{s}" for ano in range(2020, 2030) for s in (1, 2)]

# ─── Filtros e tabela ────────────────────────────────────────────────
st.subheader("Membros cadastrados")

col_busca, col_status, col_tipo = st.columns([2, 1, 1])
busca = col_busca.text_input("Buscar por nome ou ID", "")
filtro_status = col_status.radio("Status", ["ativos", "inativos", "todos"], horizontal=False)
filtro_tipo = col_tipo.radio("Tipo", ["todos", "atleta", "associado"], horizontal=False)

todos = membros_repo.listar_todos(incluir_inativos=True)

if filtro_status == "ativos":
    lista = [m for m in todos if m.status == "ativo"]
elif filtro_status == "inativos":
    lista = [m for m in todos if m.status == "inativo"]
else:
    lista = todos

if filtro_tipo != "todos":
    lista = [m for m in lista if m.tipo == filtro_tipo]

if busca.strip():
    q = busca.strip().lower()
    lista = [m for m in lista if q in m.nome.lower() or q in m.id_membro.lower()]

m_ativos = sum(1 for m in todos if m.status == "ativo")
m_inativos = sum(1 for m in todos if m.status == "inativo")
c1, c2, c3 = st.columns(3)
c1.metric("Membros ativos", m_ativos)
c2.metric("Membros inativos", m_inativos)
c3.metric("Exibindo agora", len(lista))

if lista:
    df = pd.DataFrame(
        [
            {
                "ID": m.id_membro,
                "Nome": m.nome,
                "Tipo": m.tipo,
                "Status": m.status,
                "Email": m.email or "—",
                "Telefone": m.telefone or "—",
                "Semestre entrada": m.semestre_entrada or "—",
                "Observações": m.observacoes or "—",
            }
            for m in sorted(lista, key=lambda m: m.nome)
        ]
    )

    def _cor_status(row: pd.Series) -> list[str]:
        bg = "#e6f4ea" if row["Status"] == "ativo" else "#fdecea"
        return [f"background-color: {bg}; color: #1a1a1a"] * len(row)

    st.dataframe(
        df.style.apply(_cor_status, axis=1),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("Nenhum membro encontrado com os filtros selecionados.")

st.divider()

# ─── Adicionar novo membro ───────────────────────────────────────────
with st.expander("➕ Adicionar novo membro"):
    proximo = membros_repo.proximo_id_membro()
    st.caption(f"ID gerado automaticamente para o próximo membro: **`{proximo}`**")
    with st.form("form_novo_membro", clear_on_submit=True):
        st.markdown("**Dados do novo membro**")
        novo_nome = st.text_input("Nome completo", placeholder="Ex.: João da Silva")

        nc3, nc4 = st.columns(2)
        novo_tipo = nc3.selectbox("Tipo", TIPOS)
        novo_semestre = nc4.selectbox(
            "Semestre de entrada",
            SEMESTRES,
            index=SEMESTRES.index("2026-1") if "2026-1" in SEMESTRES else 0,
        )

        nc5, nc6 = st.columns(2)
        novo_email = nc5.text_input("Email", placeholder="joao@email.com (opcional)")
        novo_telefone = nc6.text_input("Telefone", placeholder="(11) 99999-9999 (opcional)")

        novo_obs = st.text_area("Observações", placeholder="Texto livre (opcional).")

        salvar_novo = st.form_submit_button("Salvar membro", type="primary")

    if salvar_novo:
        novo_nome = novo_nome.strip()

        if not novo_nome:
            st.error("Nome é obrigatório.")
            st.stop()

        membro_dict = {
            "nome": novo_nome,
            "tipo": novo_tipo,
            "email": novo_email.strip(),
            "telefone": novo_telefone.strip(),
            "semestre_entrada": novo_semestre,
            "status": "ativo",
            "observacoes": novo_obs.strip(),
        }
        try:
            with st.spinner("Salvando..."):
                membros_repo.criar(membro_dict)
                clear_reads_cache()
            id_gerado = membros_repo.proximo_id_membro()  # próximo após salvar
            st.success(f"Membro **{novo_nome}** adicionado com sucesso.")
            st.rerun()
        except Exception as e:
            st.error(f"Falha ao salvar: {e}")

st.divider()

# ─── Editar membro existente ─────────────────────────────────────────
with st.expander("✏️ Editar membro existente"):
    todos_ord = sorted(todos, key=lambda m: m.nome)
    if not todos_ord:
        st.info("Nenhum membro cadastrado.")
    else:
        membro_labels = [f"{m.nome} ({m.id_membro}) {'[inativo]' if m.status == 'inativo' else ''}" for m in todos_ord]
        sel_idx = st.selectbox("Selecione o membro", range(len(membro_labels)),
                               format_func=lambda i: membro_labels[i], key="sel_editar")
        m_sel = todos_ord[sel_idx]

        with st.form("form_editar_membro", clear_on_submit=False):
            st.markdown(f"**Editando:** {m_sel.nome} (`{m_sel.id_membro}`)")
            ec1, ec2 = st.columns(2)
            edit_nome = ec1.text_input("Nome completo", value=m_sel.nome)
            edit_tipo = ec2.selectbox(
                "Tipo", TIPOS, index=TIPOS.index(m_sel.tipo) if m_sel.tipo in TIPOS else 0
            )

            ec3, ec4 = st.columns(2)
            edit_email = ec3.text_input("Email", value=m_sel.email)
            edit_telefone = ec4.text_input("Telefone", value=m_sel.telefone)

            ec5, ec6 = st.columns(2)
            edit_semestre = ec5.selectbox(
                "Semestre de entrada",
                SEMESTRES,
                index=SEMESTRES.index(m_sel.semestre_entrada)
                if m_sel.semestre_entrada in SEMESTRES else 0,
            )
            edit_status = ec6.selectbox(
                "Status",
                ["ativo", "inativo"],
                index=0 if m_sel.status == "ativo" else 1,
                help="Marcar como inativo impede geração de novas cobranças para este membro.",
            )
            edit_obs = st.text_area("Observações", value=m_sel.observacoes)

            salvar_edit = st.form_submit_button("Salvar alterações", type="primary")

        if salvar_edit:
            edit_nome = edit_nome.strip()
            if not edit_nome:
                st.error("Nome é obrigatório.")
                st.stop()
            updates = {
                "nome": edit_nome,
                "tipo": edit_tipo,
                "email": edit_email.strip(),
                "telefone": edit_telefone.strip(),
                "semestre_entrada": edit_semestre,
                "status": edit_status,
                "observacoes": edit_obs.strip(),
            }
            try:
                with st.spinner("Salvando..."):
                    membros_repo.atualizar(m_sel.id_membro, updates)
                    clear_reads_cache()
                st.success(f"Membro **{edit_nome}** atualizado.")
                st.rerun()
            except Exception as e:
                st.error(f"Falha ao salvar: {e}")
