"""Tela 7.4 — Registrar despesa."""

from __future__ import annotations

import sys
import uuid
from datetime import date
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st  # noqa: E402

from app.auth import render_sidebar_user, require_login  # noqa: E402
from app.repositories import despesas_repo, eventos_repo  # noqa: E402
from app.repositories.base import clear_reads_cache  # noqa: E402
from app.services import upload_service  # noqa: E402
from app.utils.formatters import formatar_brl  # noqa: E402

st.set_page_config(page_title="Registrar despesa", page_icon="💸", layout="wide")
require_login()
render_sidebar_user()

st.title("Registrar despesa")
st.caption("Coach, viagens, uniformes, inscrições e outras saídas de caixa.")

CATEGORIAS = [
    "coach",
    "viagem_campeonato",
    "uniforme",
    "inscricao_campeonato",
    "evento",
    "outros",
]

CATEGORIAS_LABEL = {
    "coach": "Coach",
    "viagem_campeonato": "Viagem / Campeonato",
    "uniforme": "Uniforme",
    "inscricao_campeonato": "Inscrição em campeonato",
    "evento": "Evento",
    "outros": "Outros",
}

eventos = eventos_repo.listar_todos()
eventos_map = {f"{e.nome} ({e.data})": e for e in eventos}

with st.form("form_despesa", clear_on_submit=True):
    st.subheader("Dados da despesa")

    cat_label = st.selectbox(
        "Categoria",
        options=[CATEGORIAS_LABEL[c] for c in CATEGORIAS],
    )
    categoria = CATEGORIAS[[CATEGORIAS_LABEL[c] for c in CATEGORIAS].index(cat_label)]

    descricao = st.text_input(
        "Descrição",
        placeholder="Ex.: Passagem João SP-BH",
        max_chars=200,
    )
    valor = st.number_input("Valor (R$)", min_value=0.0, step=5.0, format="%.2f")
    beneficiario = st.text_input(
        "Beneficiário",
        placeholder="Nome do coach, empresa, etc. (opcional)",
        max_chars=200,
    )
    data_despesa = st.date_input("Data da despesa", value=date.today(), format="DD/MM/YYYY")

    evento_vinculado_label: str | None = None
    if categoria == "evento":
        if eventos_map:
            evento_vinculado_label = st.selectbox(
                "Vincular a evento (opcional)",
                options=["— nenhum —"] + list(eventos_map.keys()),
            )
        else:
            st.info("Nenhum evento cadastrado. Crie um na aba Eventos e Vendas.")

    observacoes = st.text_area("Observações", placeholder="Texto livre (opcional).")

    comprovante = st.file_uploader(
        "Comprovante (PDF, PNG ou JPG) — opcional",
        type=["pdf", "png", "jpg", "jpeg"],
        accept_multiple_files=False,
    )

    submitted = st.form_submit_button("Salvar despesa", type="primary")

if submitted:
    if not descricao.strip():
        st.error("Descrição é obrigatória.")
        st.stop()
    if valor <= 0:
        st.error("Informe um valor maior que zero.")
        st.stop()

    id_evento_rel = ""
    if categoria == "evento" and evento_vinculado_label and evento_vinculado_label != "— nenhum —":
        id_evento_rel = eventos_map[evento_vinculado_label].id_evento

    link_comp = ""
    if comprovante is not None:
        try:
            with st.spinner("Enviando comprovante..."):
                link_comp = upload_service.upload_comprovante_despesa(
                    categoria=categoria,
                    data_iso=data_despesa.isoformat(),
                    descricao=descricao.strip(),
                    nome_arquivo_origem=comprovante.name,
                    conteudo=comprovante.getvalue(),
                )
        except Exception as e:
            st.error(f"Falha no upload do comprovante: {e}")
            st.stop()

    despesa = {
        "id_despesa": str(uuid.uuid4()),
        "data": data_despesa.isoformat(),
        "categoria": categoria,
        "descricao": descricao.strip(),
        "valor": round(float(valor), 2),
        "beneficiario": beneficiario.strip(),
        "link_comprovante": link_comp,
        "id_evento_relacionado": id_evento_rel,
        "observacoes": observacoes.strip(),
        "ativo": True,
    }

    try:
        with st.spinner("Salvando despesa..."):
            despesas_repo.criar(despesa)
            clear_reads_cache()
    except Exception as e:
        st.error(f"Falha ao salvar: {e}")
        st.stop()

    st.success(
        f"Despesa registrada: **{descricao.strip()}** — {formatar_brl(float(valor))}."
    )
    if link_comp:
        st.markdown(f"[Abrir comprovante no Drive]({link_comp})")
