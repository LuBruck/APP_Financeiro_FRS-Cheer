"""Agregações para o Dashboard (PRD 7.1).

Todas as funções recebem listas puras de domínio e retornam dataclasses.
Nenhuma chamada ao Google aqui — a camada de pages/repositories já fez isso.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from app.models.despesa import Despesa
from app.models.pagamento import Pagamento
from app.models.venda import Venda


# ─────────────────────────── Tipos de saída ──────────────────────────

@dataclass(frozen=True, slots=True)
class KPIsDashboard:
    caixa_mes: float               # receitas + vendas − despesas do mês
    inadimplencia_total: float     # saldo devedor de todas as cobranças pendentes/parciais
    vencimentos_7d_count: int      # cobranças que vencem nos próximos 7 dias
    vencimentos_7d_valor: float    # valor total dessas cobranças
    saldo_ano: float               # caixa acumulado do ano corrente


@dataclass(frozen=True, slots=True)
class ResumoMes:
    mes: str           # 'YYYY-MM'
    receitas: float    # valor pago recebido (pagamentos)
    vendas: float      # total de vendas
    despesas: float    # total de despesas
    caixa: float       # receitas + vendas − despesas


@dataclass(frozen=True, slots=True)
class Transacao:
    data: str       # 'YYYY-MM-DD'
    tipo: str       # 'Receita', 'Venda', 'Despesa'
    descricao: str
    valor: float    # sempre positivo
    entrada: bool   # True = entra no caixa


# ──────────────────────── Helpers internos ───────────────────────────

def _mes_str(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def _ultimos_n_meses(n: int, referencia: date | None = None) -> list[str]:
    """Retorna lista de strings 'YYYY-MM' dos últimos n meses (mais antigo → mais recente)."""
    ref = referencia or date.today()
    meses: list[str] = []
    ano, mes = ref.year, ref.month
    for _ in range(n):
        meses.append(f"{ano:04d}-{mes:02d}")
        mes -= 1
        if mes == 0:
            mes = 12
            ano -= 1
    return list(reversed(meses))


def _pagamentos_do_mes(pagamentos: list[Pagamento], mes: str) -> list[Pagamento]:
    return [p for p in pagamentos if p.mes_referencia == mes and p.status in {"pago", "parcial"}]


def _despesas_do_mes(despesas: list[Despesa], mes: str) -> list[Despesa]:
    return [d for d in despesas if d.data.startswith(mes)]


def _vendas_do_mes(vendas: list[Venda], mes: str) -> list[Venda]:
    return [v for v in vendas if v.data.startswith(mes)]


def _despesas_do_ano(despesas: list[Despesa], ano: int) -> list[Despesa]:
    return [d for d in despesas if d.data.startswith(str(ano))]


def _vendas_do_ano(vendas: list[Venda], ano: int) -> list[Venda]:
    return [v for v in vendas if v.data.startswith(str(ano))]


# ─────────────────────────── API pública ─────────────────────────────

def calcular_kpis(
    *,
    pagamentos: list[Pagamento],
    despesas: list[Despesa],
    vendas: list[Venda],
    mes_referencia: str,
    hoje: date | None = None,
) -> KPIsDashboard:
    """Calcula os 5 KPIs principais do Dashboard para o mês fornecido."""
    hoje = hoje or date.today()
    ano = int(mes_referencia.split("-")[0])

    # Caixa do mês
    rec_mes = sum(p.valor_pago for p in _pagamentos_do_mes(pagamentos, mes_referencia))
    desp_mes = sum(d.valor for d in _despesas_do_mes(despesas, mes_referencia))
    vend_mes = sum(v.valor_total for v in _vendas_do_mes(vendas, mes_referencia))
    caixa_mes = round(rec_mes + vend_mes - desp_mes, 2)

    # Inadimplência total (todos os meses, não só o selecionado)
    inadimplencia = round(
        sum(p.saldo_devedor for p in pagamentos if p.status in {"pendente", "parcial"}), 2
    )

    # Vencimentos nos próximos 7 dias (cobranças pendentes/parciais)
    limite_7d = hoje + timedelta(days=7)
    venc_7d = [
        p for p in pagamentos
        if p.status in {"pendente", "parcial"}
        and p.data_vencimento
        and hoje <= date.fromisoformat(p.data_vencimento) <= limite_7d
    ]
    venc_7d_count = len(venc_7d)
    venc_7d_valor = round(sum(p.saldo_devedor for p in venc_7d), 2)

    # Saldo acumulado do ano
    rec_ano = sum(
        p.valor_pago
        for p in pagamentos
        if p.mes_referencia.startswith(str(ano)) and p.status in {"pago", "parcial"}
    )
    desp_ano = sum(d.valor for d in _despesas_do_ano(despesas, ano))
    vend_ano = sum(v.valor_total for v in _vendas_do_ano(vendas, ano))
    saldo_ano = round(rec_ano + vend_ano - desp_ano, 2)

    return KPIsDashboard(
        caixa_mes=caixa_mes,
        inadimplencia_total=inadimplencia,
        vencimentos_7d_count=venc_7d_count,
        vencimentos_7d_valor=venc_7d_valor,
        saldo_ano=saldo_ano,
    )


def evolucao_caixa(
    *,
    pagamentos: list[Pagamento],
    despesas: list[Despesa],
    vendas: list[Venda],
    n_meses: int = 6,
    referencia: date | None = None,
) -> list[ResumoMes]:
    """Retorna caixa mês a mês para os últimos n_meses."""
    meses = _ultimos_n_meses(n_meses, referencia)
    resultado: list[ResumoMes] = []
    for mes in meses:
        rec = round(sum(p.valor_pago for p in _pagamentos_do_mes(pagamentos, mes)), 2)
        desp = round(sum(d.valor for d in _despesas_do_mes(despesas, mes)), 2)
        vend = round(sum(v.valor_total for v in _vendas_do_mes(vendas, mes)), 2)
        resultado.append(
            ResumoMes(mes=mes, receitas=rec, vendas=vend, despesas=desp, caixa=round(rec + vend - desp, 2))
        )
    return resultado


def distribuicao_despesas_mes(
    *,
    despesas: list[Despesa],
    mes: str,
) -> dict[str, float]:
    """Retorna dict {categoria: total} para o mês, somente categorias com valor > 0."""
    result: dict[str, float] = {}
    for d in _despesas_do_mes(despesas, mes):
        result[d.categoria] = round(result.get(d.categoria, 0.0) + d.valor, 2)
    return {k: v for k, v in result.items() if v > 0}


def ultimas_transacoes(
    *,
    pagamentos: list[Pagamento],
    despesas: list[Despesa],
    vendas: list[Venda],
    n: int = 10,
    membros_por_id: dict[str, str] | None = None,
) -> list[Transacao]:
    """Retorna as n transações mais recentes (receitas + despesas + vendas)."""
    transacoes: list[Transacao] = []

    for p in pagamentos:
        if p.status not in {"pago", "parcial"} or not p.data_pagamento:
            continue
        nome = (membros_por_id or {}).get(p.id_membro, p.id_membro)
        transacoes.append(
            Transacao(
                data=p.data_pagamento,
                tipo="Receita",
                descricao=f"Mensalidade {p.mes_referencia} — {nome}",
                valor=p.valor_pago,
                entrada=True,
            )
        )

    for d in despesas:
        transacoes.append(
            Transacao(
                data=d.data,
                tipo="Despesa",
                descricao=d.descricao,
                valor=d.valor,
                entrada=False,
            )
        )

    for v in vendas:
        transacoes.append(
            Transacao(
                data=v.data,
                tipo="Venda",
                descricao=f"{v.produto} × {v.quantidade}",
                valor=v.valor_total,
                entrada=True,
            )
        )

    transacoes.sort(key=lambda t: t.data, reverse=True)
    return transacoes[:n]


def alertas(
    *,
    pagamentos: list[Pagamento],
    n_membros_ativos: int,
    hoje: date | None = None,
) -> list[str]:
    """Retorna lista de textos de alerta para exibição no Dashboard."""
    hoje = hoje or date.today()
    msgs: list[str] = []

    pendentes = [p for p in pagamentos if p.status in {"pendente", "parcial"}]
    if n_membros_ativos > 0 and pendentes:
        pct = len({p.id_membro for p in pendentes}) / n_membros_ativos * 100
        if pct >= 30:
            msgs.append(
                f"{pct:.0f}% dos membros ativos têm cobranças em aberto."
            )

    sem_comprovante = [
        p for p in pagamentos
        if p.status in {"pago", "parcial"} and not p.link_comprovante
    ]
    if sem_comprovante:
        msgs.append(
            f"{len(sem_comprovante)} pagamento(s) sem comprovante anexado."
        )

    return msgs


__all__ = [
    "KPIsDashboard",
    "ResumoMes",
    "Transacao",
    "calcular_kpis",
    "evolucao_caixa",
    "distribuicao_despesas_mes",
    "ultimas_transacoes",
    "alertas",
]
