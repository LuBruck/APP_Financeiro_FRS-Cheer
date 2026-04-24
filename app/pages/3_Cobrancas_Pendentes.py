"""Tela 7.3 — Cobranças pendentes (filtros + tabela + exportar CSV)."""

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
from app.services import calculo_dividas  # noqa: E402
from app.utils.formatters import formatar_brl, formatar_data_br  # noqa: E402

st.set_page_config(page_title="Cobranças pendentes", page_icon="📋", layout="wide")
require_login()
render_sidebar_user()

st.title("Cobranças pendentes")
st.caption("Mensalidades em aberto (pendentes ou parciais).")

with st.spinner("Verificando cobranças do mês..."):
    calculo_dividas.garantir_pendencias_sessao()

pagamentos = [p for p in pagamentos_repo.listar_todos() if p.status in {"pendente", "parcial"}]
membros_por_id = {m.id_membro: m for m in membros_repo.listar_todos(incluir_inativos=True)}

if not pagamentos:
    st.success("Nenhuma cobrança em aberto. 🎉")
    st.stop()

# ---------- Montagem do DataFrame base ----------
hoje = date.today()
rows: list[dict] = []
for p in pagamentos:
    m = membros_por_id.get(p.id_membro)
    if m is None:
        continue
    dias = calculo_dividas.dias_em_atraso(p.data_vencimento, hoje)
    rows.append(
        {
            "id_pagamento": p.id_pagamento,
            "id_membro": m.id_membro,
            "Membro": m.nome,
            "Tipo": m.tipo,
            "Mês referência": p.mes_referencia,
            "Vencimento": p.data_vencimento,
            "Valor devido": round(p.valor_original + p.multa - p.valor_pago, 2),
            "Dias em atraso": dias,
            "Status": p.status,
            "Última observação": p.observacoes,
        }
    )
df = pd.DataFrame(rows)

# ---------- Filtros ----------
st.subheader("Filtros")
c1, c2, c3, c4, c5 = st.columns([2, 1.2, 1, 1.2, 1.4])
busca = c1.text_input("Buscar por nome", "")
meses_disp = sorted(df["Mês referência"].unique().tolist())
mes_filtro = c2.selectbox("Mês", ["Todos"] + meses_disp, index=0)
tipo_filtro = c3.radio("Tipo", ["todos", "atleta", "associado"], horizontal=False)
status_filtro = c4.multiselect(
    "Status", ["pendente", "parcial"], default=["pendente", "parcial"]
)
faixa_atraso = c5.radio(
    "Faixa de atraso",
    ["todos", "em dia", "atrasado", "atrasado > 7 dias"],
    horizontal=False,
)

mask = pd.Series([True] * len(df))
if busca.strip():
    mask &= df["Membro"].str.contains(busca.strip(), case=False, na=False)
if mes_filtro != "Todos":
    mask &= df["Mês referência"] == mes_filtro
if tipo_filtro != "todos":
    mask &= df["Tipo"] == tipo_filtro
if status_filtro:
    mask &= df["Status"].isin(status_filtro)
if faixa_atraso == "em dia":
    mask &= df["Dias em atraso"] == 0
elif faixa_atraso == "atrasado":
    mask &= df["Dias em atraso"] > 0
elif faixa_atraso == "atrasado > 7 dias":
    mask &= df["Dias em atraso"] > 7

filtrado = df.loc[mask].sort_values("Dias em atraso", ascending=False).reset_index(drop=True)

# ---------- Métricas ----------
total_aberto = float(filtrado["Valor devido"].sum())
n_cobrancas = len(filtrado)
n_membros = filtrado["id_membro"].nunique() if not filtrado.empty else 0

m1, m2, m3 = st.columns(3)
m1.metric("Total em aberto", formatar_brl(total_aberto))
m2.metric("Cobranças filtradas", n_cobrancas)
m3.metric("Membros com pendência", n_membros)

# ---------- Tabela ----------
if filtrado.empty:
    st.info("Nenhuma cobrança bate com os filtros.")
    st.stop()


def _cor_linha(row: pd.Series) -> list[str]:
    dias = row["Dias em atraso"]
    if dias == 0:
        estilo = "background-color: #e6f4ea; color: #1a1a1a"
    elif dias < 7:
        estilo = "background-color: #fff4e5; color: #1a1a1a"
    else:
        estilo = "background-color: #fdecea; color: #1a1a1a"
    return [estilo] * len(row)


exibicao = filtrado.drop(columns=["id_pagamento", "id_membro"]).copy()
exibicao["Valor devido"] = exibicao["Valor devido"].map(formatar_brl)
exibicao["Vencimento"] = exibicao["Vencimento"].map(formatar_data_br)

st.dataframe(
    exibicao.style.apply(_cor_linha, axis=1),
    use_container_width=True,
    hide_index=True,
)

# ---------- Ações ----------
st.subheader("Ações")
c_acao_1, c_acao_2 = st.columns([2, 1])

linhas_opcoes = [
    f"{r['Membro']} — {r['Mês referência']} — {formatar_brl(r['Valor devido'])}"
    for _, r in filtrado.iterrows()
]
idx = c_acao_1.selectbox(
    "Selecione uma cobrança",
    options=range(len(linhas_opcoes)),
    format_func=lambda i: linhas_opcoes[i],
)

if c_acao_1.button("Registrar pagamento desta cobrança", type="primary"):
    linha = filtrado.iloc[idx]
    st.query_params["id_membro"] = linha["id_membro"]
    st.query_params["mes"] = linha["Mês referência"]
    st.switch_page("pages/2_Registrar_Pagamento.py")

csv = filtrado.drop(columns=["id_pagamento", "id_membro"]).to_csv(index=False).encode("utf-8")
c_acao_2.download_button(
    "Exportar filtro atual (CSV)",
    data=csv,
    file_name=f"cobrancas_pendentes_{hoje.isoformat()}.csv",
    mime="text/csv",
)
