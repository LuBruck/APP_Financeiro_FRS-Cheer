"""Upload de comprovantes para o Google Drive.

Estrutura da pasta raiz (PRD 6.5):

    Financeiro-Furiosos-Cheer/
    └── {ano}/
        ├── mensalidades/
        │   └── {id_membro}-{nome-normalizado}/
        │       └── {YYYY-MM}.pdf
        ├── despesas/{categoria}/
        ├── eventos/{nome-evento}-{ano}/
        └── vendas/{produto-normalizado}/
"""

from __future__ import annotations

import io
import logging
import re
import unicodedata
from typing import Literal

from googleapiclient.http import MediaIoBaseUpload

from app.config import get_drive_folder_id, get_drive_service

logger = logging.getLogger(__name__)

TipoComprovante = Literal["mensalidades", "despesas", "eventos", "vendas"]

MIMETYPES = {
    "pdf": "application/pdf",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
}

FOLDER_MIME = "application/vnd.google-apps.folder"


def normalizar_nome(texto: str) -> str:
    """'João Silva' -> 'joao-silva'. Remove acentos, lower, hífens."""
    nfkd = unicodedata.normalize("NFKD", texto)
    ascii_ = "".join(c for c in nfkd if not unicodedata.combining(c))
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_.lower()).strip("-")
    return slug or "sem-nome"


def _find_child(parent_id: str, name: str) -> str | None:
    svc = get_drive_service()
    safe_name = name.replace("'", "\\'")
    q = (
        f"'{parent_id}' in parents and name = '{safe_name}' "
        f"and mimeType = '{FOLDER_MIME}' and trashed = false"
    )
    res = svc.files().list(q=q, fields="files(id, name)", pageSize=1).execute()
    files = res.get("files", [])
    return files[0]["id"] if files else None


def _create_folder(parent_id: str, name: str) -> str:
    svc = get_drive_service()
    metadata = {"name": name, "mimeType": FOLDER_MIME, "parents": [parent_id]}
    folder = svc.files().create(body=metadata, fields="id").execute()
    folder_id = folder.get("id")
    if not folder_id:
        raise RuntimeError(f"Falha ao criar pasta '{name}' no Drive.")
    return folder_id


def _ensure_path(parts: list[str]) -> str:
    """Cria (ou reutiliza) hierarquia de pastas a partir da raiz."""
    parent = get_drive_folder_id()
    for p in parts:
        existing = _find_child(parent, p)
        parent = existing or _create_folder(parent, p)
    return parent


def _extensao(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in MIMETYPES:
        raise ValueError(
            f"Extensão '{ext}' não suportada. Use PDF, PNG ou JPG."
        )
    return ext


def upload(
    *,
    tipo: TipoComprovante,
    ano: int,
    subpasta: str,
    nome_arquivo: str,
    conteudo: bytes,
) -> str:
    """Sobe arquivo e devolve a URL de visualização (webViewLink).

    - `subpasta`: já normalizada pela chamada de mais alto nível
      (ex: `M001-joao-silva`, `coach`, `festa-junina-2026`).
    - `nome_arquivo`: inclui extensão (ex: `2026-01.pdf`).
    """
    ext = _extensao(nome_arquivo)
    folder_id = _ensure_path([str(ano), tipo, subpasta])

    media = MediaIoBaseUpload(
        io.BytesIO(conteudo), mimetype=MIMETYPES[ext], resumable=False
    )
    metadata = {"name": nome_arquivo, "parents": [folder_id]}
    svc = get_drive_service()
    file = (
        svc.files()
        .create(body=metadata, media_body=media, fields="id, webViewLink")
        .execute()
    )
    file_id = file.get("id")
    if not file_id:
        raise RuntimeError(f"Upload de '{nome_arquivo}' falhou (sem ID retornado).")
    url = file.get("webViewLink") or f"https://drive.google.com/file/d/{file_id}/view"
    logger.info("comprovante enviado: tipo=%s pasta=%s arquivo=%s", tipo, subpasta, nome_arquivo)
    return url
