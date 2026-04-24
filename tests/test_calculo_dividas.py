"""Testes das regras puras de calculo_dividas (sem tocar em Google)."""

from __future__ import annotations

import sys
import types
from datetime import date
from unittest.mock import MagicMock


def _stub_streamlit() -> None:
    """Stub do módulo `streamlit` para permitir import sem rodar o app."""
    if "streamlit" in sys.modules:
        return
    st = types.ModuleType("streamlit")
    st.session_state = {}  # type: ignore[attr-defined]
    st.secrets = {}  # type: ignore[attr-defined]
    st.user = types.SimpleNamespace(email="teste@exemplo.com", is_logged_in=True)  # type: ignore[attr-defined]

    def _cache_data(*_a, **_kw):
        def deco(fn):
            return fn
        if _a and callable(_a[0]) and not _kw:
            return _a[0]
        return deco

    st.cache_data = _cache_data  # type: ignore[attr-defined]
    st.cache_data.clear = lambda: None  # type: ignore[attr-defined]
    sys.modules["streamlit"] = st


_stub_streamlit()

from app.services import calculo_dividas  # noqa: E402


def test_calcular_data_vencimento_mes_normal():
    assert calculo_dividas.calcular_data_vencimento("2026-01", 10) == date(2026, 2, 10)


def test_calcular_data_vencimento_virada_de_ano():
    assert calculo_dividas.calcular_data_vencimento("2026-12", 10) == date(2027, 1, 10)


def test_calcular_data_vencimento_clamp_fevereiro():
    assert calculo_dividas.calcular_data_vencimento("2026-01", 31) == date(2026, 2, 28)


def test_calcular_status_pendente():
    assert calculo_dividas.calcular_status(55.0, 0.0, 0.0) == "pendente"


def test_calcular_status_parcial():
    assert calculo_dividas.calcular_status(55.0, 7.0, 30.0) == "parcial"


def test_calcular_status_pago_exato():
    assert calculo_dividas.calcular_status(55.0, 7.0, 62.0) == "pago"


def test_calcular_status_pago_com_excedente():
    assert calculo_dividas.calcular_status(55.0, 0.0, 70.0) == "pago"


def test_dias_em_atraso():
    assert calculo_dividas.dias_em_atraso("2026-04-10", hoje=date(2026, 4, 20)) == 10
    assert calculo_dividas.dias_em_atraso("2026-04-10", hoje=date(2026, 4, 1)) == 0


def test_esta_em_atraso():
    assert calculo_dividas.esta_em_atraso("2026-04-10", hoje=date(2026, 4, 15)) is True
    assert calculo_dividas.esta_em_atraso("2026-04-10", hoje=date(2026, 4, 10)) is False


def test_registrar_pagamento_exige_observacao_no_parcial(monkeypatch):
    from app.models.configuracao import Configuracoes
    from app.models.pagamento import Pagamento

    pag = Pagamento(
        id_pagamento="p1",
        id_membro="M001",
        mes_referencia="2026-04",
        data_vencimento="2026-05-10",
        valor_original=55.0,
    )

    monkeypatch.setattr(calculo_dividas.pagamentos_repo, "get_by_id", lambda _id: pag)
    monkeypatch.setattr(calculo_dividas.configuracoes_repo, "carregar", lambda: Configuracoes())
    atualizar_mock = MagicMock()
    monkeypatch.setattr(calculo_dividas.pagamentos_repo, "atualizar", atualizar_mock)
    monkeypatch.setattr(calculo_dividas, "clear_reads_cache", lambda: None)

    import pytest
    with pytest.raises(ValueError, match="parcial"):
        calculo_dividas.registrar_pagamento(
            id_pagamento="p1",
            valor_pago_agora=20.0,
            data_pagamento=date(2026, 5, 1),
            aplicar_multa=False,
            observacoes="",
        )
    atualizar_mock.assert_not_called()


def test_registrar_pagamento_total_aplica_multa(monkeypatch):
    from app.models.configuracao import Configuracoes
    from app.models.pagamento import Pagamento

    pag = Pagamento(
        id_pagamento="p1",
        id_membro="M001",
        mes_referencia="2026-03",
        data_vencimento="2026-04-10",
        valor_original=55.0,
    )
    config = Configuracoes(valor_multa_atraso=7.0)

    monkeypatch.setattr(calculo_dividas.pagamentos_repo, "get_by_id", lambda _id: pag)
    monkeypatch.setattr(calculo_dividas.configuracoes_repo, "carregar", lambda: config)
    monkeypatch.setattr(calculo_dividas, "clear_reads_cache", lambda: None)
    updates_capturados: dict = {}

    def fake_atualizar(_id, updates):
        updates_capturados.update(updates)

    monkeypatch.setattr(calculo_dividas.pagamentos_repo, "atualizar", fake_atualizar)

    resultado = calculo_dividas.registrar_pagamento(
        id_pagamento="p1",
        valor_pago_agora=62.0,
        data_pagamento=date(2026, 4, 20),
        aplicar_multa=True,
        observacoes="",
    )

    assert resultado.status == "pago"
    assert resultado.valor_pago_total == 62.0
    assert resultado.saldo_restante == 0.0
    assert updates_capturados["multa"] == 7.0
    assert updates_capturados["status"] == "pago"
    assert updates_capturados["data_pagamento"] == "2026-04-20"
