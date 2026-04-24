"""Testes puros do repositório de comprovantes (apenas funções sem IO)."""

from __future__ import annotations

import sys
import types


def _stub_streamlit() -> None:
    if "streamlit" in sys.modules:
        return
    st = types.ModuleType("streamlit")
    st.secrets = {}  # type: ignore[attr-defined]
    sys.modules["streamlit"] = st


_stub_streamlit()

from app.repositories.comprovantes_repo import normalizar_nome  # noqa: E402


def test_normalizar_nome_remove_acentos_e_caixa():
    assert normalizar_nome("João Silva") == "joao-silva"


def test_normalizar_nome_caracteres_especiais():
    assert normalizar_nome("Maria D'Ávila!") == "maria-d-avila"


def test_normalizar_nome_espacos_e_hifens():
    assert normalizar_nome("  Pedro  --  Souza  ") == "pedro-souza"


def test_normalizar_nome_vazio():
    assert normalizar_nome("   ") == "sem-nome"
