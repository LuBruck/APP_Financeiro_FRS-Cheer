"""Tela de catálogo de produtos para vendas."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from app.auth import render_sidebar_user, require_login  # noqa: E402
from app.repositories import produtos_repo  # noqa: E402
from app.repositories.base import clear_reads_cache  # noqa: E402
from app.utils.formatters import formatar_brl  # noqa: E402

st.set_page_config(page_title="Produtos", page_icon="📦", layout="wide")
require_login()
render_sidebar_user()

st.title("Catálogo de produtos")
st.caption("Produtos disponíveis para registro em vendas.")

if st.session_state.pop("_produto_salvo", False):
    st.success("Produto salvo com sucesso!")
if st.session_state.pop("_produto_excluido", False):
    st.success("Produto desativado.")

# ─── Filtros ─────────────────────────────────────────────────────────
col_busca, col_status = st.columns([3, 1])
busca = col_busca.text_input("Buscar por nome ou categoria", "")
filtro_status = col_status.radio("Status", ["ativos", "inativos", "todos"], horizontal=False)

todos = produtos_repo.listar_todos(incluir_inativos=True)

if filtro_status == "ativos":
    lista = [p for p in todos if p.ativo]
elif filtro_status == "inativos":
    lista = [p for p in todos if not p.ativo]
else:
    lista = todos

if busca.strip():
    q = busca.strip().lower()
    lista = [p for p in lista if q in p.nome.lower() or q in p.categoria.lower()]

# ─── Modal de edição ─────────────────────────────────────────────────
@st.dialog("Editar produto", width="large")
def _modal_editar(id_produto: str) -> None:
    p = produtos_repo.get_by_id(id_produto)
    if p is None:
        st.error("Produto não encontrado.")
        return

    st.caption(f"ID: {p.id_produto}")

    nome = st.text_input("Nome", value=p.nome)
    categorias = produtos_repo.categorias_existentes()
    _NOVA = "+ Nova categoria..."
    opcoes_cat = ([""] + categorias + [_NOVA]) if categorias else ["", _NOVA]
    cat_idx = opcoes_cat.index(p.categoria) if p.categoria in opcoes_cat else opcoes_cat.index(_NOVA)
    cat_sel = st.selectbox("Categoria", opcoes_cat, index=cat_idx, key=f"cat_edit_{p.id_produto}")
    if cat_sel == _NOVA:
        categoria = st.text_input(
            "Nova categoria",
            value="" if p.categoria in categorias else p.categoria,
            key=f"cat_edit_nova_{p.id_produto}",
        )
    else:
        categoria = cat_sel

    col_c, col_p = st.columns(2)
    custo = col_c.number_input(
        "Custo padrão (R$)", min_value=0.0, value=float(p.custo_padrao), step=1.0, format="%.2f"
    )
    preco = col_p.number_input(
        "Preço padrão (R$)", min_value=0.0, value=float(p.preco_padrao), step=1.0, format="%.2f"
    )

    ativo = st.checkbox("Ativo (aparece nas vendas)", value=p.ativo)

    st.divider()
    col_salvar, col_excluir = st.columns([3, 1])
    with col_salvar:
        if st.button("💾 Salvar", type="primary", use_container_width=True):
            if not nome.strip():
                st.error("Nome é obrigatório.")
                return
            try:
                produtos_repo.atualizar(
                    p.id_produto,
                    {
                        "nome": nome.strip(),
                        "categoria": categoria.strip(),
                        "custo_padrao": round(float(custo), 2),
                        "preco_padrao": round(float(preco), 2),
                        "ativo": ativo,
                    },
                )
                clear_reads_cache()
                st.session_state["_produto_salvo"] = True
                st.rerun()
            except Exception as e:
                st.error(f"Falha ao salvar: {e}")

    with col_excluir:
        confirmar = st.checkbox("Confirmar")
        if st.button(
            "🗑️ Desativar",
            disabled=not confirmar,
            use_container_width=True,
            type="primary" if confirmar else "secondary",
        ):
            try:
                produtos_repo.desativar(p.id_produto)
                clear_reads_cache()
                st.session_state["_produto_excluido"] = True
                st.rerun()
            except Exception as e:
                st.error(f"Falha ao desativar: {e}")


# ─── Tabela ──────────────────────────────────────────────────────────
st.subheader(f"Produtos ({len(lista)})")

if lista:
    rows = []
    for p in sorted(lista, key=lambda x: x.nome):
        margem = p.preco_padrao - p.custo_padrao
        rows.append(
            {
                "ID": p.id_produto,
                "Nome": p.nome,
                "Categoria": p.categoria or "—",
                "Custo": formatar_brl(p.custo_padrao),
                "Preço": formatar_brl(p.preco_padrao),
                "Margem": formatar_brl(margem),
                "Status": "ativo" if p.ativo else "inativo",
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("**Editar produto:**")
    labels_edit = [f"{p.nome} ({p.id_produto})" for p in sorted(lista, key=lambda x: x.nome)]
    ids_edit = [p.id_produto for p in sorted(lista, key=lambda x: x.nome)]
    col_sel, col_btn = st.columns([4, 1])
    sel_label = col_sel.selectbox("Produto", labels_edit, key="prod_edit_sel", label_visibility="collapsed")
    if col_btn.button("✏️ Editar", use_container_width=True):
        _modal_editar(ids_edit[labels_edit.index(sel_label)])
else:
    st.info("Nenhum produto encontrado com os filtros atuais.")

# ─── Cadastro ────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("➕ Novo produto", expanded=not todos):
    categorias_exist = produtos_repo.categorias_existentes()
    _NOVA_NOVO = "+ Nova categoria..."
    opcoes_cat_novo = ([""] + categorias_exist + [_NOVA_NOVO]) if categorias_exist else ["", _NOVA_NOVO]
    cat_sel_novo = st.selectbox(
        "Categoria", opcoes_cat_novo, index=0, key="cat_novo_sel"
    )
    with st.form("form_novo_produto", clear_on_submit=True):
        nome_novo = st.text_input("Nome *", placeholder="Ex.: Camiseta Furiosos")
        if cat_sel_novo == _NOVA_NOVO:
            categoria_nova = st.text_input("Nova categoria", key="cat_novo_input")
        else:
            categoria_nova = cat_sel_novo
            if cat_sel_novo:
                st.caption(f"Categoria selecionada: **{cat_sel_novo}**")
        col_c, col_p = st.columns(2)
        custo_novo = col_c.number_input(
            "Custo padrão (R$)", min_value=0.0, step=1.0, format="%.2f"
        )
        preco_novo = col_p.number_input(
            "Preço padrão (R$)", min_value=0.0, step=1.0, format="%.2f"
        )
        salvar = st.form_submit_button("Salvar produto", type="primary")

    if salvar:
        if not nome_novo.strip():
            st.error("Nome é obrigatório.")
            st.stop()
        try:
            with st.spinner("Salvando..."):
                novo_id = produtos_repo.criar(
                    {
                        "nome": nome_novo.strip(),
                        "categoria": categoria_nova.strip(),
                        "custo_padrao": round(float(custo_novo), 2),
                        "preco_padrao": round(float(preco_novo), 2),
                        "ativo": True,
                    }
                )
                clear_reads_cache()
            st.success(f"Produto **{nome_novo.strip()}** cadastrado (ID: {novo_id}).")
            st.rerun()
        except Exception as e:
            st.error(f"Falha ao salvar: {e}")
