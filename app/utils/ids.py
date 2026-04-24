"""Geração de IDs sequenciais legíveis para as entidades do sistema.

Padrão: prefixo + número zero-padded (ex: M001, D0001, PAG0001).
Estratégia: lê os IDs existentes, extrai o maior número e incrementa.
Para o volume previsto (~30 membros, ~50 transações/mês) colisões são
impossíveis na prática — nunca há dois usuários escrevendo ao mesmo tempo.
"""

from __future__ import annotations

import re


def proximo_id(prefixo: str, ids_existentes: list[str], digitos: int = 4) -> str:
    """Retorna o próximo ID sequencial dado os existentes.

    Exemplos:
        proximo_id("M", ["M001", "M003"], digitos=3) -> "M004"
        proximo_id("D", [], digitos=4)               -> "D0001"
    """
    pattern = re.compile(rf"^{re.escape(prefixo)}(\d+)$")
    numeros = [int(m.group(1)) for id_ in ids_existentes if (m := pattern.match(id_))]
    n = max(numeros, default=0) + 1
    return f"{prefixo}{n:0{digitos}d}"


def proximos_ids(prefixo: str, ids_existentes: list[str], quantidade: int, digitos: int = 4) -> list[str]:
    """Retorna `quantidade` IDs sequenciais a partir do próximo disponível."""
    pattern = re.compile(rf"^{re.escape(prefixo)}(\d+)$")
    numeros = [int(m.group(1)) for id_ in ids_existentes if (m := pattern.match(id_))]
    inicio = max(numeros, default=0) + 1
    return [f"{prefixo}{i:0{digitos}d}" for i in range(inicio, inicio + quantidade)]
