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
from app.repositories import (  # noqa: E402
    despesas_repo,
    eventos_repo,
    membros_repo,
    produtos_repo,
    vendas_repo,
)
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

    if st.session_state.pop("_venda_salva", False):
        st.success("Venda atualizada.")
    if st.session_state.pop("_venda_excluida", False):
        st.success("Venda excluída.")

    vendas = vendas_repo.listar_todos()
    produtos_catalogo = produtos_repo.listar_todos(incluir_inativos=False)
    membros_todos = membros_repo.listar_todos(incluir_inativos=True)
    membros_para_compra = [m for m in membros_todos if m.tipo in {"atleta", "associado"}]
    membros_por_id = {m.id_membro: m for m in membros_todos}

    _TIPO_LABELS = {"atleta": "Atleta", "associado": "Associado", "externo": "Externo"}

    @st.dialog("Editar venda", width="large")
    def _modal_editar_venda(id_venda: str) -> None:
        v = vendas_repo.get_by_id(id_venda)
        if v is None:
            st.error("Venda não encontrada.")
            return

        st.caption(
            f"ID: {v.id_venda} · Produto original: **{v.produto}** "
            f"({v.id_produto or '—'})"
        )

        try:
            data_default = date.fromisoformat(v.data) if v.data else date.today()
        except ValueError:
            data_default = date.today()
        nova_data = st.date_input("Data", value=data_default, format="DD/MM/YYYY")

        col_q, col_vu, col_cu = st.columns(3)
        nova_qtd = col_q.number_input("Quantidade", min_value=1, value=int(v.quantidade), step=1)
        novo_vu = col_vu.number_input(
            "Preço unitário (R$)", min_value=0.0, value=float(v.valor_unitario), step=1.0, format="%.2f"
        )
        novo_cu = col_cu.number_input(
            "Custo unitário (R$)", min_value=0.0, value=float(v.custo_unitario), step=1.0, format="%.2f"
        )

        novo_total = round(int(nova_qtd) * float(novo_vu), 2)

        novo_pago = st.number_input(
            "Valor pago (R$)",
            min_value=0.0,
            value=float(v.valor_pago),
            step=5.0,
            format="%.2f",
            help=f"Total da venda: {formatar_brl(novo_total)}",
        )
        novo_pago = min(round(float(novo_pago), 2), novo_total)
        if novo_pago >= novo_total and novo_total > 0:
            status_prev = "pago"
        elif novo_pago > 0:
            status_prev = "parcial"
        else:
            status_prev = "pendente"
        st.caption(
            f"Total: {formatar_brl(novo_total)} · "
            f"Saldo: {formatar_brl(max(novo_total - novo_pago, 0.0))} · "
            f"Status: **{status_prev}**"
        )

        nova_categoria = st.text_input("Categoria", value=v.categoria)

        novo_tipo = st.radio(
            "Tipo do comprador",
            options=["atleta", "associado", "externo"],
            index=["atleta", "associado", "externo"].index(v.tipo_comprador),
            format_func=lambda t: _TIPO_LABELS[t],
            horizontal=True,
            key=f"edit_tipo_{v.id_venda}",
        )

        novo_id_membro = ""
        novo_comprador = v.comprador
        if novo_tipo in {"atleta", "associado"}:
            membros_filt = [m for m in membros_para_compra if m.tipo == novo_tipo]
            if membros_filt:
                labels = [
                    f"{m.nome} ({m.id_membro})"
                    + (" — inativo" if m.status == "inativo" else "")
                    for m in membros_filt
                ]
                ids = [m.id_membro for m in membros_filt]
                idx = ids.index(v.id_membro) if v.id_membro in ids else 0
                lbl_sel = st.selectbox(
                    f"{_TIPO_LABELS[novo_tipo]}", labels, index=idx, key=f"edit_membro_{v.id_venda}"
                )
                m_sel = membros_filt[labels.index(lbl_sel)]
                novo_id_membro = m_sel.id_membro
                novo_comprador = m_sel.nome
            else:
                st.warning(f"Nenhum {novo_tipo} cadastrado.")
        else:
            novo_comprador = st.text_input("Nome do comprador", value=v.comprador)

        novo_contato = st.text_input("Contato", value=v.contato_comprador)
        novas_obs = st.text_area("Observações", value=v.observacoes, height=80)

        if v.link_comprovante:
            st.markdown(f"[Ver comprovante atual]({v.link_comprovante})")

        st.divider()
        col_salvar, col_excluir = st.columns([3, 1])

        with col_salvar:
            if st.button("💾 Salvar", type="primary", use_container_width=True):
                if novo_vu <= 0:
                    st.error("Preço unitário deve ser maior que zero.")
                    return
                if not novo_comprador.strip():
                    st.error("Nome do comprador é obrigatório.")
                    return
                updates = {
                    "data": nova_data.isoformat(),
                    "quantidade": int(nova_qtd),
                    "valor_unitario": round(float(novo_vu), 2),
                    "valor_total": novo_total,
                    "valor_pago": novo_pago,
                    "custo_unitario": round(float(novo_cu), 2),
                    "categoria": nova_categoria.strip(),
                    "tipo_comprador": novo_tipo,
                    "id_membro": novo_id_membro,
                    "comprador": novo_comprador.strip(),
                    "contato_comprador": novo_contato.strip(),
                    "observacoes": novas_obs.strip(),
                }
                try:
                    vendas_repo.atualizar(v.id_venda, updates)
                    clear_reads_cache()
                    st.session_state["_venda_salva"] = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Falha ao salvar: {e}")

        with col_excluir:
            confirmar = st.checkbox("Confirmar")
            if st.button(
                "🗑️ Excluir",
                disabled=not confirmar,
                use_container_width=True,
                type="primary" if confirmar else "secondary",
            ):
                try:
                    vendas_repo.excluir(v.id_venda)
                    clear_reads_cache()
                    st.session_state["_venda_excluida"] = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Falha ao excluir: {e}")

    # Métricas do mês corrente.
    hoje = date.today()
    mes_atual = f"{hoje.year:04d}-{hoje.month:02d}"
    vendas_mes = [v for v in vendas if v.data.startswith(mes_atual)]
    total_mes = sum(v.valor_total for v in vendas_mes)
    total_ano = sum(v.valor_total for v in vendas)
    lucro_ano = sum(v.lucro_total for v in vendas)
    saldo_aberto = sum(v.saldo for v in vendas)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total vendido no mês", formatar_brl(total_mes))
    c2.metric("Total vendido no ano", formatar_brl(total_ano))
    c3.metric("Lucro estimado no ano", formatar_brl(lucro_ano))
    c4.metric("A receber (vendas em aberto)", formatar_brl(saldo_aberto))

    # ── Filtros ──────────────────────────────────────────────────────
    if vendas:
        produtos_distintos = sorted({v.produto for v in vendas if v.produto})
        categorias_distintas = sorted({v.categoria for v in vendas if v.categoria})

        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        f_produto = col_f1.selectbox(
            "Produto", ["Todos"] + produtos_distintos, key="f_venda_produto"
        )
        f_categoria = col_f2.selectbox(
            "Categoria", ["Todas"] + categorias_distintas, key="f_venda_categoria"
        )
        datas_existentes = [v.data for v in vendas if v.data]
        try:
            data_min = min(date.fromisoformat(d) for d in datas_existentes)
            data_max = max(date.fromisoformat(d) for d in datas_existentes)
        except ValueError:
            data_min = data_max = hoje
        f_data_ini = col_f3.date_input(
            "De", value=data_min, format="DD/MM/YYYY", key="f_venda_data_ini"
        )
        f_data_fim = col_f4.date_input(
            "Até", value=data_max, format="DD/MM/YYYY", key="f_venda_data_fim"
        )

        f_status = st.radio(
            "Status pagamento",
            ["todos", "pago", "parcial", "pendente"],
            horizontal=True,
            key="f_venda_status",
        )

        vendas_filtradas = []
        for v in vendas:
            if f_produto != "Todos" and v.produto != f_produto:
                continue
            if f_categoria != "Todas" and v.categoria != f_categoria:
                continue
            if v.data:
                try:
                    d = date.fromisoformat(v.data)
                    if d < f_data_ini or d > f_data_fim:
                        continue
                except ValueError:
                    pass
            if f_status != "todos" and v.status_pagamento != f_status:
                continue
            vendas_filtradas.append(v)

        st.caption(f"Mostrando {len(vendas_filtradas)} de {len(vendas)} vendas.")

        rows_vendas = []
        for v in sorted(vendas_filtradas, key=lambda v: v.data, reverse=True):
            if v.tipo_comprador in {"atleta", "associado"} and v.id_membro:
                m = membros_por_id.get(v.id_membro)
                comprador_label = m.nome if m else (v.comprador or v.id_membro)
            else:
                comprador_label = v.comprador or "—"
            rows_vendas.append(
                {
                    "Data": formatar_data_br(v.data),
                    "Produto": v.produto,
                    "Categoria": v.categoria or "—",
                    "Qtd": v.quantidade,
                    "Total": formatar_brl(v.valor_total),
                    "Pago": formatar_brl(v.valor_pago),
                    "Saldo": formatar_brl(v.saldo),
                    "Status": v.status_pagamento,
                    "Lucro": formatar_brl(v.lucro_total),
                    "Comprador": comprador_label,
                    "Tipo": _TIPO_LABELS.get(v.tipo_comprador, v.tipo_comprador),
                    "Contato": v.contato_comprador or "—",
                    "Observações": v.observacoes,
                }
            )
        if rows_vendas:
            st.dataframe(pd.DataFrame(rows_vendas), use_container_width=True, hide_index=True)

            st.markdown("**Editar venda:**")
            vendas_ord = sorted(vendas_filtradas, key=lambda v: v.data, reverse=True)
            labels_v = [
                f"{formatar_data_br(v.data)} · {v.produto} · "
                f"{v.comprador or '—'} · {formatar_brl(v.valor_total)}"
                for v in vendas_ord
            ]
            ids_v = [v.id_venda for v in vendas_ord]
            col_sv, col_bv = st.columns([4, 1])
            sel_v = col_sv.selectbox(
                "Venda", labels_v, key="venda_edit_sel", label_visibility="collapsed"
            )
            if col_bv.button("✏️ Editar", use_container_width=True, key="btn_editar_venda"):
                _modal_editar_venda(ids_v[labels_v.index(sel_v)])
        else:
            st.info("Nenhuma venda corresponde aos filtros.")
    else:
        st.info("Nenhuma venda registrada ainda.")

    st.markdown("---")
    with st.expander("➕ Registrar nova venda", expanded=not vendas):
        # ── Seleção de produto (fora do form para reagir à mudança) ──
        if not produtos_catalogo:
            st.warning(
                "Nenhum produto cadastrado no catálogo. "
                "Adicione produtos na aba `produtos` da planilha antes de registrar vendas."
            )

        produto_opcoes = ["— selecione —"] + [
            f"{p.nome} ({p.id_produto})" for p in produtos_catalogo
        ]
        produto_escolhido_label = st.selectbox(
            "Produto",
            produto_opcoes,
            key="venda_produto",
            disabled=not produtos_catalogo,
        )
        produto_escolhido = None
        if produto_escolhido_label != "— selecione —" and produtos_catalogo:
            idx = produto_opcoes.index(produto_escolhido_label) - 1
            produto_escolhido = produtos_catalogo[idx]

        custo_default = produto_escolhido.custo_padrao if produto_escolhido else 0.0
        preco_default = produto_escolhido.preco_padrao if produto_escolhido else 0.0
        categoria_default = produto_escolhido.categoria if produto_escolhido else ""

        tipo_comprador = st.radio(
            "Tipo do comprador",
            options=["atleta", "associado", "externo"],
            format_func=lambda t: _TIPO_LABELS[t],
            horizontal=True,
            key="venda_tipo_comprador",
        )

        with st.form("form_nova_venda", clear_on_submit=True):
            data_venda = st.date_input("Data da venda", value=date.today(), format="DD/MM/YYYY")
            quantidade = st.number_input("Quantidade", min_value=1, step=1, value=1)

            col_custo, col_preco = st.columns(2)
            custo_unit = col_custo.number_input(
                "Custo unitário (R$)",
                min_value=0.0,
                value=float(custo_default),
                step=1.0,
                format="%.2f",
                help="Quanto cada unidade custou pra produzir/comprar.",
            )
            valor_unit = col_preco.number_input(
                "Preço de venda unitário (R$)",
                min_value=0.0,
                value=float(preco_default),
                step=1.0,
                format="%.2f",
            )

            categoria_venda = st.text_input(
                "Categoria",
                value=categoria_default,
                help="Pré-preenchido pelo catálogo. Pode editar.",
            )

            id_membro_venda = ""
            comprador_nome = ""
            if tipo_comprador in {"atleta", "associado"}:
                membros_filtrados = [
                    m for m in membros_para_compra if m.tipo == tipo_comprador
                ]
                if membros_filtrados:
                    membro_labels = [
                        f"{m.nome} ({m.id_membro})"
                        + (" — inativo" if m.status == "inativo" else "")
                        for m in membros_filtrados
                    ]
                    membro_label_sel = st.selectbox(
                        f"{_TIPO_LABELS[tipo_comprador]} comprador",
                        membro_labels,
                        key="venda_membro",
                    )
                    membro_idx = membro_labels.index(membro_label_sel)
                    membro_sel = membros_filtrados[membro_idx]
                    id_membro_venda = membro_sel.id_membro
                    comprador_nome = membro_sel.nome
                else:
                    st.warning(f"Nenhum membro do tipo {tipo_comprador} cadastrado.")
            else:
                comprador_nome = st.text_input("Nome do comprador *")
            contato_comprador = st.text_input(
                "Contato (opcional)", placeholder="Telefone ou e-mail"
            )

            qtd_prev = int(quantidade)
            total_prev = round(qtd_prev * float(valor_unit), 2)

            valor_pago_input = st.number_input(
                "Valor já pago (R$)",
                min_value=0.0,
                value=float(total_prev),
                step=5.0,
                format="%.2f",
                help=(
                    "Default = total da venda (pago integralmente). "
                    "Coloque 0 se ainda não recebeu, ou um valor parcial."
                ),
            )

            obs_venda = st.text_area("Observações")
            comprovante_venda = st.file_uploader(
                "Comprovante (PDF, PNG ou JPG) — opcional",
                type=["pdf", "png", "jpg", "jpeg"],
                accept_multiple_files=False,
                key="comp_venda",
            )

            lucro_prev = round((float(valor_unit) - float(custo_unit)) * qtd_prev, 2)
            saldo_prev = round(max(total_prev - float(valor_pago_input), 0.0), 2)
            st.caption(
                f"Total: {formatar_brl(total_prev)} · "
                f"Saldo: {formatar_brl(saldo_prev)} · "
                f"Lucro estimado: {formatar_brl(lucro_prev)}"
            )

            salvar_venda = st.form_submit_button("Salvar venda", type="primary")

        if salvar_venda:
            if produto_escolhido is None:
                st.error("Selecione um produto do catálogo.")
                st.stop()
            if not comprador_nome.strip():
                st.error("Nome do comprador é obrigatório.")
                st.stop()
            if valor_unit <= 0:
                st.error("Informe um preço de venda maior que zero.")
                st.stop()

            link_comp_venda = ""
            if comprovante_venda is not None:
                try:
                    with st.spinner("Enviando comprovante..."):
                        link_comp_venda = upload_service.upload_comprovante_venda(
                            produto=produto_escolhido.nome,
                            data_iso=data_venda.isoformat(),
                            nome_arquivo_origem=comprovante_venda.name,
                            conteudo=comprovante_venda.getvalue(),
                        )
                except Exception as e:
                    st.error(f"Falha no upload: {e}")
                    st.stop()

            qtd = int(quantidade)
            v_unit = round(float(valor_unit), 2)
            c_unit = round(float(custo_unit), 2)
            v_total = round(qtd * v_unit, 2)
            v_pago = min(round(float(valor_pago_input), 2), v_total)
            venda_dict = {
                "data": data_venda.isoformat(),
                "produto": produto_escolhido.nome,
                "id_produto": produto_escolhido.id_produto,
                "categoria": categoria_venda.strip(),
                "quantidade": qtd,
                "valor_unitario": v_unit,
                "valor_total": v_total,
                "valor_pago": v_pago,
                "custo_unitario": c_unit,
                "tipo_comprador": tipo_comprador,
                "id_membro": id_membro_venda,
                "comprador": comprador_nome.strip(),
                "contato_comprador": contato_comprador.strip(),
                "link_comprovante": link_comp_venda,
                "observacoes": obs_venda.strip(),
                "ativo": True,
            }
            try:
                with st.spinner("Salvando venda..."):
                    vendas_repo.criar(venda_dict)
                    clear_reads_cache()
                lucro_total = round((v_unit - c_unit) * qtd, 2)
                st.success(
                    f"Venda registrada: **{produto_escolhido.nome}** × {qtd} = "
                    f"{formatar_brl(qtd * v_unit)} (lucro: {formatar_brl(lucro_total)})."
                )
                if link_comp_venda:
                    st.markdown(f"[Abrir comprovante]({link_comp_venda})")
                st.rerun()
            except Exception as e:
                st.error(f"Falha ao salvar: {e}")
