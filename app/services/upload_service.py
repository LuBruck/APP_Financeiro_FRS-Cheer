"""Serviço de upload de comprovantes.

Traduz entidades de domínio (membro, mes_referencia, despesa...) em
chamadas ao `comprovantes_repo`, resolvendo nomes de pasta/arquivo conforme
as convenções do PRD (Seção 6.5).
"""

from __future__ import annotations

from app.models.membro import Membro
from app.repositories import comprovantes_repo
from app.repositories.comprovantes_repo import normalizar_nome


def _ano_from_mes(mes_referencia: str) -> int:
    """'2026-01' -> 2026."""
    try:
        return int(mes_referencia.split("-")[0])
    except (ValueError, IndexError) as e:
        raise ValueError(f"mes_referencia inválido: {mes_referencia!r}") from e


def _ano_from_data(data_iso: str) -> int:
    """'2026-03-15' -> 2026."""
    try:
        return int(data_iso.split("-")[0])
    except (ValueError, IndexError) as e:
        raise ValueError(f"data inválida: {data_iso!r}") from e


def upload_comprovante_despesa(
    *,
    categoria: str,
    data_iso: str,
    descricao: str,
    nome_arquivo_origem: str,
    conteudo: bytes,
) -> str:
    """Sobe comprovante de despesa e retorna a URL.

    Nome do arquivo: `{data}-{descricao-curta}.{ext}`
    Pasta: `{ano}/despesas/{categoria}/`
    """
    ext = nome_arquivo_origem.rsplit(".", 1)[-1].lower() if "." in nome_arquivo_origem else "pdf"
    descricao_curta = normalizar_nome(descricao)[:40]
    nome = f"{data_iso}-{descricao_curta}.{ext}"
    ano = _ano_from_data(data_iso)
    return comprovantes_repo.upload(
        tipo="despesas",
        ano=ano,
        subpasta=categoria,
        nome_arquivo=nome,
        conteudo=conteudo,
    )


def upload_comprovante_venda(
    *,
    comprador: str,
    produto: str,
    data_iso: str,
    nome_arquivo_origem: str,
    conteudo: bytes,
    sufixo: str = "",
) -> str:
    """Sobe comprovante de venda e retorna a URL.

    Pasta: `{ano}/vendas/{comprador-normalizado}/`
    Nome: `{data}-{produto-slug}[-sufixo].{ext}`. Use `sufixo` para diferenciar
    múltiplos comprovantes (parcelas) da mesma venda.
    """
    ext = nome_arquivo_origem.rsplit(".", 1)[-1].lower() if "." in nome_arquivo_origem else "pdf"
    comprador_slug = normalizar_nome(comprador)[:40] or "sem-comprador"
    produto_slug = normalizar_nome(produto)[:40] or "produto"
    sufixo_str = f"-{normalizar_nome(sufixo)}" if sufixo else ""
    nome = f"{data_iso}-{produto_slug}{sufixo_str}.{ext}"
    ano = _ano_from_data(data_iso)
    return comprovantes_repo.upload(
        tipo="vendas",
        ano=ano,
        subpasta=comprador_slug,
        nome_arquivo=nome,
        conteudo=conteudo,
    )


def upload_comprovante_mensalidade(
    *,
    membro: Membro,
    mes_referencia: str,
    nome_arquivo_origem: str,
    conteudo: bytes,
    sufixo: str = "",
) -> str:
    """Sobe comprovante de mensalidade e retorna a URL.

    Nome do arquivo: `{mes_referencia}.pdf` ou `{mes_referencia}-part{N}.pdf`
    quando houver múltiplos uploads no mesmo mês.
    """
    ext = nome_arquivo_origem.rsplit(".", 1)[-1].lower() if "." in nome_arquivo_origem else "pdf"
    nome = f"{mes_referencia}{('-' + sufixo) if sufixo else ''}.{ext}"
    subpasta = f"{membro.id_membro}-{normalizar_nome(membro.nome)}"
    return comprovantes_repo.upload(
        tipo="mensalidades",
        ano=_ano_from_mes(mes_referencia),
        subpasta=subpasta,
        nome_arquivo=nome,
        conteudo=conteudo,
    )
