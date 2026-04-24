"""Tela 7.6 — Histórico financeiro de um membro."""

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
from app.repositories import membros_repo, pagamentos_repo  # noqa: E402
from app.services.calculo_dividas import dias_em_atraso  # noqa: E402
from app.utils.formatters import formatar_brl, formatar_data_br, mes_referencia as fmt_mes  # noqa: E402

st.set_page_config(page_title="Histórico do membro", page_icon="👤", layout="wide")
require_login()
render_sidebar_user()

st.title("Histórico do membro")
st.caption("Extrato completo de mensalidades de um membro.")

# ─── Seleção de membro ───────────────────────────────────────────────
membros = membros_repo.listar_todos(incluir_inativos=True)
if not membros:
    st.warning("Nenhum membro cadastrado.")
    st.stop()

membros_map = {f"{m.nome} ({m.id_membro}) {'[inativo]' if m.status == 'inativo' else ''}".strip(): m
               for m in sorted(membros, key=lambda m: m.nome)}

membro_label = st.selectbox("Selecione o membro", list(membros_map.keys()))
membro = membros_map[membro_label]

# ─── Dados cadastrais ────────────────────────────────────────────────
with st.expander("Dados cadastrais", expanded=True):
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"**Nome:** {membro.nome}")
    c2.markdown(f"**ID:** `{membro.id_membro}`")
    c3.markdown(f"**Tipo:** {membro.tipo}")
    c4.markdown(f"**Status:** {membro.status}")
    if membro.email:
        st.markdown(f"**Email:** {membro.email}")
    if membro.semestre_entrada:
        st.markdown(f"**Semestre de entrada:** {membro.semestre_entrada}")
    if membro.observacoes:
        st.markdown(f"**Observações:** {membro.observacoes}")

# ─── Pagamentos do membro ────────────────────────────────────────────
pagamentos = pagamentos_repo.listar_por_membro(membro.id_membro)

if not pagamentos:
    st.info("Nenhuma cobrança registrada para este membro.")
    st.stop()

hoje = date.today()
ano_atual = str(hoje.year)

# Resumos
pags_pagos = [p for p in pagamentos if p.status == "pago"]
pags_pendentes = [p for p in pagamentos if p.status in {"pendente", "parcial"}]

total_pago_ano = sum(p.valor_pago for p in pagamentos if p.mes_referencia.startswith(ano_atual))
saldo_devedor = sum(p.saldo_devedor for p in pags_pendentes)
n_atrasos = sum(1 for p in pagamentos if dias_em_atraso(p.data_vencimento, hoje) > 0)

st.divider()

# ─── Métricas de resumo ──────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total pago no ano", formatar_brl(total_pago_ano))
m2.metric("Saldo devedor atual", formatar_brl(saldo_devedor))
m3.metric("Mensalidades quitadas", len(pags_pagos))
m4.metric("Atrasos históricos", n_atrasos)

# ─── Tabela de mensalidades ──────────────────────────────────────────
st.subheader("Extrato de mensalidades")

STATUS_EMOJI = {"pago": "✅", "parcial": "⚠️", "pendente": "🔴", "cancelado": "❌"}

rows = []
for p in sorted(pagamentos, key=lambda p: p.mes_referencia, reverse=True):
    dias = dias_em_atraso(p.data_vencimento, hoje)
    comp_link = f"[📎 ver]({p.link_comprovante})" if p.link_comprovante else "—"
    rows.append(
        {
            "Mês ref.": p.mes_referencia,
            "Vencimento": formatar_data_br(p.data_vencimento),
            "Status": f"{STATUS_EMOJI.get(p.status, '')} {p.status}",
            "Valor original": formatar_brl(p.valor_original),
            "Multa": formatar_brl(p.multa) if p.multa else "—",
            "Valor pago": formatar_brl(p.valor_pago),
            "Saldo devedor": formatar_brl(p.saldo_devedor) if p.saldo_devedor > 0 else "—",
            "Data pagamento": formatar_data_br(p.data_pagamento) if p.data_pagamento else "—",
            "Dias em atraso": dias if dias > 0 else "—",
            "Comprovante": comp_link,
            "Observações": p.observacoes or "—",
        }
    )

df = pd.DataFrame(rows)

# Coloração por status
_STATUS_BG = {
    "✅ pago": "#e6f4ea",
    "⚠️ parcial": "#fff4e5",
    "🔴 pendente": "#fdecea",
    "❌ cancelado": "#f5f5f5",
}


def _cor_status(row: pd.Series) -> list[str]:
    bg = _STATUS_BG.get(str(row["Status"]), "")
    estilo = f"background-color: {bg}; color: #1a1a1a" if bg else ""
    return [estilo] * len(row)


st.dataframe(
    df.style.apply(_cor_status, axis=1),
    use_container_width=True,
    hide_index=True,
)

# ─── Exportar CSV ────────────────────────────────────────────────────
csv = df.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Exportar histórico (CSV)",
    data=csv,
    file_name=f"historico_{membro.id_membro}_{hoje.isoformat()}.csv",
    mime="text/csv",
)

# ─── Ação rápida ─────────────────────────────────────────────────────
if pags_pendentes:
    st.divider()
    st.subheader("Ação rápida")
    pend_labels = [
        f"{p.mes_referencia} — {formatar_brl(p.saldo_devedor)}" for p in
        sorted(pags_pendentes, key=lambda p: p.mes_referencia)
    ]
    idx = st.selectbox("Registrar pagamento de:", range(len(pend_labels)),
                       format_func=lambda i: pend_labels[i])
    if st.button("Ir para Registrar Pagamento", type="primary"):
        pag_sel = sorted(pags_pendentes, key=lambda p: p.mes_referencia)[idx]
        st.query_params["id_membro"] = membro.id_membro
        st.query_params["mes"] = pag_sel.mes_referencia
        st.switch_page("pages/2_Registrar_Pagamento.py")
