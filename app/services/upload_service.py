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
