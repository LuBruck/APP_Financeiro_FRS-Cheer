"""Tela 7.3 — Cobranças pendentes em tabela dinâmica + modal de edição."""

from __future__ import annotations

import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st  # noqa: E402

from app.auth import render_sidebar_user, require_login  # noqa: E402
from app.repositories import membros_repo, pagamentos_repo  # noqa: E402
from app.repositories.base import clear_reads_cache  # noqa: E402
from app.services import calculo_dividas, upload_service  # noqa: E402
from app.utils.formatters import formatar_brl, formatar_data_br  # noqa: E402

st.set_page_config(page_title="Cobranças Pendentes", page_icon="📋", layout="wide")
require_login()
render_sidebar_user()

st.title("Cobranças Pendentes")

with st.spinner("Verificando cobranças do mês..."):
    calculo_dividas.garantir_pendencias_sessao()

# ─── Notificações pós-modal ──────────────────────────────────────────
if st.session_state.pop("_cobranca_salva", False):
    st.success("Cobrança atualizada com sucesso!")
if st.session_state.pop("_cobranca_excluida", False):
    st.success("Cobrança excluída.")

# ─── Carregamento de dados ───────────────────────────────────────────
STATUS_VISIVEIS = {"pendente", "parcial", "avisado"}
pagamentos_ativos = [p for p in pagamentos_repo.listar_todos() if p.status in STATUS_VISIVEIS]
membros_por_id = {m.id_membro: m for m in membros_repo.listar_todos(incluir_inativos=True)}

if not pagamentos_ativos:
    st.success("Nenhuma cobrança em aberto.")
    st.stop()

hoje = date.today()
itens: list[dict] = []
for p in pagamentos_ativos:
    m = membros_por_id.get(p.id_membro)
    if m is None:
        continue
    itens.append(
        {
            "pagamento": p,
            "membro": m,
            "dias_atraso": calculo_dividas.dias_em_atraso(p.data_vencimento, hoje),
        }
    )

if not itens:
    st.success("Nenhuma cobrança em aberto.")
    st.stop()

# ─── Filtros ─────────────────────────────────────────────────────────
c1, c2 = st.columns([3, 1])
busca = c1.text_input("Buscar por nome", "")
tipo_filtro = c2.radio("Tipo de membro", ["Todos", "atleta", "associado"], horizontal=True)

if busca.strip():
    itens = [i for i in itens if busca.strip().lower() in i["membro"].nome.lower()]
if tipo_filtro != "Todos":
    itens = [i for i in itens if i["membro"].tipo == tipo_filtro]

# ─── Métricas ────────────────────────────────────────────────────────
total_aberto = sum(i["pagamento"].saldo_devedor for i in itens)
n_membros = len({i["membro"].id_membro for i in itens})

m1, m2, m3 = st.columns(3)
m1.metric("Total em aberto", formatar_brl(total_aberto))
m2.metric("Cobranças em aberto", len(itens))
m3.metric("Membros com pendência", n_membros)

st.divider()

# ─── Modal de edição ─────────────────────────────────────────────────
_STATUS_OPCOES = ["pendente", "avisado", "isento", "parcial", "pago", "cancelado"]


def _formatar_tipo(mes_referencia: str) -> str:
    """'2025-12' -> 'Mensalidade 12/2025'. Fallback: retorna o valor original."""
    try:
        ano, mes = mes_referencia.split("-")
        if len(ano) == 4 and len(mes) == 2:
            return f"Mensalidade {mes}/{ano}"
    except (ValueError, AttributeError):
        pass
    return mes_referencia


@st.dialog("Editar cobrança", width="large")
def _modal_editar(id_pagamento: str) -> None:
    p = pagamentos_repo.get_by_id(id_pagamento)
    if p is None:
        st.error("Cobrança não encontrada.")
        return

    membro = membros_por_id.get(p.id_membro)
    nome_membro = membro.nome if membro else p.id_membro
    st.caption(f"Membro: **{nome_membro}** · {_formatar_tipo(p.mes_referencia)} · ID: {p.id_pagamento}")

    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Referência", value=p.mes_referencia, disabled=True)
        novo_valor = st.number_input(
            "Valor original (R$)", value=float(p.valor_original), min_value=0.0, step=0.01, format="%.2f"
        )
        nova_multa = st.number_input(
            "Multa (R$)", value=float(p.multa), min_value=0.0, step=0.01, format="%.2f"
        )
        try:
            venc_default = date.fromisoformat(p.data_vencimento)
        except ValueError:
            venc_default = hoje
        nova_venc = st.date_input("Data de vencimento", value=venc_default)

    with col2:
        status_idx = _STATUS_OPCOES.index(p.status) if p.status in _STATUS_OPCOES else 0
        novo_status = st.selectbox("Status", _STATUS_OPCOES, index=status_idx)
        novo_valor_pago = st.number_input(
            "Valor pago (R$)", value=float(p.valor_pago), min_value=0.0, step=0.01, format="%.2f"
        )
        pag_default = None
        if p.data_pagamento:
            try:
                pag_default = date.fromisoformat(p.data_pagamento)
            except ValueError:
                pass
        nova_data_pag = st.date_input("Data de pagamento", value=pag_default)

    nova_obs = st.text_area("Observações", value=p.observacoes, height=80)

    novo_comprovante = st.file_uploader(
        "Comprovante (substituir)", type=["pdf", "jpg", "jpeg", "png"]
    )
    if p.link_comprovante:
        st.markdown(f"[Ver comprovante atual]({p.link_comprovante})")

    st.divider()

    col_salvar, col_excluir = st.columns([3, 1])

    with col_salvar:
        if st.button("💾 Salvar alterações", type="primary", use_container_width=True):
            updates: dict = {
                "valor_original": novo_valor,
                "multa": nova_multa,
                "data_vencimento": nova_venc.isoformat(),
                "status": novo_status,
                "valor_pago": novo_valor_pago,
                "data_pagamento": nova_data_pag.isoformat() if nova_data_pag else "",
                "observacoes": nova_obs.strip(),
            }
            if novo_comprovante and membro:
                try:
                    link = upload_service.upload_comprovante_mensalidade(
                        membro=membro,
                        mes_referencia=p.mes_referencia,
                        nome_arquivo_origem=novo_comprovante.name,
                        conteudo=novo_comprovante.read(),
                    )
                    updates["link_comprovante"] = link
                except Exception as e:
                    st.error(f"Erro ao subir comprovante: {e}")
                    return
            try:
                pagamentos_repo.atualizar(p.id_pagamento, updates)
                clear_reads_cache()
                st.session_state["_cobranca_salva"] = True
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

    with col_excluir:
        confirmar = st.checkbox("Confirmar exclusão")
        if st.button(
            "🗑️ Excluir",
            disabled=not confirmar,
            use_container_width=True,
            type="primary" if confirmar else "secondary",
        ):
            try:
                pagamentos_repo.desativar(p.id_pagamento)
                st.session_state["_cobranca_excluida"] = True
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao excluir: {e}")


# ─── Tabela dinâmica (linhas expansíveis) ────────────────────────────
if "_membros_expandidos" not in st.session_state:
    st.session_state["_membros_expandidos"] = set()

grupos: dict[str, list[dict]] = defaultdict(list)
for item in itens:
    grupos[item["membro"].id_membro].append(item)

# Ordenar membros pelo maior saldo devedor
membros_ordenados = sorted(
    grupos.items(),
    key=lambda kv: sum(i["pagamento"].saldo_devedor for i in kv[1]),
    reverse=True,
)

# Cabeçalho da tabela
h_nome, h_total = st.columns([5, 1])
h_nome.markdown("**Membro**")
h_total.markdown("**Total devido**")
st.divider()

for id_membro, cobr_list in membros_ordenados:
    membro = cobr_list[0]["membro"]
    total_membro = sum(i["pagamento"].saldo_devedor for i in cobr_list)
    n = len(cobr_list)
    expandido = id_membro in st.session_state["_membros_expandidos"]
    seta = "▼" if expandido else "▶"

    row_nome, row_total = st.columns([5, 1])
    if row_nome.button(
        f"{seta}  {membro.nome}  · {n} pendência(s)",
        key=f"toggle_{id_membro}",
        use_container_width=True,
        type="tertiary",
    ):
        s = st.session_state["_membros_expandidos"]
        if id_membro in s:
            s.discard(id_membro)
        else:
            s.add(id_membro)
        st.rerun()
    row_total.markdown(f"**{formatar_brl(total_membro)}**")

    if expandido:
        with st.container(border=True):
            sh_tipo, sh_saldo, sh_data, sh_obs = st.columns([3, 1.3, 1.4, 3])
            sh_tipo.caption("Tipo")
            sh_saldo.caption("Saldo")
            sh_data.caption("Data limite")
            sh_obs.caption("Observações")

            for item in sorted(cobr_list, key=lambda x: x["pagamento"].data_vencimento):
                p = item["pagamento"]
                rc_tipo, rc_saldo, rc_data, rc_obs = st.columns([3, 1.3, 1.4, 3])
                if rc_tipo.button(
                    f"✏️ {_formatar_tipo(p.mes_referencia)}",
                    key=f"edit_{p.id_pagamento}",
                    use_container_width=True,
                    type="tertiary",
                    help="Clique para editar esta cobrança",
                ):
                    _modal_editar(p.id_pagamento)
                rc_saldo.write(formatar_brl(p.saldo_devedor))
                rc_data.write(formatar_data_br(p.data_vencimento))
                rc_obs.write(p.observacoes or "—")
