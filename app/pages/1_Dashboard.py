"""Tela 7.1 — Dashboard financeiro."""

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
    membros_repo,
    pagamentos_repo,
    vendas_repo,
)
from app.services import calculo_dividas, dashboard_service  # noqa: E402
from app.utils.formatters import formatar_brl, formatar_data_br, mes_referencia as fmt_mes  # noqa: E402

_MESES_LABELS = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
_COR_STATUS = {
    "Pago":     "background-color: #c8e6c9; color: #1b5e20",
    "Pendente": "background-color: #fff9c4; color: #856404",
    "Multa":    "background-color: #ffcdd2; color: #b71c1c",
    "Avisado":  "background-color: #bbdefb; color: #0d47a1",
    "Isento":   "background-color: #f0f0f0; color: #757575",
}

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
require_login()
render_sidebar_user()

# ─── Seletor de mês ──────────────────────────────────────────────────
hoje = date.today()
st.title("Dashboard")

col_titulo, col_mes = st.columns([3, 1])
with col_titulo:
    st.caption("Visão consolidada do caixa e inadimplência.")
with col_mes:
    meses_opcoes: list[str] = []
    ano_it, mes_it = hoje.year, hoje.month
    for _ in range(12):
        meses_opcoes.append(f"{ano_it:04d}-{mes_it:02d}")
        mes_it -= 1
        if mes_it == 0:
            mes_it = 12
            ano_it -= 1
    mes_sel = st.selectbox("Mês de referência", meses_opcoes, label_visibility="collapsed")

# ─── Carregamento de dados ───────────────────────────────────────────
with st.spinner("Verificando cobranças do mês..."):
    calculo_dividas.garantir_pendencias_sessao(mes_sel)

with st.spinner("Carregando dados..."):
    pagamentos = pagamentos_repo.listar_todos()
    despesas = despesas_repo.listar_todos()
    vendas = vendas_repo.listar_todos()
    membros = membros_repo.listar_todos(incluir_inativos=True)

membros_por_id = {m.id_membro: m.nome for m in membros}
membros_ativos = [m for m in membros if m.status == "ativo"]

tab_geral, tab_grade = st.tabs(["Visão geral", "Grade de mensalidades"])

with tab_geral:
    # ─── Alertas ─────────────────────────────────────────────────────────
    msgs = dashboard_service.alertas(
        pagamentos=pagamentos,
        n_membros_ativos=len(membros_ativos),
        hoje=hoje,
    )
    for msg in msgs:
        st.warning(msg)

    # ─── KPIs ────────────────────────────────────────────────────────────
    kpis = dashboard_service.calcular_kpis(
        pagamentos=pagamentos,
        despesas=despesas,
        vendas=vendas,
        mes_referencia=mes_sel,
        hoje=hoje,
    )

    k1, k2, k3, k4 = st.columns(4)
    k1.metric(
        "Caixa do mês",
        formatar_brl(kpis.caixa_mes),
        delta=None,
        delta_color="normal" if kpis.caixa_mes >= 0 else "inverse",
    )
    k2.metric("Inadimplência total", formatar_brl(kpis.inadimplencia_total))
    k3.metric(
        "Vencem em ≤ 7 dias",
        f"{kpis.vencimentos_7d_count} cobranças",
        delta=formatar_brl(kpis.vencimentos_7d_valor) if kpis.vencimentos_7d_count else None,
        delta_color="off",
    )
    k4.metric("Saldo acumulado do ano", formatar_brl(kpis.saldo_ano))

    st.divider()

    # ─── Gráficos ────────────────────────────────────────────────────────
    col_graf1, col_graf2 = st.columns([3, 2])

    with col_graf1:
        st.subheader("Evolução do caixa — últimos 6 meses")
        evolucao = dashboard_service.evolucao_caixa(
            pagamentos=pagamentos, despesas=despesas, vendas=vendas, n_meses=6, referencia=hoje
        )
        df_ev = pd.DataFrame(
            [{"Mês": r.mes, "Receitas": r.receitas, "Despesas": r.despesas, "Vendas": r.vendas, "Caixa": r.caixa}
             for r in evolucao]
        ).set_index("Mês")
        st.line_chart(df_ev[["Receitas", "Despesas", "Caixa"]])

    with col_graf2:
        st.subheader(f"Despesas por categoria — {mes_sel}")
        dist = dashboard_service.distribuicao_despesas_mes(despesas=despesas, mes=mes_sel)
        if dist:
            df_dist = pd.DataFrame(
                [{"Categoria": k, "Total": v} for k, v in sorted(dist.items(), key=lambda x: -x[1])]
            ).set_index("Categoria")
            st.bar_chart(df_dist)
        else:
            st.info("Nenhuma despesa registrada neste mês.")

    st.divider()

    # ─── Últimas transações ───────────────────────────────────────────────
    st.subheader("Últimas 10 transações")
    transacoes = dashboard_service.ultimas_transacoes(
        pagamentos=pagamentos,
        despesas=despesas,
        vendas=vendas,
        n=10,
        membros_por_id=membros_por_id,
    )

    if transacoes:
        df_trans = pd.DataFrame(
            [
                {
                    "Data": formatar_data_br(t.data),
                    "Tipo": t.tipo,
                    "Descrição": t.descricao,
                    "Valor": formatar_brl(t.valor),
                    "Fluxo": "↑ Entrada" if t.entrada else "↓ Saída",
                }
                for t in transacoes
            ]
        )

        def _cor_fluxo(row: pd.Series) -> list[str]:
            cor = "color: #2e7d32" if "Entrada" in str(row["Fluxo"]) else "color: #c62828"
            return [""] * (len(row) - 1) + [cor]

        st.dataframe(
            df_trans.style.apply(_cor_fluxo, axis=1),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Nenhuma transação registrada ainda.")

with tab_grade:
    # ─── Grade de mensalidades do ano ────────────────────────────────────
    anos_disponiveis = sorted(
        {p.mes_referencia[:4] for p in pagamentos if len(p.mes_referencia) >= 4},
        reverse=True,
    )
    if str(hoje.year) not in anos_disponiveis:
        anos_disponiveis.insert(0, str(hoje.year))

    col_titulo_grade, col_ano_grade = st.columns([3, 1])
    with col_titulo_grade:
        st.subheader("Mensalidades")
    with col_ano_grade:
        ano_grade = st.selectbox(
            "Ano",
            anos_disponiveis,
            index=0,
            key="ano_grade_dash",
            label_visibility="collapsed",
        )

    meses_ano = [f"{ano_grade}-{m:02d}" for m in range(1, 13)]

    pag_index: dict[str, dict[str, object]] = {}
    for p in pagamentos:
        if p.mes_referencia.startswith(ano_grade):
            pag_index.setdefault(p.id_membro, {})[p.mes_referencia] = p

    ids_com_cobranca_no_ano = set(pag_index.keys())
    membros_grade = sorted(
        [m for m in membros if m.id_membro in ids_com_cobranca_no_ano],
        key=lambda m: m.nome,
    )

    busca_grade = st.text_input("Filtrar por nome na grade", "", key="busca_grade_dash")

    grade_rows = []
    for m in membros_grade:
        if busca_grade.strip() and busca_grade.strip().lower() not in m.nome.lower():
            continue
        nome_label = f"{m.nome} (inativo)" if m.status == "inativo" else m.nome
        row: dict = {"Nome": nome_label}
        for mes_ref, label in zip(meses_ano, _MESES_LABELS):
            p = pag_index.get(m.id_membro, {}).get(mes_ref)
            row[label] = calculo_dividas.status_grade(p, hoje) if p else ""
        grade_rows.append(row)

    if grade_rows:
        df_grade = pd.DataFrame(grade_rows)

        def _cor_celula(val: str) -> str:
            return _COR_STATUS.get(val, "")

        styler = df_grade.style
        _fn = getattr(styler, "map", None) or getattr(styler, "applymap")
        styled = _fn(_cor_celula, subset=_MESES_LABELS)

        st.dataframe(styled, use_container_width=True, hide_index=True)

        leg = st.columns(5)
        leg[0].markdown("🟢 **Pago**")
        leg[1].markdown("🟡 **Pendente**")
        leg[2].markdown("🔴 **Multa**")
        leg[3].markdown("🔵 **Avisado**")
        leg[4].markdown("⚫ **Isento**")
    else:
        st.info("Nenhum membro com cobrança neste ano.")
