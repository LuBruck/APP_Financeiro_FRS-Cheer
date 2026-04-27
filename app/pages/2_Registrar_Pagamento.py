"""Tela 7.2 — Registrar pagamento de mensalidade."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st  # noqa: E402

from app.auth import render_sidebar_user, require_login  # noqa: E402
from app.repositories import (  # noqa: E402
    configuracoes_repo,
    membros_repo,
    pagamentos_repo,
)
from app.services import calculo_dividas  # noqa: E402
from app.utils.formatters import formatar_brl, mes_referencia as fmt_mes_ref  # noqa: E402

st.set_page_config(page_title="Registrar pagamento", page_icon="💳", layout="wide")
require_login()
render_sidebar_user()

st.title("Registrar pagamento")

membros = membros_repo.listar_todos(incluir_inativos=False)
if not membros:
    st.warning("Nenhum membro ativo cadastrado. Adicione membros na aba `membros`.")
    st.stop()

config = configuracoes_repo.carregar()

# Últimos 12 meses + o corrente (compartilhado entre as duas abas).
hoje = date.today()
meses_opcoes: list[str] = []
ano, mes = hoje.year, hoje.month
for _ in range(36):
    meses_opcoes.append(f"{ano:04d}-{mes:02d}")
    mes -= 1
    if mes == 0:
        mes = 12
        ano -= 1

tab_individual, tab_massa = st.tabs(["Pagamento individual", "Gerar cobranças em massa"])

# ─── Aba 1: Pagamento individual ─────────────────────────────────────────────
with tab_individual:
    st.caption("Registra o recebimento de mensalidade de um membro por vez.")

    # Garante que o mês corrente tenha linhas pendentes.
    with st.spinner("Verificando cobranças do mês..."):
        calculo_dividas.garantir_pendencias_sessao()

    # Pré-seleção via query params (vindo da tela de Cobranças Pendentes).
    qp = st.query_params
    membro_pre = qp.get("id_membro")
    mes_pre = qp.get("mes")

    membros_map = {f"{m.nome} ({m.id_membro})": m for m in membros}
    default_label = None
    if membro_pre:
        for label, m in membros_map.items():
            if m.id_membro == membro_pre:
                default_label = label
                break
    membro_label = st.selectbox(
        "Membro",
        options=list(membros_map.keys()),
        index=list(membros_map.keys()).index(default_label) if default_label else 0,
        key="ind_membro",
    )
    membro = membros_map[membro_label]

    default_mes = mes_pre if mes_pre in meses_opcoes else fmt_mes_ref(hoje)
    mes_selecionado = st.selectbox(
        "Mês de referência",
        meses_opcoes,
        index=meses_opcoes.index(default_mes),
        key="ind_mes",
    )

    pagamento = pagamentos_repo.get_por_membro_e_mes(membro.id_membro, mes_selecionado)
    if pagamento is None:
        st.info(
            "Não há linha de cobrança para este membro neste mês. "
            "Ela será criada automaticamente ao salvar."
        )
        valor_sugerido = config.valor_mensalidade(membro.tipo)
        multa_ja_aplicada = 0.0
        em_atraso = False
        saldo = valor_sugerido
    else:
        if pagamento.status == "pago":
            st.success(
                f"Mensalidade de **{mes_selecionado}** já está quitada "
                f"(valor pago: {formatar_brl(pagamento.valor_pago)})."
            )
        valor_sugerido = pagamento.valor_original
        multa_ja_aplicada = pagamento.multa
        em_atraso = calculo_dividas.esta_em_atraso(pagamento.data_vencimento)
        saldo = pagamento.saldo_devedor

    colA, colB, colC = st.columns(3)
    colA.metric("Valor mensalidade", formatar_brl(valor_sugerido))
    colB.metric("Multa já aplicada", formatar_brl(multa_ja_aplicada))
    colC.metric("Saldo devedor", formatar_brl(saldo))

    with st.form("form_pagamento", clear_on_submit=True):
        st.subheader("Dados do pagamento")

        aplicar_multa_default = em_atraso and multa_ja_aplicada == 0
        aplicar_multa = st.checkbox(
            f"Aplicar multa de atraso ({formatar_brl(config.valor_multa_atraso)})",
            value=aplicar_multa_default,
            help="Sugerido automaticamente quando a data de vencimento já passou.",
        )

        multa_efetiva = (
            config.valor_multa_atraso if (aplicar_multa and multa_ja_aplicada == 0) else multa_ja_aplicada
        )
        valor_devido = max(valor_sugerido + multa_efetiva - (pagamento.valor_pago if pagamento else 0.0), 0.0)

        valor_pago = st.number_input(
            "Valor pago agora (R$)",
            min_value=0.0,
            value=float(valor_devido),
            step=5.0,
            format="%.2f",
            help="Valor recebido neste ato. Se parcial, o saldo restante continuará em aberto.",
        )
        data_pag = st.date_input(
            "Data do pagamento",
            value=hoje,
            format="DD/MM/YYYY",
            help="Data em que o PIX foi recebido (pode diferir da data de hoje).",
        )

        observacoes = st.text_area(
            "Observações",
            placeholder="Obrigatório se o pagamento for parcial.",
            help="Obrigatório quando o valor pago for menor que o total devido.",
        )

        comprovante = st.file_uploader(
            "Comprovante (PDF, PNG ou JPG)",
            type=["pdf", "png", "jpg", "jpeg"],
            accept_multiple_files=False,
            help="Recomendado. O arquivo será salvo no Google Drive vinculado a este membro e mês.",
        )

        submitted = st.form_submit_button("Salvar pagamento", type="primary")

    if submitted:
        if valor_pago <= 0:
            st.error("Informe um valor maior que zero.")
            st.stop()

        if pagamento is None:
            calculo_dividas.gerar_pendencias_do_mes(mes_selecionado)
            pagamento = pagamentos_repo.get_por_membro_e_mes(membro.id_membro, mes_selecionado)
            if pagamento is None:
                st.error("Falha ao criar linha de cobrança para este mês.")
                st.stop()

        comp_bytes = comprovante.getvalue() if comprovante is not None else None
        comp_name = comprovante.name if comprovante is not None else None

        try:
            with st.spinner("Salvando pagamento..."):
                resultado = calculo_dividas.registrar_pagamento(
                    id_pagamento=pagamento.id_pagamento,
                    valor_pago_agora=float(valor_pago),
                    data_pagamento=data_pag,
                    aplicar_multa=aplicar_multa,
                    observacoes=observacoes,
                    comprovante_bytes=comp_bytes,
                    comprovante_filename=comp_name,
                )
        except ValueError as e:
            st.error(str(e))
            st.stop()
        except Exception as e:  # pragma: no cover
            st.error(f"Erro inesperado: {e}")
            st.stop()

        if resultado.status == "pago":
            st.success(
                f"Pagamento registrado. Status: **pago**. "
                f"Total recebido: {formatar_brl(resultado.valor_pago_total)}."
            )
        elif resultado.status == "parcial":
            st.warning(
                f"Pagamento parcial registrado. Saldo restante: "
                f"{formatar_brl(resultado.saldo_restante)}."
            )
        else:
            st.info(f"Status atual: {resultado.status}.")

        if resultado.link_comprovante:
            st.markdown(f"[Abrir comprovante no Drive]({resultado.link_comprovante})")

        st.query_params.clear()

# ─── Aba 2: Gerar cobranças em massa ─────────────────────────────────────────
with tab_massa:
    st.caption(
        "Cria cobranças **pendentes** para vários membros de uma vez. "
        "Membros que já têm registro no mês escolhido são pulados automaticamente."
    )

    mes_massa = st.selectbox(
        "Mês de referência",
        meses_opcoes,
        index=0,
        key="massa_mes",
    )

    # Calcula quem já tem registro no mês para destacar na lista.
    existentes_no_mes = {p.id_membro for p in pagamentos_repo.listar_por_mes(mes_massa)}

    opcoes_membros = [
        f"{m.nome} ({m.id_membro}) — {m.tipo}"
        + (" ✓ já lançado" if m.id_membro in existentes_no_mes else "")
        for m in membros
    ]
    ids_membros_ordem = [m.id_membro for m in membros]

    col_sel, col_btn = st.columns([4, 1])
    with col_btn:
        st.write("")  # alinhamento vertical
        selecionar_todos = st.button("Selecionar todos", key="massa_todos")

    default_sel = opcoes_membros if selecionar_todos else []
    membros_selecionados_labels = col_sel.multiselect(
        "Membros",
        options=opcoes_membros,
        default=default_sel,
        key="massa_membros",
        help="Membros marcados com ✓ já têm cobrança neste mês e serão pulados.",
    )

    ids_selecionados = [
        ids_membros_ordem[opcoes_membros.index(label)]
        for label in membros_selecionados_labels
    ]

    # Preview do que será criado.
    if ids_selecionados:
        novos = [i for i in ids_selecionados if i not in existentes_no_mes]
        pulados_prev = [i for i in ids_selecionados if i in existentes_no_mes]
        membros_por_id = {m.id_membro: m for m in membros}

        venc = calculo_dividas.calcular_data_vencimento(mes_massa, config.dia_vencimento)

        st.markdown(f"**{len(novos)} cobrança(s) serão criadas** / {len(pulados_prev)} já existem (serão puladas)")

        if novos:
            preview_rows = [
                {
                    "Membro": membros_por_id[i].nome,
                    "Tipo": membros_por_id[i].tipo,
                    "Valor": formatar_brl(config.valor_mensalidade(membros_por_id[i].tipo)),
                    "Vencimento": venc.strftime("%d/%m/%Y"),
                    "Status": "pendente",
                }
                for i in novos
                if i in membros_por_id
            ]
            st.dataframe(preview_rows, use_container_width=True, hide_index=True)

        if st.button(
            f"Confirmar — criar {len(novos)} cobrança(s)",
            type="primary",
            disabled=len(novos) == 0,
            key="massa_confirmar",
        ):
            with st.spinner("Criando cobranças..."):
                criados, pulados = calculo_dividas.gerar_pendencias_para_membros(
                    ids_selecionados, mes_massa
                )
            if criados:
                st.success(f"{criados} cobrança(s) criada(s) para **{mes_massa}**.")
            if pulados:
                st.info(f"{pulados} membro(s) pulado(s) — já tinham registro neste mês.")
    else:
        st.info("Selecione ao menos um membro para continuar.")
