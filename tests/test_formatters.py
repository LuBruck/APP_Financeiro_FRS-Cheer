from __future__ import annotations

from datetime import date

from app.utils.formatters import (
    data_iso,
    formatar_brl,
    formatar_data_br,
    mes_referencia,
    parse_brl,
)


class TestFormatarBRL:
    def test_valor_inteiro(self):
        assert formatar_brl(55) == "R$ 55,00"

    def test_valor_float(self):
        assert formatar_brl(1234.56) == "R$ 1.234,56"

    def test_valor_grande(self):
        assert formatar_brl(1234567.89) == "R$ 1.234.567,89"

    def test_none(self):
        assert formatar_brl(None) == "R$ 0,00"

    def test_string_invalida(self):
        assert formatar_brl("abc") == "R$ 0,00"


class TestParseBRL:
    def test_com_prefixo(self):
        assert parse_brl("R$ 1.234,56") == 1234.56

    def test_sem_prefixo(self):
        assert parse_brl("55,00") == 55.0


class TestDatas:
    def test_formatar_data_br(self):
        assert formatar_data_br(date(2026, 1, 15)) == "15/01/2026"

    def test_formatar_data_iso_string(self):
        assert formatar_data_br("2026-01-15") == "15/01/2026"

    def test_formatar_data_vazia(self):
        assert formatar_data_br(None) == ""
        assert formatar_data_br("") == ""

    def test_data_iso(self):
        assert data_iso(date(2026, 1, 15)) == "2026-01-15"

    def test_mes_referencia(self):
        assert mes_referencia(date(2026, 1, 15)) == "2026-01"
