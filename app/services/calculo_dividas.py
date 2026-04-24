"""Regras de negócio de cobrança e pagamento.

Responsabilidades:
    - Geração lazy de linhas pendentes do mês corrente (PRD 6.3).
    - Cálculo de data de vencimento, multa por atraso e status.
    - Orquestração do registro de pagamento (parcial/total) + upload opcional.

Todas as funções recebem dependências puras (membros, pagamentos, configs)
e retornam dados; a UI chama estas funções, não os repositórios diretamente.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, timedelta

import streamlit as st

from app.models.configuracao import Configuracoes
from app.models.membro import Membro
from app.models.pagamento import Pagamento, StatusPagamento
from app.repositories import (
    configuracoes_repo,
    membros_repo,
    pagamentos_repo,
)
from app.repositories.base import clear_reads_cache
from app.services import upload_service
from app.utils.formatters import data_iso, mes_referencia as fmt_mes_ref

logger = logging.getLogger(__name__)


# ---------- Utilitários de data / status ----------

def calcular_data_vencimento(mes_referencia: str, dia_vencimento: int) -> date:
    """Dia `dia_vencimento` do mês **seguinte** ao mes_referencia.

    Ex.: mes_referencia='2026-01', dia=10 -> 2026-02-10.
    """
    ano, mes = (int(x) for x in mes_referencia.split("-"))
    mes_seguinte = mes + 1
    ano_seguinte = ano
    if mes_seguinte > 12:
        mes_seguinte = 1
        ano_seguinte = ano + 1
    # Clamp do dia (28 para fevereiro, etc).
    ultimo_dia = (date(ano_seguinte, mes_seguinte % 12 + 1, 1) if mes_seguinte < 12
                  else date(ano_seguinte + 1, 1, 1)) - timedelta(days=1)
    dia = min(dia_vencimento, ultimo_dia.day)
    return date(ano_seguinte, mes_seguinte, dia)


def esta_em_atraso(data_vencimento: str | date, hoje: date | None = None) -> bool:
    if isinstance(data_vencimento, str):
        data_vencimento = date.fromisoformat(data_vencimento)
    hoje = hoje or date.today()
    return hoje > data_vencimento


def dias_em_atraso(data_vencimento: str | date, hoje: date | None = None) -> int:
    if isinstance(data_vencimento, str):
        data_vencimento = date.fromisoformat(data_vencimento)
    hoje = hoje or date.today()
    delta = (hoje - data_vencimento).days
    return max(delta, 0)


def calcular_status(valor_original: float, multa: float, valor_pago: float) -> StatusPagamento:
    total = valor_original + multa
    if valor_pago <= 0:
        return "pendente"
    if valor_pago >= total:
        return "pago"
    return "parcial"


# ---------- Geração lazy de cobranças ----------

def _build_linha_pendente(
    membro: Membro, mes_ref: str, config: Configuracoes
) -> dict:
    venc = calcular_data_vencimento(mes_ref, config.dia_vencimento)
    return {
        "id_membro": membro.id_membro,
        "mes_referencia": mes_ref,
        "data_vencimento": venc.isoformat(),
        "data_pagamento": "",
        "valor_original": config.valor_mensalidade(membro.tipo),
        "multa": 0,
        "valor_pago": 0,
        "status": "pendente",
        "link_comprovante": "",
        "observacoes": "",
    }


def gerar_pendencias_do_mes(mes_ref: str | None = None) -> int:
    """Cria linhas `pendente` para membros ativos sem pagamento no mês.

    Retorna quantas linhas foram criadas. Idempotente.
    """
    mes_ref = mes_ref or fmt_mes_ref()
    config = configuracoes_repo.carregar()
    membros = membros_repo.listar_todos(incluir_inativos=False)
    existentes = {p.id_membro for p in pagamentos_repo.listar_por_mes(mes_ref)}

    novas = [
        _build_linha_pendente(m, mes_ref, config)
        for m in membros
        if m.id_membro and m.id_membro not in existentes
    ]
    if not novas:
        return 0

    pagamentos_repo.criar_varios(novas)
    clear_reads_cache()
    logger.info("geração lazy: %d pendência(s) criada(s) para %s", len(novas), mes_ref)
    return len(novas)


def garantir_pendencias_sessao(mes_ref: str | None = None) -> None:
    """Chama `gerar_pendencias_do_mes` uma vez por sessão por mês (flag em session_state)."""
    mes_ref = mes_ref or fmt_mes_ref()
    flag = f"cobrancas_checked_{mes_ref}"
    if st.session_state.get(flag):
        return
    try:
        gerar_pendencias_do_mes(mes_ref)
    finally:
        st.session_state[flag] = True


# ---------- Registro de pagamento ----------

@dataclass(frozen=True, slots=True)
class ResultadoPagamento:
    id_pagamento: str
    status: StatusPagamento
    valor_pago_total: float
    saldo_restante: float
    link_comprovante: str


def _sugerir_multa(pagamento: Pagamento, hoje: date, config: Configuracoes) -> float:
    """Sugere multa quando em atraso (somente se ainda não houve multa aplicada)."""
    if pagamento.multa > 0:
        return pagamento.multa
    if esta_em_atraso(pagamento.data_vencimento, hoje):
        return config.valor_multa_atraso
    return 0.0


def sugerir_multa(pagamento: Pagamento, hoje: date | None = None) -> float:
    """Versão pública: útil para a UI pré-marcar o checkbox de multa."""
    return _sugerir_multa(pagamento, hoje or date.today(), configuracoes_repo.carregar())


def registrar_pagamento(
    *,
    id_pagamento: str,
    valor_pago_agora: float,
    data_pagamento: date,
    aplicar_multa: bool,
    observacoes: str,
    comprovante_bytes: bytes | None = None,
    comprovante_filename: str | None = None,
) -> ResultadoPagamento:
    """Registra pagamento (total ou parcial) em uma cobrança existente.

    - Soma `valor_pago_agora` ao `valor_pago` atual (mesma linha; ver PRD 10.3).
    - Aplica multa somente se `aplicar_multa=True` e ainda não houver multa.
    - Sobe o comprovante (se enviado) e grava o link.
    - Atualiza `status` e `data_pagamento`.
    - Exige observação quando o resultado for parcial.
    """
    if valor_pago_agora <= 0:
        raise ValueError("O valor pago deve ser maior que zero.")

    pagamento = pagamentos_repo.get_by_id(id_pagamento)
    if pagamento is None:
        raise LookupError(f"Pagamento {id_pagamento} não encontrado.")
    if pagamento.status == "cancelado":
        raise ValueError("Pagamento cancelado não pode receber valores.")

    config = configuracoes_repo.carregar()
    multa = config.valor_multa_atraso if (aplicar_multa and pagamento.multa == 0) else pagamento.multa
    valor_pago_total = round(pagamento.valor_pago + valor_pago_agora, 2)
    valor_total_devido = round(pagamento.valor_original + multa, 2)
    novo_status = calcular_status(pagamento.valor_original, multa, valor_pago_total)
    saldo = round(max(valor_total_devido - valor_pago_total, 0.0), 2)

    if novo_status == "parcial" and not observacoes.strip():
        raise ValueError("Observação é obrigatória para pagamento parcial.")

    link = pagamento.link_comprovante
    if comprovante_bytes and comprovante_filename:
        membro = membros_repo.get_by_id(pagamento.id_membro)
        if membro is None:
            raise LookupError(
                f"Membro {pagamento.id_membro} não encontrado ao subir comprovante."
            )
        # Sufixo evita colidir com comprovante anterior (parcial + complemento).
        sufixo = "part2" if pagamento.link_comprovante else ""
        link = upload_service.upload_comprovante_mensalidade(
            membro=membro,
            mes_referencia=pagamento.mes_referencia,
            nome_arquivo_origem=comprovante_filename,
            conteudo=comprovante_bytes,
            sufixo=sufixo,
        )

    updates = {
        "multa": multa,
        "valor_pago": valor_pago_total,
        "status": novo_status,
        "data_pagamento": data_iso(data_pagamento),
        "link_comprovante": link,
    }
    if observacoes.strip():
        updates["observacoes"] = observacoes.strip()

    pagamentos_repo.atualizar(id_pagamento, updates)
    clear_reads_cache()
    logger.info(
        "pagamento registrado: id=%s status=%s valor_pago=%.2f saldo=%.2f",
        id_pagamento, novo_status, valor_pago_total, saldo,
    )
    return ResultadoPagamento(
        id_pagamento=id_pagamento,
        status=novo_status,
        valor_pago_total=valor_pago_total,
        saldo_restante=saldo,
        link_comprovante=link,
    )


__all__ = [
    "ResultadoPagamento",
    "calcular_data_vencimento",
    "calcular_status",
    "dias_em_atraso",
    "esta_em_atraso",
    "garantir_pendencias_sessao",
    "gerar_pendencias_do_mes",
    "registrar_pagamento",
    "sugerir_multa",
]
