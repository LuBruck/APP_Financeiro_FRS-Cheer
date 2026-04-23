# App Financeiro — Furiosos Cheer

Web app em Streamlit para gestão financeira do **Furiosos Cheer** (time universitário de líder de torcida). Dados em Google Sheets, comprovantes em Google Drive, login via Google OIDC.

Ver **`docs/prd-app-financeiro-furiosos-cheer.md`** para o PRD completo (fonte da verdade).

## Stack

- Python 3.11+ (testado em 3.12)
- Streamlit ≥ 1.42 (`st.login()`)
- `gspread` + `google-api-python-client`
- `Authlib` (OIDC)

## Setup local

1. **Clone o repositório** e entre na pasta:
   ```bash
   git clone <url-do-repo>
   cd App_Financeiro_cheer
   ```

2. **Crie um virtualenv** e instale as dependências:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate          # Linux/Mac
   pip install -r requirements.txt
   ```

   Para desenvolvimento (testes, lint, typecheck):
   ```bash
   pip install -r requirements-dev.txt
   ```

3. **Configure os secrets:**
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   # edite e preencha com os valores reais
   ```

   Valores necessários (ver PRD §8):
   - **JSON da Service Account** (em `[google_service_account]`)
   - **OAuth 2.0 Client ID/Secret** + `redirect_uri` + `cookie_secret` (em `[auth]`)
   - **Whitelist de emails** autorizados (em `[authorized_users]`)
   - **IDs** da planilha e da pasta do Drive (em `[google_resources]`)

   > **NUNCA** commite o `secrets.toml`. Ele está no `.gitignore`.

4. **Rode o app:**
   ```bash
   streamlit run app/streamlit_app.py
   ```
   Abre em `http://localhost:8501`.

## Estrutura do código

```
app/
├── streamlit_app.py     # Entry point (Home + auth guard)
├── pages/               # Telas (uma por arquivo) — próximos sprints
├── repositories/        # Acesso a dados (Sheets/Drive)
├── services/            # Regras de negócio
├── models/              # Dataclasses (Membro, Pagamento, ...)
├── utils/               # Helpers (formatação pt-BR, datas)
├── auth.py              # Login + whitelist
└── config.py            # Secrets + clientes Google
```

Arquitetura: **Repository Pattern** (ver CLAUDE.md e PRD §5.4). `pages/` nunca importa `gspread` direto — chama `services/` → `repositories/`.

## Comandos úteis

```bash
# Rodar app local
streamlit run app/streamlit_app.py

# Rodar testes
pytest tests/ -v

# Lint
ruff check app/
ruff format app/

# Type check
mypy app/
```

## Status do projeto

- [x] **Sprint 0** — Setup Google Cloud, Sheets, Drive, repo
- [x] **Sprint 1** — Fundação: auth + config + repo de membros + Home
- [ ] **Sprint 2** — Fluxo de pagamentos (registrar + cobranças pendentes)
- [ ] **Sprint 3** — Despesas + eventos + vendas
- [ ] **Sprint 4** — Dashboard + histórico do membro
- [ ] **Sprint 5** — Polimento e deploy

## Licença

MIT — ver `LICENSE`.
