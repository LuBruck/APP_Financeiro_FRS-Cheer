"""Testes para services/dashboard_service.py.

Todas as funções são puras (sem I/O), então não precisam de mock.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.models.despesa import Despesa
from app.models.pagamento import Pagamento
from app.models.venda import Venda
from app.services import dashboard_service as ds


# ─── Fixtures ────────────────────────────────────────────────────────

def _pagamento(
    id: str = "p1",
    id_membro: str = "M001",
    mes: str = "2026-04",
    valor_original: float = 55.0,
    multa: float = 0.0,
    valor_pago: float = 0.0,
    status: str = "pendente",
    data_pagamento: str = "",
    data_vencimento: str = "2026-05-10",
    link_comprovante: str = "",
) -> Pagamento:
    return Pagamento(
        id_pagamento=id,
        id_membro=id_membro,
        mes_referencia=mes,
        data_vencimento=data_vencimento,
        valor_original=valor_original,
        multa=multa,
        valor_pago=valor_pago,
        status=status,  # type: ignore[arg-type]
        data_pagamento=data_pagamento,
        link_comprovante=link_comprovante,
    )


def _despesa(
    id: str = "d1",
    data: str = "2026-04-10",
    categoria: str = "coach",
    descricao: str = "Aula de coach",
    valor: float = 200.0,
) -> Despesa:
    return Despesa(
        id_despesa=id,
        data=data,
        categoria=categoria,  # type: ignore[arg-type]
        descricao=descricao,
        valor=valor,
    )


def _venda(
    id: str = "v1",
    data: str = "2026-04-15",
    produto: str = "Camiseta",
    quantidade: int = 2,
    valor_unitario: float = 50.0,
    valor_total: float = 100.0,
) -> Venda:
    return Venda(
        id_venda=id,
        data=data,
        produto=produto,
        quantidade=quantidade,
        valor_unitario=valor_unitario,
        valor_total=valor_total,
    )


# ─── calcular_kpis ───────────────────────────────────────────────────

class TestCalcularKpis:
    def test_tudo_vazio(self):
        kpis = ds.calcular_kpis(
            pagamentos=[], despesas=[], vendas=[], mes_referencia="2026-04"
        )
        assert kpis.caixa_mes == 0.0
        assert kpis.inadimplencia_total == 0.0
        assert kpis.vencimentos_7d_count == 0
        assert kpis.saldo_ano == 0.0

    def test_caixa_mes_receita_menos_despesa(self):
        pag = _pagamento(mes="2026-04", valor_pago=55.0, status="pago", data_pagamento="2026-04-05")
        desp = _despesa(data="2026-04-10", valor=20.0)
        kpis = ds.calcular_kpis(
            pagamentos=[pag], despesas=[desp], vendas=[], mes_referencia="2026-04"
        )
        assert kpis.caixa_mes == 35.0

    def test_caixa_mes_inclui_vendas(self):
        vend = _venda(data="2026-04-15", valor_total=100.0)
        kpis = ds.calcular_kpis(
            pagamentos=[], despesas=[], vendas=[vend], mes_referencia="2026-04"
        )
        assert kpis.caixa_mes == 100.0

    def test_caixa_mes_negativo(self):
        desp = _despesa(data="2026-04-01", valor=300.0)
        kpis = ds.calcular_kpis(
            pagamentos=[], despesas=[desp], vendas=[], mes_referencia="2026-04"
        )
        assert kpis.caixa_mes == -300.0

    def test_inadimplencia_soma_saldo_devedor(self):
        p1 = _pagamento(id="p1", valor_original=55.0, multa=0.0, valor_pago=0.0, status="pendente")
        p2 = _pagamento(id="p2", valor_original=55.0, multa=7.0, valor_pago=30.0, status="parcial")
        kpis = ds.calcular_kpis(
            pagamentos=[p1, p2], despesas=[], vendas=[], mes_referencia="2026-04"
        )
        assert kpis.inadimplencia_total == pytest.approx(55.0 + 32.0)

    def test_inadimplencia_ignora_pagos(self):
        pag = _pagamento(valor_original=55.0, valor_pago=55.0, status="pago")
        kpis = ds.calcular_kpis(
            pagamentos=[pag], despesas=[], vendas=[], mes_referencia="2026-04"
        )
        assert kpis.inadimplencia_total == 0.0

    def test_vencimentos_7d_detecta_dentro_do_prazo(self):
        hoje = date(2026, 5, 1)
        # vence em 2026-05-07 — dentro dos 7 dias
        pag = _pagamento(status="pendente", data_vencimento="2026-05-07", valor_original=55.0)
        kpis = ds.calcular_kpis(
            pagamentos=[pag], despesas=[], vendas=[], mes_referencia="2026-04", hoje=hoje
        )
        assert kpis.vencimentos_7d_count == 1
        assert kpis.vencimentos_7d_valor == 55.0

    def test_vencimentos_7d_ignora_fora_do_prazo(self):
        hoje = date(2026, 5, 1)
        # vence em 2026-05-20 — fora dos 7 dias
        pag = _pagamento(status="pendente", data_vencimento="2026-05-20")
        kpis = ds.calcular_kpis(
            pagamentos=[pag], despesas=[], vendas=[], mes_referencia="2026-04", hoje=hoje
        )
        assert kpis.vencimentos_7d_count == 0

    def test_saldo_ano_soma_receitas_vendas_menos_despesas(self):
        pag = _pagamento(
            mes="2026-03", valor_pago=55.0, status="pago", data_pagamento="2026-03-05"
        )
        desp = _despesa(data="2026-02-10", valor=100.0)
        vend = _venda(data="2026-01-20", valor_total=80.0)
        kpis = ds.calcular_kpis(
            pagamentos=[pag], despesas=[desp], vendas=[vend], mes_referencia="2026-04"
        )
        assert kpis.saldo_ano == pytest.approx(55.0 + 80.0 - 100.0)

    def test_saldo_ano_ignora_anos_anteriores(self):
        pag_ant = _pagamento(
            mes="2025-12", valor_pago=55.0, status="pago", data_pagamento="2025-12-10"
        )
        kpis = ds.calcular_kpis(
            pagamentos=[pag_ant], despesas=[], vendas=[], mes_referencia="2026-04"
        )
        assert kpis.saldo_ano == 0.0


# ─── evolucao_caixa ──────────────────────────────────────────────────

class TestEvolucaoCaixa:
    def test_retorna_n_meses(self):
        ev = ds.evolucao_caixa(pagamentos=[], despesas=[], vendas=[], n_meses=6)
        assert len(ev) == 6

    def test_ordem_cronologica(self):
        ev = ds.evolucao_caixa(
            pagamentos=[], despesas=[], vendas=[], n_meses=3,
            referencia=date(2026, 4, 1)
        )
        assert ev[0].mes == "2026-02"
        assert ev[1].mes == "2026-03"
        assert ev[2].mes == "2026-04"

    def test_caixa_correto_por_mes(self):
        pag = _pagamento(mes="2026-03", valor_pago=55.0, status="pago", data_pagamento="2026-03-05")
        desp = _despesa(data="2026-03-10", valor=20.0)
        ev = ds.evolucao_caixa(
            pagamentos=[pag], despesas=[desp], vendas=[], n_meses=3,
            referencia=date(2026, 4, 1)
        )
        mar = next(r for r in ev if r.mes == "2026-03")
        assert mar.receitas == 55.0
        assert mar.despesas == 20.0
        assert mar.caixa == 35.0

    def test_mes_sem_dados_e_zero(self):
        ev = ds.evolucao_caixa(
            pagamentos=[], despesas=[], vendas=[], n_meses=3,
            referencia=date(2026, 4, 1)
        )
        for r in ev:
            assert r.caixa == 0.0


# ─── distribuicao_despesas_mes ───────────────────────────────────────

class TestDistribuicaoDespesasMes:
    def test_vazio(self):
        assert ds.distribuicao_despesas_mes(despesas=[], mes="2026-04") == {}

    def test_agrupa_por_categoria(self):
        d1 = _despesa(id="d1", data="2026-04-01", categoria="coach", valor=200.0)
        d2 = _despesa(id="d2", data="2026-04-10", categoria="coach", valor=100.0)
        d3 = _despesa(id="d3", data="2026-04-15", categoria="uniforme", valor=50.0)
        dist = ds.distribuicao_despesas_mes(despesas=[d1, d2, d3], mes="2026-04")
        assert dist["coach"] == pytest.approx(300.0)
        assert dist["uniforme"] == pytest.approx(50.0)

    def test_ignora_outros_meses(self):
        d = _despesa(data="2026-03-10", valor=200.0)
        dist = ds.distribuicao_despesas_mes(despesas=[d], mes="2026-04")
        assert dist == {}


# ─── ultimas_transacoes ──────────────────────────────────────────────

class TestUltimasTransacoes:
    def test_vazio(self):
        assert ds.ultimas_transacoes(pagamentos=[], despesas=[], vendas=[], n=10) == []

    def test_limite_n(self):
        pagamentos = [
            _pagamento(id=f"p{i}", mes="2026-04", valor_pago=55.0, status="pago",
                       data_pagamento=f"2026-04-{i+1:02d}")
            for i in range(15)
        ]
        result = ds.ultimas_transacoes(pagamentos=pagamentos, despesas=[], vendas=[], n=5)
        assert len(result) == 5

    def test_ordem_mais_recente_primeiro(self):
        p1 = _pagamento(id="p1", mes="2026-02", valor_pago=55.0, status="pago",
                        data_pagamento="2026-02-05")
        p2 = _pagamento(id="p2", mes="2026-04", valor_pago=55.0, status="pago",
                        data_pagamento="2026-04-10")
        result = ds.ultimas_transacoes(pagamentos=[p1, p2], despesas=[], vendas=[], n=10)
        assert result[0].data == "2026-04-10"
        assert result[1].data == "2026-02-05"

    def test_despesa_e_entrada_false(self):
        d = _despesa(data="2026-04-10", valor=200.0)
        result = ds.ultimas_transacoes(pagamentos=[], despesas=[d], vendas=[], n=10)
        assert len(result) == 1
        assert result[0].tipo == "Despesa"
        assert result[0].entrada is False

    def test_venda_e_entrada_true(self):
        v = _venda(data="2026-04-15", valor_total=100.0)
        result = ds.ultimas_transacoes(pagamentos=[], despesas=[], vendas=[v], n=10)
        assert len(result) == 1
        assert result[0].tipo == "Venda"
        assert result[0].entrada is True

    def test_pagamento_pendente_nao_aparece(self):
        pag = _pagamento(status="pendente", valor_pago=0.0)
        result = ds.ultimas_transacoes(pagamentos=[pag], despesas=[], vendas=[], n=10)
        assert result == []

    def test_usa_nome_do_membro(self):
        pag = _pagamento(id_membro="M001", status="pago", valor_pago=55.0,
                         data_pagamento="2026-04-05")
        result = ds.ultimas_transacoes(
            pagamentos=[pag], despesas=[], vendas=[], n=10,
            membros_por_id={"M001": "João Silva"}
        )
        assert "João Silva" in result[0].descricao


# ─── alertas ─────────────────────────────────────────────────────────

class TestAlertas:
    def test_sem_dados_sem_alertas(self):
        assert ds.alertas(pagamentos=[], n_membros_ativos=10) == []

    def test_alerta_inadimplencia_alta(self):
        # 4 membros distintos inadimplentes de 10 = 40% → deve alertar (≥30%)
        pagamentos = [
            _pagamento(id=f"p{i}", id_membro=f"M{i:03d}", status="pendente")
            for i in range(4)
        ]
        msgs = ds.alertas(pagamentos=pagamentos, n_membros_ativos=10)
        assert any("%" in m for m in msgs)

    def test_sem_alerta_inadimplencia_baixa(self):
        # 2 membros de 10 = 20% → abaixo do limiar de 30%
        pagamentos = [
            _pagamento(id=f"p{i}", id_membro=f"M{i:03d}", status="pendente")
            for i in range(2)
        ]
        msgs = ds.alertas(pagamentos=pagamentos, n_membros_ativos=10)
        assert not any("%" in m for m in msgs)

    def test_alerta_sem_comprovante(self):
        pag = _pagamento(status="pago", valor_pago=55.0, link_comprovante="")
        msgs = ds.alertas(pagamentos=[pag], n_membros_ativos=10)
        assert any("comprovante" in m.lower() for m in msgs)

    def test_sem_alerta_com_comprovante(self):
        pag = _pagamento(status="pago", valor_pago=55.0,
                         link_comprovante="https://drive.google.com/file/abc")
        msgs = ds.alertas(pagamentos=[pag], n_membros_ativos=10)
        assert not any("comprovante" in m.lower() for m in msgs)
