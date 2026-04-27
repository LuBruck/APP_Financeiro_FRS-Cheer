# App Financeiro — Furiosos Cheer

Web app em **Streamlit** para gestão financeira do **Furiosos Cheer** (time universitário de líder de torcida). Centraliza mensalidades, despesas, eventos, vendas e comprovantes num único painel, substituindo o fluxo manual de planilhas e pastas de OneDrive.

- **Dados:** Google Sheets (6 abas)
- **Comprovantes:** Google Drive (organizado por entidade/ano)
- **Login:** Google OIDC nativo (`st.login()`)
- **Hospedagem:** Streamlit Community Cloud (gratuito)

Documentação completa: `docs/prd-app-financeiro-furiosos-cheer.md`

---

## Pré-requisitos (setup único — faça uma vez)

### 1. Projeto no Google Cloud

1. Acesse [console.cloud.google.com](https://console.cloud.google.com) e crie um projeto (ex: `app-financeiro-cheer`).
2. Ative as APIs: **Google Sheets API** e **Google Drive API**.

### 2. Service Account (app → Google APIs)

1. Em **IAM & Admin → Service Accounts**, crie uma conta de serviço.
2. Gere uma chave JSON (aba **Keys → Add Key → JSON**) e guarde o arquivo.
3. **Compartilhe** a planilha e a pasta do Drive com o e-mail da Service Account (como editor).

### 3. OAuth 2.0 Client (login do usuário)

1. Em **APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID**.
2. Tipo: **Web application**.
3. Em **Authorized redirect URIs**, adicione:
   - `http://localhost:8501/oauth2callback` (desenvolvimento local)
   - `https://<seu-app>.streamlit.app/oauth2callback` (produção)
4. Anote o **Client ID** e o **Client Secret**.

### 4. Planilha Google Sheets

Crie uma planilha com **6 abas** exatamente com esses nomes e cabeçalhos:

| Aba | Colunas (em ordem) |
|-----|--------------------|
| `membros` | `id_membro`, `nome`, `tipo`, `email`, `telefone`, `semestre_entrada`, `status`, `observacoes` |
| `pagamentos` | `id_pagamento`, `id_membro`, `mes_referencia`, `data_vencimento`, `data_pagamento`, `valor_original`, `multa`, `valor_pago`, `status`, `link_comprovante`, `observacoes`, `ativo`, `criado_em`, `criado_por`, `atualizado_em`, `atualizado_por` |
| `despesas` | `id_despesa`, `data`, `categoria`, `descricao`, `valor`, `beneficiario`, `link_comprovante`, `id_evento_relacionado`, `observacoes`, `ativo`, `criado_em`, `criado_por`, `atualizado_em`, `atualizado_por` |
| `eventos` | `id_evento`, `nome`, `data`, `receita_bruta`, `publico_estimado`, `observacoes`, `ativo`, `criado_em`, `criado_por`, `atualizado_em`, `atualizado_por` |
| `vendas_produtos` | `id_venda`, `data`, `produto`, `quantidade`, `valor_unitario`, `valor_total`, `comprador`, `link_comprovante`, `observacoes`, `ativo`, `criado_em`, `criado_por`, `atualizado_em`, `atualizado_por` |
| `configuracoes` | `chave`, `valor`, `descricao` |

Preencha a aba `configuracoes` com os valores padrão:

| chave | valor |
|-------|-------|
| `valor_mensalidade_atleta` | `55` |
| `valor_mensalidade_associado` | `15` |
| `valor_multa_atraso` | `7` |
| `dia_vencimento` | `10` |
| `nome_time` | `Furiosos Cheer` |

### 5. Pasta no Google Drive

Crie uma pasta raiz (ex: `Financeiro-Furiosos-Cheer`) e compartilhe com a Service Account. O app cria as subpastas automaticamente.

---

## Setup local

```bash
# 1. Clone e entre na pasta
git clone <url-do-repo>
cd App_Financeiro_cheer

# 2. Crie o virtualenv e instale dependências
python3 -m venv venv
source venv/bin/activate          # Linux/Mac
# venv\Scripts\activate           # Windows
pip install -r requirements.txt

# (opcional) dependências de desenvolvimento
pip install -r requirements-dev.txt

# 3. Configure os secrets
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# edite o arquivo conforme instruções abaixo

# 4. Rode o app
streamlit run app/streamlit_app.py
# Abre em http://localhost:8501
```

### Como preencher o secrets.toml

> **Formato:** TOML usa `chave = "valor"`. Não cole JSON direto (com `:` e `,`).

Abra `.streamlit/secrets.toml` e substitua cada placeholder:

```toml
# ── 1. Service Account ─────────────────────────────────────────────
# Copie os campos individualmente do JSON baixado no Google Cloud.
# NÃO cole o JSON inteiro — converta cada campo para formato TOML.
[google_service_account]
type = "service_account"
project_id = "seu-projeto-gcp"
private_key_id = "abc123..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "nome@seu-projeto.iam.gserviceaccount.com"
client_id = "12345678"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
universe_domain = "googleapis.com"

# ── 2. OAuth para login do usuário ────────────────────────────────
[auth]
redirect_uri = "http://localhost:8501/oauth2callback"
cookie_secret = "gere-aqui-uma-string-aleatoria-de-pelo-menos-32-chars"
client_id = "123456789-abc.apps.googleusercontent.com"
client_secret = "GOCSPX-..."
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"

# ── 3. Emails autorizados ─────────────────────────────────────────
[authorized_users]
"diretor@seudominio.com" = "admin"
# "assistente@seudominio.com" = "assistant"

# ── 4. IDs dos recursos Google ────────────────────────────────────
[google_resources]
spreadsheet_id = "1AbCdEfGhIj..."   # da URL da planilha
drive_folder_id = "1XyZw..."        # da URL da pasta no Drive
```

**Como gerar o `cookie_secret`:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

> **NUNCA** commite o `secrets.toml`. Ele está no `.gitignore`.

---

## Deploy no Streamlit Community Cloud

1. Faça push do código no GitHub (repositório **público**).
2. Acesse [share.streamlit.io](https://share.streamlit.io) e conecte o repositório.
3. Em **Advanced settings → Secrets**, cole o conteúdo completo do seu `secrets.toml`.
4. Em **Main file path**, coloque `app/streamlit_app.py`.
5. Clique **Deploy**.

Ao fazer merge na branch `main`, o Streamlit Cloud faz redeploy automático.

**URI de redirect para produção:** adicione `https://<seu-app>.streamlit.app/oauth2callback` nas URIs autorizadas do OAuth Client no Google Cloud Console.

---

## Gestão de acesso

Os usuários autorizados são gerenciados diretamente pelo app, na tela **Usuários** (só visível para admins). Não é necessário mexer no Streamlit Cloud para adicionar ou remover pessoas.

### Setup inicial (uma vez só)

1. Crie a aba `usuarios` na planilha com as colunas:
   ```
   email | role | ativo | criado_em | criado_por | atualizado_em | atualizado_por
   ```
2. Adicione uma linha inicial com seu próprio email:
   ```
   lucasbruck04@gmail.com | admin | TRUE
   ```
   (os campos de auditoria podem ficar vazios nessa linha inicial)
3. Opcionalmente, mantenha seu email também em `[authorized_users]` no `secrets.toml` como fallback de emergência.

### Adicionar novo usuário

1. Acesse o app → **Usuários** → **Adicionar usuário**
2. Informe o email Google e o papel (admin ou assistente)
3. Salve — o acesso é liberado em até 1 minuto (sem redeploy)

### Remover usuário (troca de diretoria)

1. Acesse o app → **Usuários**
2. Clique em **Desativar** ao lado do email
3. O acesso é bloqueado na próxima sessão do usuário

### Fallback (emergência)

Se a aba `usuarios` estiver vazia ou inacessível, o app usa automaticamente `[authorized_users]` do `secrets.toml`. Isso garante que você nunca fique completamente travado.

### Transferência para o próximo diretor

1. Na tela Usuários, adicione o email do novo diretor como `admin`
2. Desative o email do diretor anterior
3. Atualize o `[authorized_users]` do secrets.toml também (fallback)
4. O novo diretor acessa pelo link do app — sem treinamento de sistema necessário

---

## Operação diária

| Tarefa | Tela |
|--------|------|
| Registrar mensalidade recebida | Registrar Pagamento |
| Ver quem está devendo | Cobranças Pendentes |
| Lançar despesa do time | Registrar Despesa |
| Criar/atualizar evento | Eventos e Vendas → aba Eventos |
| Registrar venda de produto | Eventos e Vendas → aba Vendas |
| Ver histórico de um membro | Histórico do Membro |
| Visão geral do caixa | Dashboard |

**Adição/remoção de membros:** edite diretamente a aba `membros` na planilha Google Sheets. O app reflete as mudanças automaticamente (cache de 5 minutos).

**Alteração de valores** (mensalidade, multa, dia de vencimento): edite a aba `configuracoes` na planilha. Não mexe no código.

---

## Estrutura do código

```
app/
├── streamlit_app.py          # Entry point (Home + auth guard + validação de config)
├── pages/
│   ├── 1_Dashboard.py        # KPIs, gráficos, últimas transações
│   ├── 2_Registrar_Pagamento.py
│   ├── 3_Cobrancas_Pendentes.py
│   ├── 4_Registrar_Despesa.py
│   ├── 5_Eventos_e_Vendas.py
│   └── 6_Historico_Membro.py
├── repositories/             # Acesso a dados (Sheets + Drive)
├── services/                 # Regras de negócio puras
├── models/                   # Dataclasses (Membro, Pagamento, Despesa, Evento, Venda)
├── utils/formatters.py       # Formatação pt-BR (R$, DD/MM/YYYY)
├── auth.py                   # Login Google OIDC + whitelist
└── config.py                 # Secrets + clientes Google + validação de configuração
```

Padrão: **Repository Pattern** — `pages/` nunca importa `gspread` diretamente. Fluxo: `pages/` → `services/` → `repositories/` → Google APIs.

---

## Comandos de desenvolvimento

```bash
# Testes
pytest tests/ -v

# Lint
ruff check app/
ruff format app/

# Type check
mypy app/
```

---

## Status do projeto

- [x] **Sprint 0** — Setup Google Cloud, Sheets, Drive, repo
- [x] **Sprint 1** — Auth + config + repo de membros + Home
- [x] **Sprint 2** — Registrar Pagamento + Cobranças Pendentes + geração lazy de cobranças
- [x] **Sprint 3** — Registrar Despesa + Eventos e Vendas
- [x] **Sprint 4** — Dashboard + Histórico do Membro
- [x] **Sprint 5** — Polimento: testes, UX, validação de config, README

---

## Backlog (próximas versões)

Ideias levantadas durante o desenvolvimento, priorizadas para versões futuras:

- **Grade de mensalidades — filtro por ano:** Permitir visualizar a situação de mensalidades de anos anteriores na grade do Dashboard. Exige resolver como filtrar quais membros estavam ativos em cada ano (membros podem sair e voltar), então a lógica de "ativo no período" precisa ser modelada antes de implementar.

- **Registro de pagamento em lote:** Selecionar múltiplas cobranças de um mesmo membro na tela de Cobranças Pendentes e registrar o pagamento de todas de uma vez, com um único formulário e comprovante.

---

## Licença

MIT — ver `LICENSE`.
