"""Acesso à aba `configuracoes` (chave/valor)."""

from __future__ import annotations

import streamlit as st

from app.config import SHEET_CONFIGURACOES
from app.models.configuracao import Configuracoes
from app.repositories.base import read_all_records


def _as_float(v: object, default: float) -> float:
    if v is None or v == "":
        return default
    try:
        return float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return default


def _as_int(v: object, default: int) -> int:
    try:
        return int(float(str(v)))
    except (TypeError, ValueError):
        return default


@st.cache_data(ttl=300, show_spinner=False)
def carregar() -> Configuracoes:
    """Lê toda a aba `configuracoes` e retorna um snapshot tipado."""
    rows = read_all_records(SHEET_CONFIGURACOES, only_ativo=False)
    kv: dict[str, str] = {
        str(r.get("chave", "")).strip(): str(r.get("valor", "")).strip() for r in rows
    }
    defaults = Configuracoes()
    return Configuracoes(
        valor_mensalidade_atleta=_as_float(
            kv.get("valor_mensalidade_atleta"), defaults.valor_mensalidade_atleta
        ),
        valor_mensalidade_associado=_as_float(
            kv.get("valor_mensalidade_associado"), defaults.valor_mensalidade_associado
        ),
        valor_multa_atraso=_as_float(
            kv.get("valor_multa_atraso"), defaults.valor_multa_atraso
        ),
        dia_vencimento=_as_int(kv.get("dia_vencimento"), defaults.dia_vencimento),
        nome_time=kv.get("nome_time") or defaults.nome_time,
    )
