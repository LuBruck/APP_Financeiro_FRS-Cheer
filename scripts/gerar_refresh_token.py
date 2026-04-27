"""Gera o refresh token OAuth da conta institucional do Drive.

Roda 1x no setup. O refresh token gerado vai para `.streamlit/secrets.toml`,
seção [google_drive_oauth]. A partir daí o app sobe arquivos no Drive como
se fosse a conta institucional, sem precisar de novo login.

Pré-requisitos:
1. OAuth Client tipo "Desktop app" criado no Google Cloud Console.
2. Arquivo `client_secret.json` baixado e salvo nesta pasta (`scripts/`).
3. Conta institucional (ex: cheer.financeiro@gmail.com) cadastrada como
   "Test user" no OAuth consent screen.

Como rodar:
    python scripts/gerar_refresh_token.py

Vai abrir o navegador. **Logue com a conta institucional** (não com a sua
conta pessoal). Autorize o acesso ao Drive. O refresh token é impresso no
terminal — copie e cole no secrets.toml.
"""

from __future__ import annotations

import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
CLIENT_SECRET = Path(__file__).parent / "client_secret.json"


def main() -> None:
    if not CLIENT_SECRET.exists():
        print(f"ERRO: {CLIENT_SECRET} não encontrado.")
        print("Baixe o JSON do OAuth Client (Desktop app) no Google Cloud Console")
        print("e salve nesse caminho exato.")
        sys.exit(1)

    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent")

    if not creds.refresh_token:
        print("ERRO: Google não retornou refresh token.")
        print("Possíveis causas: você já autorizou esse app antes com a mesma conta.")
        print("Solução: revogue o acesso em https://myaccount.google.com/permissions")
        print("e rode este script de novo.")
        sys.exit(1)

    print()
    print("=" * 70)
    print("Cole no .streamlit/secrets.toml:")
    print("=" * 70)
    print()
    print("[google_drive_oauth]")
    print(f'client_id = "{creds.client_id}"')
    print(f'client_secret = "{creds.client_secret}"')
    print(f'refresh_token = "{creds.refresh_token}"')
    print()


if __name__ == "__main__":
    main()
