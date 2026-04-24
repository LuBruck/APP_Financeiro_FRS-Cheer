"""Tela 7.5 — Eventos e Vendas de produtos."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from app.auth import render_sidebar_user, require_login  # noqa: E402
from app.repositories import despesas_repo, eventos_repo, vendas_repo  # noqa: E402
from app.repositories.base import clear_reads_cache  # noqa: E402
from app.services import upload_service  # noqa: E402
from app.utils.formatters import formatar_brl, formatar_data_br  # noqa: E402

st.set_page_config(page_title="Eventos e Vendas", page_icon="🎉", layout="wide")
require_login()
render_sidebar_user()

st.title("Eventos e Vendas")

aba_eventos, aba_vendas = st.tabs(["Eventos", "Vendas de produtos"])


# ─────────────────────────── ABA EVENTOS ────────────────────────────

with aba_eventos:
    st.subheader("Eventos")

    eventos = eventos_repo.listar_todos()
    todas_despesas = despesas_repo.listar_todos()

    # Monta tabela de eventos com lucro líquido calculado.
    if eventos:
        rows_ev = []
        for ev in sorted(eventos, key=lambda e: e.data, reverse=True):
            despesas_ev = [d for d in todas_despesas if d.id_evento_relacionado == ev.id_evento]
            total_desp = sum(d.valor for d in despesas_ev)
            lucro = ev.receita_bruta - total_desp
            rows_ev.append(
                {
                    "id_evento": ev.id_evento,
                    "Nome": ev.nome,
                    "Data": formatar_data_br(ev.data),
                    "Receita bruta": formatar_brl(ev.receita_bruta),
                    "Total despesas": formatar_brl(total_desp),
                    "Lucro líquido": formatar_brl(lucro),
                    "Público estimado": ev.publico_estimado or "—",
                    "Observações": ev.observacoes,
                }
            )
        df_ev = pd.DataFrame(rows_ev)
        st.dataframe(
            df_ev.drop(columns=["id_evento"]),
            use_container_width=True,
            hide_index=True,
        )

        # Detalhe de um evento.
        st.markdown("---")
        st.markdown("**Ver despesas de um evento:**")
        ev_labels = [f"{e.nome} ({e.data})" for e in eventos]
        ev_sel_label = st.selectbox("Selecione o evento", ev_labels, key="ev_detail")
        ev_sel = eventos[[f"{e.nome} ({e.data})" for e in eventos].index(ev_sel_label)]
        desp_ev = [d for d in todas_despesas if d.id_evento_relacionado == ev_sel.id_evento]
        if desp_ev:
            df_desp = pd.DataFrame(
                [
                    {
                        "Data": formatar_data_br(d.data),
                        "Categoria": d.categoria,
                        "Descrição": d.descricao,
                        "Valor": formatar_brl(d.valor),
                        "Beneficiário": d.beneficiario,
                    }
                    for d in sorted(desp_ev, key=lambda d: d.data)
                ]
            )
            st.dataframe(df_desp, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma despesa vinculada a este evento.")
    else:
        st.info("Nenhum evento cadastrado. Crie o primeiro abaixo.")

    # Formulário de novo evento.
    st.markdown("---")
    with st.expander("➕ Novo evento", expanded=not eventos):
        with st.form("form_novo_evento", clear_on_submit=True):
            nome_ev = st.text_input("Nome do evento", placeholder="Ex.: Festa Junina 2026")
            data_ev = st.date_input("Data do evento", value=date.today(), format="DD/MM/YYYY")
            receita_ev = st.number_input(
                "Receita bruta (R$)",
                min_value=0.0,
                step=10.0,
                format="%.2f",
                help="Pode preencher depois ao editar o evento.",
            )
            publico_ev = st.number_input("Público estimado", min_value=0, step=10)
            obs_ev = st.text_area("Observações")
            salvar_ev = st.form_submit_button("Salvar evento", type="primary")

        if salvar_ev:
            if not nome_ev.strip():
                st.error("Nome do evento é obrigatório.")
                st.stop()
            evento_dict = {
                "nome": nome_ev.strip(),
                "data": data_ev.isoformat(),
                "receita_bruta": round(float(receita_ev), 2),
                "publico_estimado": int(publico_ev),
                "observacoes": obs_ev.strip(),
                "ativo": True,
            }
            try:
                with st.spinner("Salvando evento..."):
                    eventos_repo.criar(evento_dict)
                    clear_reads_cache()
                st.success(f"Evento **{nome_ev.strip()}** criado com sucesso.")
                st.rerun()
            except Exception as e:
                st.error(f"Falha ao salvar: {e}")

    # Editar receita bruta de evento existente.
    if eventos:
        st.markdown("---")
        with st.expander("✏️ Atualizar receita bruta de um evento"):
            with st.form("form_editar_evento", clear_on_submit=True):
                ev_edit_label = st.selectbox(
                    "Evento", [f"{e.nome} ({e.data})" for e in eventos], key="ev_edit"
                )
                ev_edit = eventos[[f"{e.nome} ({e.data})" for e in eventos].index(ev_edit_label)]
                nova_receita = st.number_input(
                    "Nova receita bruta (R$)",
                    min_value=0.0,
                    value=float(ev_edit.receita_bruta),
                    step=10.0,
                    format="%.2f",
                )
                salvar_edit = st.form_submit_button("Atualizar", type="primary")

            if salvar_edit:
                try:
                    with st.spinner("Atualizando..."):
                        eventos_repo.atualizar(
                            ev_edit.id_evento,
                            {"receita_bruta": round(float(nova_receita), 2)},
                        )
                        clear_reads_cache()
                    st.success("Receita atualizada.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Falha: {e}")


# ─────────────────────────── ABA VENDAS ─────────────────────────────

with aba_vendas:
    st.subheader("Vendas de produtos")

    vendas = vendas_repo.listar_todos()

    # Métricas do mês corrente.
    hoje = date.today()
    mes_atual = f"{hoje.year:04d}-{hoje.month:02d}"
    vendas_mes = [v for v in vendas if v.data.startswith(mes_atual)]
    total_mes = sum(v.valor_total for v in vendas_mes)
    total_ano = sum(v.valor_total for v in vendas)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total vendido no mês", formatar_brl(total_mes))
    c2.metric("Total vendido no ano", formatar_brl(total_ano))
    c3.metric("Registros no mês", len(vendas_mes))

    if vendas:
        df_vendas = pd.DataFrame(
            [
                {
                    "Data": formatar_data_br(v.data),
                    "Produto": v.produto,
                    "Quantidade": v.quantidade,
                    "Valor unit.": formatar_brl(v.valor_unitario),
                    "Total": formatar_brl(v.valor_total),
                    "Comprador": v.comprador or "—",
                    "Observações": v.observacoes,
                }
                for v in sorted(vendas, key=lambda v: v.data, reverse=True)
            ]
        )
        st.dataframe(df_vendas, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma venda registrada ainda.")

    st.markdown("---")
    with st.expander("➕ Registrar nova venda", expanded=not vendas):
        with st.form("form_nova_venda", clear_on_submit=True):
            produto = st.text_input("Produto", placeholder="Ex.: Camiseta Furiosos")
            data_venda = st.date_input("Data da venda", value=date.today(), format="DD/MM/YYYY")
            quantidade = st.number_input("Quantidade", min_value=1, step=1, value=1)
            valor_unit = st.number_input(
                "Valor unitário (R$)", min_value=0.0, step=1.0, format="%.2f"
            )
            comprador = st.text_input("Comprador (opcional)")
            obs_venda = st.text_area("Observações")
            comprovante_venda = st.file_uploader(
                "Comprovante (PDF, PNG ou JPG) — opcional",
                type=["pdf", "png", "jpg", "jpeg"],
                accept_multiple_files=False,
                key="comp_venda",
            )
            salvar_venda = st.form_submit_button("Salvar venda", type="primary")

        if salvar_venda:
            if not produto.strip():
                st.error("Nome do produto é obrigatório.")
                st.stop()
            if valor_unit <= 0:
                st.error("Informe um valor unitário maior que zero.")
                st.stop()

            link_comp_venda = ""
            if comprovante_venda is not None:
                try:
                    with st.spinner("Enviando comprovante..."):
                        link_comp_venda = upload_service.upload_comprovante_venda(
                            produto=produto.strip(),
                            data_iso=data_venda.isoformat(),
                            nome_arquivo_origem=comprovante_venda.name,
                            conteudo=comprovante_venda.getvalue(),
                        )
                except Exception as e:
                    st.error(f"Falha no upload: {e}")
                    st.stop()

            qtd = int(quantidade)
            v_unit = round(float(valor_unit), 2)
            venda_dict = {
                "data": data_venda.isoformat(),
                "produto": produto.strip(),
                "quantidade": qtd,
                "valor_unitario": v_unit,
                "valor_total": round(qtd * v_unit, 2),
                "comprador": comprador.strip(),
                "link_comprovante": link_comp_venda,
                "observacoes": obs_venda.strip(),
                "ativo": True,
            }
            try:
                with st.spinner("Salvando venda..."):
                    vendas_repo.criar(venda_dict)
                    clear_reads_cache()
                st.success(
                    f"Venda registrada: **{produto.strip()}** × {qtd} = "
                    f"{formatar_brl(qtd * v_unit)}."
                )
                if link_comp_venda:
                    st.markdown(f"[Abrir comprovante]({link_comp_venda})")
                st.rerun()
            except Exception as e:
                st.error(f"Falha ao salvar: {e}")
