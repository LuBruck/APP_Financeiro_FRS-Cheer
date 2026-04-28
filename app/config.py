"""Carregamento de secrets e conexão com as APIs do Google.

Centraliza a criação dos clientes (`gspread` para Sheets, Drive API para arquivos)
para que o resto do app não repita boilerplate de autenticação.
"""

from __future__ import annotations

import logging
from functools import lru_cache

import gspread
import streamlit as st
from google.oauth2.credentials import Credentials as UserCredentials
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

# A SA é usada APENAS para o Sheets. O Drive usa OAuth da conta institucional
# (ver [google_drive_oauth] no secrets) porque Service Accounts em Gmail comum
# não têm cota de armazenamento própria — uploads falham com storageQuotaExceeded.
SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.file"]
DRIVE_TOKEN_URI = "https://oauth2.googleapis.com/token"

# Nomes das abas da planilha (Seção 6.2 do PRD).
SHEET_MEMBROS = "membros"
SHEET_PAGAMENTOS = "pagamentos"
SHEET_DESPESAS = "despesas"
SHEET_EVENTOS = "eventos"
SHEET_VENDAS = "vendas_produtos"
SHEET_PRODUTOS = "produtos"
SHEET_CONFIGURACOES = "configuracoes"
SHEET_USUARIOS = "usuarios"

_SECOES_OBRIGATORIAS = [
    "google_service_account",
    "google_drive_oauth",
    "auth",
    "google_resources",
]

_CAMPOS_SERVICE_ACCOUNT = ["type", "project_id", "private_key", "client_email"]
_CAMPOS_DRIVE_OAUTH = ["client_id", "client_secret", "refresh_token"]
_CAMPOS_AUTH = ["redirect_uri", "cookie_secret", "client_id", "client_secret", "server_metadata_url"]
_CAMPOS_RESOURCES = ["spreadsheet_id", "drive_folder_id"]


def validar_secrets() -> list[str]:
    """Retorna lista de erros de configuração no secrets.toml. Vazia = OK."""
    erros: list[str] = []
    for secao in _SECOES_OBRIGATORIAS:
        if secao not in st.secrets:
            erros.append(f"Seção [{secao}] ausente no secrets.toml.")
    if erros:
        return erros

    sa = st.secrets["google_service_account"]
    for campo in _CAMPOS_SERVICE_ACCOUNT:
        if not sa.get(campo):
            erros.append(f"[google_service_account].{campo} está vazio ou ausente.")
        # Detecta formato JSON colado em vez de TOML (valor começa com '{' ou '"type":')
        if campo == "type" and str(sa.get("type", "")).startswith("{"):
            erros.append(
                "[google_service_account] parece estar no formato JSON em vez de TOML. "
                "Cada campo deve usar `chave = \"valor\"`, não `\"chave\": \"valor\"`."
            )

    drive_oauth = st.secrets["google_drive_oauth"]
    for campo in _CAMPOS_DRIVE_OAUTH:
        if not drive_oauth.get(campo):
            erros.append(f"[google_drive_oauth].{campo} está vazio ou ausente.")

    auth = st.secrets["auth"]
    for campo in _CAMPOS_AUTH:
        if not auth.get(campo):
            erros.append(f"[auth].{campo} está vazio ou ausente.")
    if len(str(auth.get("cookie_secret", ""))) < 32:
        erros.append("[auth].cookie_secret deve ter pelo menos 32 caracteres.")

    resources = st.secrets["google_resources"]
    for campo in _CAMPOS_RESOURCES:
        if not resources.get(campo):
            erros.append(f"[google_resources].{campo} está vazio ou ausente.")

    return erros


def mostrar_erros_config_e_parar() -> None:
    """Exibe erros de configuração na UI e para a execução."""
    erros = validar_secrets()
    if not erros:
        return
    st.error("**Configuração incompleta no secrets.toml.** Corrija os itens abaixo:")
    for e in erros:
        st.markdown(f"- {e}")
    st.info(
        "Consulte `.streamlit/secrets.toml.example` para o formato correto. "
        "Cada campo deve usar `chave = \"valor\"` (TOML), não `\"chave\": \"valor\"` (JSON)."
    )
    st.stop()


@lru_cache(maxsize=1)
def _sheets_credentials() -> Credentials:
    sa_info = dict(st.secrets["google_service_account"])
    return Credentials.from_service_account_info(sa_info, scopes=SHEETS_SCOPES)


@lru_cache(maxsize=1)
def _drive_credentials() -> UserCredentials:
    cfg = st.secrets["google_drive_oauth"]
    return UserCredentials(
        token=None,
        refresh_token=cfg["refresh_token"],
        client_id=cfg["client_id"],
        client_secret=cfg["client_secret"],
        token_uri=DRIVE_TOKEN_URI,
        scopes=DRIVE_SCOPES,
    )


@lru_cache(maxsize=1)
def get_gspread_client() -> gspread.Client:
    return gspread.authorize(_sheets_credentials())


@lru_cache(maxsize=1)
def get_drive_service():
    return build("drive", "v3", credentials=_drive_credentials(), cache_discovery=False)


def get_spreadsheet_id() -> str:
    return st.secrets["google_resources"]["spreadsheet_id"]


def get_drive_folder_id() -> str:
    return st.secrets["google_resources"]["drive_folder_id"]


def get_spreadsheet() -> gspread.Spreadsheet:
    return get_gspread_client().open_by_key(get_spreadsheet_id())


def get_worksheet(name: str) -> gspread.Worksheet:
    return get_spreadsheet().worksheet(name)
