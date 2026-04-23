"""Carregamento de secrets e conexão com as APIs do Google.

Centraliza a criação dos clientes (`gspread` para Sheets, Drive API para arquivos)
para que o resto do app não repita boilerplate de autenticação.
"""

from __future__ import annotations

import logging
from functools import lru_cache

import gspread
import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Nomes das abas da planilha (Seção 6.2 do PRD).
SHEET_MEMBROS = "membros"
SHEET_PAGAMENTOS = "pagamentos"
SHEET_DESPESAS = "despesas"
SHEET_EVENTOS = "eventos"
SHEET_VENDAS = "vendas_produtos"
SHEET_CONFIGURACOES = "configuracoes"


@lru_cache(maxsize=1)
def _credentials() -> Credentials:
    sa_info = dict(st.secrets["google_service_account"])
    return Credentials.from_service_account_info(sa_info, scopes=SCOPES)


@lru_cache(maxsize=1)
def get_gspread_client() -> gspread.Client:
    return gspread.authorize(_credentials())


@lru_cache(maxsize=1)
def get_drive_service():
    return build("drive", "v3", credentials=_credentials(), cache_discovery=False)


def get_spreadsheet_id() -> str:
    return st.secrets["google_resources"]["spreadsheet_id"]


def get_drive_folder_id() -> str:
    return st.secrets["google_resources"]["drive_folder_id"]


def get_spreadsheet() -> gspread.Spreadsheet:
    return get_gspread_client().open_by_key(get_spreadsheet_id())


def get_worksheet(name: str) -> gspread.Worksheet:
    return get_spreadsheet().worksheet(name)
