# CLAUDE.md — App Financeiro Furiosos Cheer

Instruções para o Claude Code trabalhar neste repositório. Este arquivo é lido automaticamente a cada sessão.

## Fonte da verdade

Antes de tomar qualquer decisão arquitetural, de modelagem ou de UX, **leia o PRD** em `docs/prd.md`. Ele é a fonte oficial de decisões do projeto. Se algo neste CLAUDE.md conflita com o PRD, o PRD vence — avise o usuário sobre a inconsistência.

Seções do PRD que você vai consultar com mais frequência:

- **Seção 5 (Arquitetura)** — stack, padrão de organização do código (Repository Pattern)
- **Seção 6 (Modelo de dados)** — estrutura das 6 abas do Sheets e da pasta do Drive
- **Seção 7 (Telas)** — o que cada página do Streamlit faz
- **Seção 8 (Segurança)** — autenticação Google OIDC + Service Account

## Sobre o projeto (resumo de 1 parágrafo)

Web app em Streamlit para gestão financeira do Furiosos Cheer (time universitário de líder de torcida). Dados em Google Sheets (6 abas), comprovantes em Google Drive (organização por entidade), login via Google OIDC nativo (`st.login()`), hospedagem no Streamlit Community Cloud. Usuários: diretor financeiro + até 2 assistentes. Volume: ~30 membros, ~30 transações/mês.

## Stack e versões

- Python 3.11+
- Streamlit ≥ 1.42 (exigência para `st.login()`)
- `gspread` para Google Sheets
- `google-api-python-client` para Google Drive
- `Authlib` para OIDC (dependência de `st.login()`)
- Gerenciador de pacotes: `uv` (preferido) ou `pip`

Versões pinadas em `requirements.txt`. Não atualizar dependências sem pedido explícito.

## Estrutura do repositório

```
app/
├── streamlit_app.py          # Entry point (tela Home + auth guard)
├── pages/                    # Uma tela por arquivo
│   ├── 1_Dashboard.py
│   ├── 2_Registrar_Pagamento.py
│   ├── 3_Cobrancas_Pendentes.py
│   ├── 4_Registrar_Despesa.py
│   ├── 5_Eventos_e_Vendas.py
│   └── 6_Historico_Membro.py
├── repositories/             # Acesso a dados
│   ├── base.py               # Classes abstratas
│   ├── membros_repo.py
│   ├── pagamentos_repo.py
│   ├── despesas_repo.py
│   ├── eventos_repo.py
│   ├── vendas_repo.py
│   ├── configuracoes_repo.py
│   └── comprovantes_repo.py  # Upload pro Drive
├── services/                 # Regras de negócio
│   ├── calculo_dividas.py
│   ├── dashboard_service.py
│   └── upload_service.py
├── models/                   # Dataclasses tipadas (Membro, Pagamento, etc)
├── auth.py                   # Login + whitelist
├── config.py                 # Carregamento de secrets, conexão com APIs
└── utils/                    # Helpers (formatação BR, datas, etc)

docs/
└── prd.md                    # PRD do projeto (fonte da verdade)

tests/                        # Espelha a estrutura de app/
.streamlit/
└── secrets.toml              # NUNCA commitar; está no .gitignore
requirements.txt
pyproject.toml
README.md
CLAUDE.md                     # Este arquivo
```

## Princípio arquitetural número 1: Repository Pattern

**A camada `pages/` nunca fala com Google direto.** Fluxo correto:

```
pages/ ─────> services/ ─────> repositories/ ─────> Google APIs
```

Exemplo correto:
```python
# pages/2_Registrar_Pagamento.py
from services.calculo_dividas import registrar_pagamento

if st.button("Salvar"):
    registrar_pagamento(membro_id, valor, comprovante)
```

Exemplo ERRADO (não fazer):
```python
# pages/2_Registrar_Pagamento.py
import gspread  # ❌ pages nunca importa client de infraestrutura
sheet = gspread.open(...)
sheet.append_row(...)
```

Motivo: isolamento permite trocar Sheets por Postgres no futuro mexendo só em `repositories/`.

## Regras específicas do projeto

### Formatação (sempre pt-BR na UI, ISO no armazenamento)

- Datas exibidas: `DD/MM/YYYY`. Armazenadas: `YYYY-MM-DD` (ISO 8601).
- Valores exibidos: `R$ 1.234,56`. Armazenados: número puro (ex: `1234.56`).
- Mês de referência: formato `YYYY-MM` (ex: `2026-01`).
- Use helpers em `utils/formatters.py` — não formate inline.

### IDs

- `id_pagamento`, `id_despesa`, `id_evento`, `id_venda` → UUID v4 gerado por `uuid.uuid4()`.
- `id_membro` → string curta manual (ex: `M001`) preenchida pelo diretor na planilha.

### Soft delete

Nunca delete linhas fisicamente. Toda tabela tem coluna `ativo` (boolean). Exclusão = `ativo = False`. Toda query de leitura filtra `ativo = True` por default — deixe o filtro explícito nos repositórios, não presuma.

### Campos de auditoria

Toda escrita preenche `criado_em`, `criado_por`, `atualizado_em`, `atualizado_por`. O `criado_por` e `atualizado_por` vêm de `st.user.email`. Encapsule isso em `repositories/base.py`.

### Cache de leituras

Use `@st.cache_data(ttl=300)` (5 min) em funções de leitura dos repositórios. **Invalide o cache explicitamente após cada escrita** com `st.cache_data.clear()` ou invalidação seletiva. Não confie só no TTL — dados pós-escrita precisam aparecer no ato.

### Rate limit do Google Sheets

Limite prático: 60 leituras/minuto por usuário. Sempre prefira:

- Ler a aba inteira e filtrar em memória (1 request) vs. ler célula a célula (N requests)
- `worksheet.batch_update()` vs. múltiplos `worksheet.update()`

Se for fazer loop de escritas, pare e refatore para batch.

### Secrets

Tudo sensível em `.streamlit/secrets.toml` (nunca commitar). Acessar via `st.secrets["chave"]`. Chaves esperadas:

```toml
[google_service_account]
# JSON da Service Account

[auth]
redirect_uri = "..."
cookie_secret = "..."
client_id = "..."
client_secret = "..."
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"

[authorized_users]
# { "email@domain.com" = "admin" | "assistant" }

[google_resources]
spreadsheet_id = "..."
drive_folder_id = "..."
```

### Auth guard

Toda página em `pages/` começa com:

```python
from auth import require_login

require_login()  # redireciona se não logado ou não autorizado
```

Nunca expor uma página sem esse guard.

## Comandos úteis

```bash
# Rodar localmente
streamlit run app/streamlit_app.py

# Instalar dependências
uv pip install -r requirements.txt

# Rodar testes
pytest tests/ -v

# Lint
ruff check app/
ruff format app/

# Type check
mypy app/
```

## Convenções de código

- **Tipagem:** todas as funções públicas têm type hints. Use `from __future__ import annotations` no topo.
- **Docstrings:** Google style, apenas para funções não-triviais. Não documente o óbvio.
- **Nomes em português:** nomes de modelos de domínio (`Membro`, `Pagamento`, `Despesa`) e colunas do Sheets são em português. Nomes de funções genéricas (`get_by_id`, `to_dict`) em inglês.
- **Logging:** use `logging` padrão, nível `INFO` em produção. Nunca logar valores sensíveis (senhas, tokens, conteúdo completo de comprovantes).
- **Imports:** ordem padrão (stdlib → third-party → local), ordenados pelo `ruff`.

## Testes

- **Obrigatório** para `services/` (regras de negócio puras, fáceis de testar).
- **Recomendado** para `repositories/` usando mock do `gspread`.
- **Opcional** para `pages/` (teste manual costuma ser mais eficaz em UI Streamlit).
- Use `pytest` + `pytest-mock`. Fixtures compartilhadas em `tests/conftest.py`.

## Gotchas conhecidos

1. **Streamlit re-executa o script inteiro a cada interação.** Use `st.session_state` para persistir estado entre reruns. Não assuma que variáveis globais sobrevivem.

2. **`st.cache_data` serializa argumentos.** Não passe objetos não-hashable (conexões, clients) pra funções cacheadas. Passe só IDs e carregue o client dentro.

3. **Datas no Google Sheets são números serial.** O `gspread` retorna como string por default. Converta explicitamente em `repositories/`, nunca espalhe `datetime.strptime` pelo código.

4. **Upload ao Drive pode falhar silenciosamente.** Sempre verifique o retorno da API e faça raise se `file.get('id')` for None.

5. **Lazy generation de cobranças mensais (ver PRD 6.3).** A verificação roda uma vez por sessão (use `st.session_state["cobrancas_checked_{mes}"]` como flag). Não rode em toda rerun.

## Fluxo de trabalho

- **Branches:** `main` é sempre deployável. Features vão em `feature/nome-curto`.
- **Commits:** mensagens em português, imperativo. Ex: `adiciona tela de registro de pagamento`, `corrige cálculo de multa em atraso`.
- **Deploy:** automático no Streamlit Cloud ao fazer merge na `main`. Não há staging — teste local antes.

## Ao começar uma nova sessão

1. Leia este CLAUDE.md (você está fazendo isso agora).
2. Leia `docs/prd.md` se a tarefa envolver decisões de produto ou arquitetura.
3. Cheque `git status` e `git log --oneline -n 10` para saber onde o projeto parou.
4. Se a tarefa não estiver clara, pergunte antes de codar.

## Quando pedir confirmação ao usuário

- Antes de instalar novas dependências
- Antes de mudar estrutura de pastas
- Antes de modificar `requirements.txt` ou `pyproject.toml`
- Antes de mexer em `.streamlit/secrets.toml` (na verdade, nunca mexa nele — só oriente o usuário)
- Antes de fazer mudanças que conflitam com o PRD
- Antes de deletar arquivos

## O que NUNCA fazer

- Commitar secrets, chaves, tokens, `.streamlit/secrets.toml`, JSON de Service Account
- Fazer escritas no Sheets sem invalidar cache
- Fazer leituras linha-a-linha em loops (quebra rate limit)
- Remover auditoria/soft delete "pra simplificar"
- Adicionar frameworks pesados (React, Vue, Django) — este é um app Streamlit puro
- Alterar a estrutura do PRD sem pedido explícito
