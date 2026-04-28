from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

TipoMembro = Literal["atleta", "associado"]
StatusMembro = Literal["ativo", "inativo"]


@dataclass(frozen=True, slots=True)
class Membro:
    id_membro: str
    nome: str
    tipo: TipoMembro
    email: str = ""
    telefone: str = ""
    semestre_entrada: str = ""
    status: StatusMembro = "ativo"
    observacoes: str = ""

    @classmethod
    def from_row(cls, row: dict[str, str]) -> "Membro":
        """Cria a partir de uma linha do Sheets (dict coluna→valor string)."""
        return cls(
            id_membro=row.get("id_membro", "").strip(),
            nome=row.get("nome", "").strip(),
            tipo=row.get("tipo", "atleta").strip() or "atleta",  # type: ignore[arg-type]
            email=row.get("email", "").strip(),
            telefone=str(row.get("telefone", "") or "").strip(),
            semestre_entrada=row.get("semestre_entrada", "").strip(),
            status=row.get("status", "ativo").strip() or "ativo",  # type: ignore[arg-type]
            observacoes=row.get("observacoes", "").strip(),
        )
