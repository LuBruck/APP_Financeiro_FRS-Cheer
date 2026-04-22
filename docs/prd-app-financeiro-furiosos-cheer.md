# PRD — App de Gestão Financeira (Time de Líder de Torcida)

> Documento de definição do projeto. Última atualização: 22/04/2026

---

## 1. Visão geral

### 1.1 O que é

Sistema web de gestão financeira para o **Furiosos Cheer**, time universitário de líder de torcida. Substitui o fluxo manual atual baseado em múltiplas planilhas soltas por uma aplicação única, acessível pelo navegador, que centraliza: registro de mensalidades, controle de inadimplência, registro de despesas, organização de comprovantes e visão consolidada do caixa.

### 1.2 Para quem

- **Usuário principal:** diretor(a) financeiro do Furiosos Cheer, responsável por todos os registros e prestação de contas.
- **Usuários secundários:** até 2 assistentes de diretoria que auxiliam em períodos de alto volume (início de semestre, pré-evento).
- **Beneficiários indiretos:** demais membros da diretoria (presidente, vice) que consomem relatórios, e atletas que dependem de informação clara sobre sua situação de pagamento.

### 1.3 Por que existir

O fluxo atual tem três problemas dolorosos:

1. **Fragmentação.** Cada tipo de transação mora em uma planilha diferente (mensalidades, coach, eventos, vendas), sem visão consolidada.
2. **Trabalho manual repetitivo.** Cada pagamento exige abrir planilha, localizar linha do membro, marcar como pago, salvar comprovante em pasta separada do OneDrive.
3. **Transição difícil entre diretorias.** Cada novo diretor herda um emaranhado de arquivos com convenções próprias do anterior, e precisa redescobrir o sistema a cada troca.

O app resolve esses três pontos ao (1) centralizar dados numa estrutura única, (2) automatizar a ligação entre registro-de-pagamento e comprovante, e (3) padronizar o fluxo de forma que o próximo diretor só precisa do link e do login, sem repassar arquivos.

### 1.4 O que NÃO é

Para evitar expectativas erradas, o sistema **não é**:

- Um ERP completo (não faz emissão de nota fiscal, conciliação bancária automática, integração com Receita Federal)
- Um aplicativo para atletas acompanharem seus pagamentos (MVP é só para diretoria; acesso para atletas é escopo de v2)
- Um sistema multi-tenant (serve apenas o Furiosos Cheer; não é pensado para outros times usarem a mesma instância)

---

## 2. Contexto e problema atual

### 2.1 Fluxo atual do diretor financeiro

O diretor opera em dois ambientes desconectados:

1. **Planilhas (atualmente em migração do Excel → Google Sheets).** Uma por domínio:
   - Controle de mensalidades mês a mês (marcação manual de "pago/não pago")
   - Pagamento de coaches
   - Ganhos e despesas de eventos
   - Vendas de produtos
2. **OneDrive.** Pasta com subpastas por mês, onde são salvos os PDFs/prints de comprovantes de PIX.

A ligação entre os dois é **implícita** (nome do arquivo no OneDrive "combina" com a linha da planilha) e depende de disciplina manual.

### 2.2 Ciclo mensal típico

Ao receber um comprovante pelo WhatsApp, o diretor executa uma sequência manual:

1. Abrir planilha de mensalidades
2. Localizar a linha do membro
3. Marcar o mês como pago
4. Baixar o PDF do comprovante
5. Renomear o arquivo seguindo alguma convenção
6. Fazer upload no OneDrive na pasta correta
7. Eventualmente anotar em outra planilha

Repetido para cada pagamento de cada membro, todo mês. Passos 1 a 7 somam ~2-3 minutos por comprovante, escalando linearmente com o número de membros.

### 2.3 Dores concretas identificadas

| # | Problema | Consequência |
|---|---|---|
| D1 | Planilhas separadas, sem visão consolidada | Diretor não sabe rapidamente "qual o caixa real do mês" |
| D2 | Status "pago/não pago" como marcação binária em célula | Impossível fazer análise temporal (atraso médio, sazonalidade) |
| D3 | Comprovantes desacoplados dos registros | Encontrar um comprovante específico exige navegar pastas por data |
| D4 | Cada diretor adapta as planilhas ao próprio estilo | Transição entre diretorias perde histórico e convenções |
| D5 | Cálculo de multa é mental e subjetivo | Inconsistência na aplicação entre membros |
| D6 | Inadimplência consultada ao olhar planilha linha por linha | Cobrança tardia, não sistemática |
| D7 | Não há rastreamento de despesas por evento | Impossível saber se festa junina deu lucro ou prejuízo de verdade |

### 2.4 Volume de operação atual

- Membros: 15-35 (rotaciona por semestre; atualmente 25, semestre anterior 33)
- Transações típicas por mês:
  - ~25 mensalidades recebidas
  - 1-2 pagamentos de coach
  - 0-3 despesas avulsas (viagem, uniforme, inscrição)
  - Eventos: 2-4 por ano (festa junina, halloween, etc)
  - Vendas de produto: volume irregular

### 2.5 Restrições externas

- 90% dos pagamentos chegam por PIX com comprovante em PDF
- Comprovantes hoje estão no OneDrive; migração para Google Drive está alinhada com a migração das planilhas para o Google Sheets
- Não há orçamento para ferramentas pagas (o MVP precisa rodar em serviços gratuitos)

---

## 3. Escopo do MVP

### 3.1 Princípio de escopo

O MVP foca em **eliminar as dores diárias do diretor** (D1, D2, D3, D6 da Seção 2.3). Funcionalidades de análise aprofundada, portal do atleta e automações avançadas ficam para versões posteriores, documentadas no Roadmap (Seção 9).

### 3.2 Dentro do escopo do MVP

| Feature | Dores atendidas | Prioridade |
|---|---|---|
| Dashboard consolidado (caixa do mês, inadimplência, próximos vencimentos) | D1, D6 | Alta |
| Registrar pagamento de mensalidade com upload de comprovante | D2, D3 | Alta |
| Registrar despesa (coach, viagem, uniforme, inscrição) com upload de comprovante | D1, D3 | Alta |
| Lista de cobranças pendentes com cálculo sugerido de multa | D5, D6 | Alta |
| Registrar evento (festa junina, halloween) e receita gerada | D7 | Média |
| Registrar vendas de produtos | D1 | Média |
| Buscar histórico financeiro de um membro específico | D2 | Média |
| Geração automática de linhas de cobrança mensais (lazy) | D6 | Alta |
| Login de diretor/assistentes via email e senha | — | Alta (segurança) |
| Soft delete com capacidade de restaurar | — | Média |

### 3.3 Fora do escopo do MVP (explicitamente)

Itens pensados, mas deliberadamente **adiados**:

- **Portal do atleta** (atleta loga e vê seu próprio status). Adicionar autenticação para ~30 usuários extras aumenta complexidade e exige tela pública.
- **Emissão automática de cobranças por email/WhatsApp.** Requer integração com serviço de mensageria.
- **Dashboard de análise avançada** (gráficos de tendência, projeções, comparação ano-a-ano). Dados serão coletados de forma adequada desde o MVP, mas a análise visual profunda vira feature de v1.1.
- **Exportação de relatório PDF para prestação de contas.** Útil, mas workaround é exportar a planilha direto.
- **Conciliação bancária automática** (comparar extrato com registros).
- **Suporte multi-time.** O código fica preparado (via Repository Pattern), mas o MVP é single-tenant.
- **App mobile nativo.** O web app é responsivo e funciona no navegador do celular.

### 3.4 Critérios de sucesso do MVP

O MVP é considerado bem-sucedido quando:

1. O diretor consegue registrar um pagamento de mensalidade em **menos de 30 segundos** (vs ~2-3 minutos hoje), incluindo upload de comprovante.
2. A pergunta "quem está devendo e quanto?" é respondida em **uma tela**, sem abrir planilhas paralelas.
3. Um diretor substituto recebe apenas o link do app e as credenciais e consegue operar no primeiro dia, sem treinamento presencial.
4. Os dados na planilha ficam estruturados de forma que **qualquer ferramenta de análise** (pandas, Power BI, Metabase) consegue importar sem transformação adicional.

---

## 4. Usuários e fluxos principais

### 4.1 Personas

**Diretor(a) financeiro (usuário primário)**

- Nível técnico: variável. A versão atual do diretor tem conhecimento técnico (é estudante de engenharia de software), mas o sistema precisa funcionar com o próximo diretor, que pode não ter.
- Frequência de uso: diária em períodos de vencimento (dias 5 a 15 do mês), esporádica no resto do mês.
- Contexto de uso: predominantemente desktop (registro de pagamentos em lote, upload de PDFs), ocasionalmente celular (consultas rápidas).
- Objetivos: registrar pagamentos recebidos com rapidez, acompanhar inadimplência, prestar contas à diretoria e ao time.

**Assistente de diretoria (usuário secundário)**

- Nível técnico: normalmente menor que o diretor.
- Frequência: pontual, quando o diretor delega tarefas (ex: pré-evento, fechamento de semestre).
- Objetivos: registrar transações específicas delegadas pelo diretor.
- Restrição: MVP não distingue permissões entre diretor e assistente — ambos têm acesso total. Diferenciação fica para v2.

### 4.2 Fluxos principais

**Fluxo 1 — Registrar mensalidade recebida**

```
1. Atleta paga PIX e envia PDF pelo WhatsApp
2. Diretor abre o app → tela "Registrar Pagamento"
3. Seleciona o membro (dropdown com busca)
4. Seleciona o mês de referência (default: mês corrente)
5. App pré-preenche valor esperado (R$ 55 ou R$ 15 conforme tipo do membro)
6. App alerta se pagamento está em atraso e sugere multa de R$ 7
7. Diretor confirma valor, aplica multa ou não, insere observação (se necessário)
8. Diretor arrasta o PDF para a área de upload
9. Ao clicar "Salvar":
   - App faz upload do PDF ao Google Drive (pasta de comprovantes do ano)
   - App atualiza linha na aba `pagamentos` do Sheets
   - Dashboard é invalidado (cache limpo)
10. Mensagem de confirmação, formulário limpa para o próximo
```

**Fluxo 2 — Consultar inadimplência**

```
1. Diretor abre o app → tela "Cobranças Pendentes"
2. Tabela filtra automaticamente linhas com status=pendente ou parcial
3. Colunas: membro | tipo | mês | valor devido | dias em atraso | ação
4. Ordenação padrão: dias em atraso (decrescente)
5. Diretor pode clicar em linha para registrar pagamento (redireciona para Fluxo 1 pré-preenchido)
```

**Fluxo 3 — Registrar despesa**

```
1. Diretor abre o app → tela "Registrar Despesa"
2. Seleciona categoria (coach, viagem, uniforme, inscrição, evento, outros)
3. Preenche descrição, valor, beneficiário, data
4. Se categoria = "evento", aparece campo extra: "vincular a evento existente?" (dropdown)
5. Upload do comprovante (opcional, mas recomendado)
6. Salvar → escrita na aba `despesas`, upload no Drive
```

**Fluxo 4 — Registrar evento**

```
1. Diretor abre o app → tela "Eventos e Vendas" → aba "Eventos"
2. Botão "Novo evento" → formulário (nome, data, público estimado)
3. Durante/após o evento, diretor edita e preenche receita bruta arrecadada
4. Despesas do evento são registradas no Fluxo 3, vinculando ao id_evento
5. App calcula e exibe lucro líquido automaticamente (receita - despesas vinculadas)
```

**Fluxo 5 — Buscar histórico de um membro**

```
1. Diretor abre o app → tela "Histórico do Membro"
2. Busca por nome no dropdown
3. Tela exibe:
   - Dados cadastrais
   - Tabela com todas as mensalidades (pagas e pendentes)
   - Total pago no semestre/ano
   - Saldo devedor atual
   - Links para comprovantes
```

**Fluxo 6 — Dashboard (tela inicial)**

```
1. Diretor abre o app → tela default é Dashboard
2. Cards principais:
   - Caixa do mês (receitas - despesas do mês corrente)
   - Inadimplência total (soma de valor devido em linhas pendentes/parciais)
   - Próximos vencimentos (cobranças do mês que vencem em ≤ 7 dias)
   - Lucro do último evento
3. Gráfico: evolução do caixa nos últimos 6 meses
4. Lista resumida: últimas 10 transações (entradas e saídas)
```

### 4.3 Fluxos de manutenção (menos frequentes)

- **Início de semestre:** diretor edita a aba `membros` diretamente no Google Sheets, adicionando novos membros e marcando os que saíram como `inativo`. O app reflete automaticamente nas próximas execuções.
- **Alteração de valores (mensalidade, multa):** diretor edita a aba `configuracoes`, sem mexer no código.
- **Correção de erro:** toda tela de listagem tem ação "editar" e "excluir" por linha. Exclusão é soft delete (reversível).

---

## 5. Arquitetura técnica

### 5.1 Visão geral

O sistema é um **web app single-tenant** (serve apenas um time) construído em Python com Streamlit, hospedado gratuitamente no Streamlit Community Cloud. Todos os dados persistem em serviços do Google (Sheets para dados tabulares, Drive para arquivos), o que elimina a necessidade de manter um banco de dados próprio.

```
┌─────────────────────────────────────────────────┐
│  Navegador do diretor/assistente                │
│  (qualquer dispositivo com internet)            │
└──────────────────┬──────────────────────────────┘
                   │ HTTPS
                   ▼
┌─────────────────────────────────────────────────┐
│  Streamlit Community Cloud                      │
│  ├── Código Python (UI + lógica)                │
│  ├── Secrets (credenciais Google, senhas)       │
│  └── Bibliotecas: gspread, google-api-client    │
└─────┬───────────────────────┬───────────────────┘
      │                       │
      ▼                       ▼
┌──────────────┐       ┌───────────────────────┐
│ Google Sheets│       │ Google Drive          │
│ (dados)      │       │ (comprovantes PDF)    │
└──────────────┘       └───────────────────────┘
```

### 5.2 Stack tecnológica

| Camada | Tecnologia | Justificativa |
|---|---|---|
| Linguagem | Python 3.11+ | Preferência do time, ecossistema de dados |
| Framework UI | Streamlit | Frontend gerado automaticamente a partir de Python; sem HTML/CSS/JS |
| Hospedagem | Streamlit Community Cloud | Gratuita, deploy via `git push`, sem manutenção de infraestrutura |
| Armazenamento tabular | Google Sheets (API v4) | Permite conferência e edição manual pelo diretor fora do app |
| Armazenamento de arquivos | Google Drive (API v3) | Integração nativa com Sheets, 15GB grátis |
| Cliente Sheets | `gspread` | Biblioteca mais madura em Python |
| Cliente Drive | `google-api-python-client` | Cliente oficial do Google |
| Autenticação de usuários | Google OIDC via `st.login()` | Login "Entrar com Google" nativo do Streamlit; não armazena senhas |
| Autenticação com Google | Service Account | Conta de serviço com permissão escrita nas planilhas/pasta |
| Versionamento | Git + GitHub (repo público) | Requisito do Streamlit Community Cloud |
| Gerenciador de dependências | `uv` ou `pip` + `requirements.txt` | Padrão Python |

### 5.3 Modelo de autenticação em duas camadas

O sistema opera com duas autenticações independentes que não se cruzam:

**Camada 1 — Usuário → App.** Autenticação exclusivamente via **Google OIDC** (OpenID Connect), usando a API nativa `st.login()` do Streamlit (disponível a partir da versão 1.42). O diretor ou assistente clica em "Entrar com Google", é redirecionado ao Google, autentica com sua conta, e retorna ao app. O app valida se o email retornado está na whitelist de usuários autorizados (armazenada nos secrets do Streamlit Cloud). Nenhuma senha é armazenada pelo app.

**Camada 2 — App → Google APIs.** Uma Service Account (criada no Google Cloud Console) tem permissão de edição nas planilhas e na pasta do Drive específicas do projeto. O app usa a chave JSON dessa conta — armazenada nos secrets do Streamlit Cloud, nunca no código — para ler e escrever dados.

As duas camadas são independentes: o login do diretor usa **a conta dele** (autenticação); o acesso às planilhas usa **a Service Account** (autorização de dados). A Service Account nunca é usada como identidade do usuário.

### 5.4 Padrão de arquitetura do código (Repository Pattern)

O código é organizado em camadas para isolar o acesso a dados da lógica de negócio e da UI. Isso permite trocar o Google Sheets por um banco relacional no futuro (Postgres/Supabase) sem reescrever o app.

```
app/
├── streamlit_app.py          # Entry point
├── pages/                    # Uma tela por arquivo (Streamlit multipage)
│   ├── 1_Dashboard.py
│   ├── 2_Registrar_Pagamento.py
│   ├── 3_Registrar_Despesa.py
│   ├── 4_Cobrancas_Pendentes.py
│   ├── 5_Eventos_e_Vendas.py
│   └── 6_Historico_Membro.py
├── repositories/             # Acesso a dados (interface entre app e Sheets)
│   ├── base.py               # Classes abstratas
│   ├── membros_repo.py
│   ├── pagamentos_repo.py
│   ├── despesas_repo.py
│   └── comprovantes_repo.py  # Upload pro Drive
├── services/                 # Regras de negócio
│   ├── calculo_dividas.py    # Lógica de multa, inadimplência
│   ├── dashboard_service.py  # Agregações para o dashboard
│   └── upload_service.py     # Orquestra upload de comprovante
├── auth.py                   # Login do diretor
├── config.py                 # Configurações e constantes
└── requirements.txt
```

**Responsabilidades de cada camada:**

- `pages/` — Só UI. Desenha formulários, tabelas, gráficos. Nunca fala com Google diretamente.
- `services/` — Lógica de negócio. Calcula dívida, aplica multa, gera métricas do dashboard. Não sabe que os dados vêm de Sheets.
- `repositories/` — Acesso a dados. Converte linhas da planilha em objetos Python (`Pagamento`, `Membro`) e vice-versa. Se um dia trocar para Postgres, só essa camada muda.

### 5.5 Modelo de execução do Streamlit

O Streamlit re-executa o script inteiro a cada interação do usuário (clique de botão, mudança de campo). Para evitar chamadas repetidas à API do Google (que é lenta e tem rate limit), serão usados dois recursos do framework:

- **`@st.cache_data`** — memoriza o resultado de leituras do Sheets por N segundos (ex: lista de membros, histórico de pagamentos). Invalidado manualmente após qualquer escrita.
- **`st.session_state`** — mantém estado entre re-execuções do script (ex: filtros aplicados, mês selecionado).

### 5.6 Rate limits e performance

A API do Google Sheets tem limite de 60 leituras/minuto por usuário. Estratégia para evitar travamentos:

1. Cache agressivo de leituras (`@st.cache_data` com TTL de 5 minutos)
2. Leitura em lote: uma única chamada que baixa a aba inteira, em vez de leitura célula a célula
3. Escritas agrupadas quando possível (`batch_update` do gspread)

Para o volume previsto (1-3 usuários, ~30 membros, ~50 transações/mês), esses limites não serão atingidos.

### 5.7 Diretrizes de implementação

- Todo timestamp é armazenado em UTC na planilha, exibido em horário de Brasília na UI
- Valores monetários armazenados como número (não string), formatados como moeda só na exibição
- IDs de pagamento/despesa gerados como UUID para evitar colisões
- Logs de erro enviados para `st.error()` na UI e registrados em `logging` para debug
- Código versionado em repositório GitHub **público** (requisito do Streamlit Cloud). Dados sensíveis (credenciais, senhas) ficam exclusivamente nos secrets do Streamlit, nunca no Git.

---

## 6. Modelo de dados (estrutura do Google Sheets)

### 6.1 Princípios de modelagem

O modelo segue o padrão **"tidy data"** (forma longa): cada linha é uma observação única, cada coluna é uma variável. Isso garante compatibilidade direta com ferramentas de análise (pandas, Power BI, SQL, Metabase) no futuro, sem pré-processamento.

**Decisões estruturais:**

- **Soft delete em todas as abas transacionais.** Em vez de apagar linhas, o campo `ativo` (SIM/NÃO) marca registros excluídos. O app filtra `ativo=SIM` por padrão, mas o histórico permanece para auditoria e prestação de contas.
- **IDs como UUID.** Gerados pelo app, não dependem de numeração sequencial (evita colisão se duas pessoas criarem registros simultaneamente).
- **Valores monetários como número**, não string. Formatação "R$ 55,00" só na exibição.
- **Datas no formato ISO 8601** (`YYYY-MM-DD`). Google Sheets reconhece como data, e parsers Python/SQL também.
- **Configurações parametrizadas.** Valor de mensalidade, multa, dia de vencimento ficam na aba `configuracoes`, não hardcoded no código.

### 6.2 Abas da planilha

#### Aba `membros`

Cadastro de atletas e associados. O diretor edita manualmente (diretamente na planilha) no início de cada semestre.

| Coluna | Tipo | Descrição |
|---|---|---|
| `id_membro` | string | ID único (ex: `M001`, `M002`). Preenchido manualmente ou por fórmula |
| `nome` | string | Nome completo |
| `tipo` | enum | `atleta` ou `associado` |
| `email` | string | Email de contato |
| `telefone` | string | Telefone (opcional) |
| `semestre_entrada` | string | Formato `YYYY-S` (ex: `2026-1`) |
| `status` | enum | `ativo` ou `inativo` (membros que saíram mas têm histórico) |
| `observacoes` | string | Texto livre |

**Regra:** membros com `status=inativo` não geram novas cobranças mensais, mas aparecem em consultas históricas.

#### Aba `pagamentos`

Mensalidades (cobranças e recebimentos). Uma linha por membro ativo por mês de referência.

| Coluna | Tipo | Descrição |
|---|---|---|
| `id_pagamento` | UUID | Gerado pelo app |
| `id_membro` | string | FK para `membros` |
| `mes_referencia` | string | Formato `YYYY-MM` (ex: `2026-01`) |
| `data_vencimento` | date | Dia 10 do mês seguinte (configurável) |
| `data_pagamento` | date ou vazio | Data do último recebimento (null se pendente) |
| `valor_original` | number | R$ 55,00 para atleta ou R$ 15,00 para associado, conforme `configuracoes` |
| `multa` | number | R$ 7,00 se aplicada pelo diretor; 0 caso contrário |
| `valor_pago` | number | Total acumulado recebido (0 se nada pago) |
| `status` | enum | `pendente`, `parcial`, `pago`, `cancelado` |
| `link_comprovante` | URL ou vazio | Link do Drive (último comprovante) |
| `observacoes` | string | Obrigatório se `status=parcial` ou se foi aplicada multa |
| `ativo` | boolean | Soft delete |

**Regras de negócio:**

- `status=parcial` quando `0 < valor_pago < valor_original + multa`
- `status=pago` quando `valor_pago >= valor_original + multa`
- Pagamento parcial adicional **soma** em `valor_pago` (mesma linha, sem criar nova linha)
- `data_pagamento` sempre reflete a última data de recebimento
- Multa é **sugerida** pelo app quando `hoje > data_vencimento` e não há aviso prévio registrado, mas só aplicada mediante confirmação do diretor

#### Aba `despesas`

Saídas de caixa (coach, viagem, uniforme, etc).

| Coluna | Tipo | Descrição |
|---|---|---|
| `id_despesa` | UUID | Gerado pelo app |
| `data` | date | Data da despesa |
| `categoria` | enum | `coach`, `viagem_campeonato`, `uniforme`, `inscricao_campeonato`, `evento`, `outros` |
| `descricao` | string | Texto curto (ex: "Passagem João SP-BH") |
| `valor` | number | Valor pago |
| `beneficiario` | string | Quem recebeu (nome do coach, empresa, etc) |
| `link_comprovante` | URL ou vazio | Link do Drive |
| `id_evento_relacionado` | UUID ou vazio | FK para `eventos` quando a despesa for parte de um evento |
| `observacoes` | string | Texto livre |
| `ativo` | boolean | Soft delete |

#### Aba `eventos`

Eventos organizados pelo time (festa junina, halloween, etc). Agregado de receitas e despesas vinculadas.

| Coluna | Tipo | Descrição |
|---|---|---|
| `id_evento` | UUID | Gerado pelo app |
| `nome` | string | Ex: "Festa Junina 2026" |
| `data` | date | Data do evento |
| `receita_bruta` | number | Total arrecadado (ingressos, bar, rifa) |
| `publico_estimado` | number | Quantidade de pessoas (opcional, útil pra análise) |
| `observacoes` | string | Texto livre |
| `ativo` | boolean | Soft delete |

**Regra:** despesas do evento são registradas na aba `despesas` com `id_evento_relacionado` preenchido. O lucro líquido é calculado dinamicamente (`receita_bruta - soma das despesas vinculadas`), não armazenado.

#### Aba `vendas_produtos`

Vendas avulsas de produtos (camisetas, canecas, etc).

| Coluna | Tipo | Descrição |
|---|---|---|
| `id_venda` | UUID | Gerado pelo app |
| `data` | date | Data da venda |
| `produto` | string | Nome do produto |
| `quantidade` | integer | Unidades vendidas |
| `valor_unitario` | number | Preço por unidade |
| `valor_total` | number | `quantidade * valor_unitario` (redundante mas útil para leitura direta) |
| `comprador` | string | Opcional |
| `link_comprovante` | URL ou vazio | Link do Drive |
| `observacoes` | string | Texto livre |
| `ativo` | boolean | Soft delete |

#### Aba `configuracoes`

Parâmetros editáveis sem alterar código.

| chave | valor | descricao |
|---|---|---|
| `valor_mensalidade_atleta` | 55.00 | Mensalidade atleta |
| `valor_mensalidade_associado` | 15.00 | Mensalidade associado |
| `valor_multa_atraso` | 7.00 | Multa aplicada quando pagamento em atraso sem aviso |
| `dia_vencimento` | 10 | Dia do mês de vencimento da mensalidade do mês anterior |
| `nome_time` | "Nome do Time" | Exibido no header do app |

### 6.3 Geração de linhas pendentes (lazy generation)

Não há job agendado. A cada sessão do diretor, o app executa a verificação:

```
para cada membro com status='ativo':
    se não existe linha em `pagamentos` para (id_membro, mes_corrente):
        criar linha com:
            - id_pagamento = novo UUID
            - mes_referencia = mes_corrente (YYYY-MM)
            - data_vencimento = dia 10 do mês seguinte
            - valor_original = configuracoes[f'valor_mensalidade_{tipo}']
            - status = 'pendente'
            - valor_pago = 0
            - ativo = True
```

A operação é idempotente: se já existe linha, nada acontece. Executada uma vez por sessão (com cache de 1h em `st.session_state`) para evitar chamadas repetidas.

### 6.4 Relacionamentos entre abas

```
membros (1) ────< (N) pagamentos
eventos (1) ────< (N) despesas  [despesas.id_evento_relacionado]
```

Não há foreign keys reais no Sheets — a integridade é garantida pela camada de `repositories/` do app (valida antes de inserir).

### 6.5 Estrutura do Google Drive

Pasta raiz compartilhada com a Service Account, organizada por **ano → tipo → entidade**. Essa estrutura facilita auditoria humana direta no Drive (sem depender do app) e simplifica arquivamento quando membros/eventos saem do ciclo ativo.

```
Financeiro-Furiosos-Cheer/
├── 2026/
│   ├── mensalidades/
│   │   ├── M001-joao-silva/
│   │   │   ├── 2026-01.pdf
│   │   │   ├── 2026-02.pdf
│   │   │   └── ...
│   │   ├── M002-maria-santos/
│   │   │   └── ...
│   │   └── ...
│   ├── despesas/
│   │   ├── coach/
│   │   ├── viagem-campeonato/
│   │   ├── uniforme/
│   │   ├── inscricao-campeonato/
│   │   └── outros/
│   ├── eventos/
│   │   ├── festa-junina-2026/
│   │   └── halloween-2026/
│   └── vendas/
│       ├── camisetas/
│       └── outros-produtos/
└── 2027/
    └── ...
```

**Convenção de nomenclatura:**

- **Pastas de membro:** `{id_membro}-{nome-normalizado}` (ex: `M001-joao-silva`). O ID garante unicidade (evita conflito em caso de homônimos ou troca de nome); o nome é puramente para legibilidade humana.
- **Nomes de arquivo de mensalidade:** `{mes_referencia}.pdf` (ex: `2026-01.pdf`). Se houver múltiplos pagamentos no mesmo mês (parcial + complemento), o app adiciona sufixo: `2026-01-part2.pdf`.
- **Nomes de arquivo de despesa:** `{data}-{descricao-curta}.pdf` (ex: `2026-03-15-passagem-joao-sp.pdf`).
- **Pastas de evento:** `{nome-evento}-{ano}` (ex: `festa-junina-2026`).

**Comportamento do app:**

- Ao registrar pagamento/despesa/venda, o app verifica se a pasta de destino existe; se não, cria automaticamente (via API do Drive).
- A camada `repositories/comprovantes_repo.py` encapsula essa lógica — o resto do código só chama `upload_comprovante(tipo, entidade_id, arquivo)`.
- O campo `link_comprovante` na planilha guarda a URL de visualização do arquivo no Drive (não é público; requer autenticação).

**Benefícios dessa estrutura:**

- Auditor/presidente consegue navegar no Drive direto e ver todos os comprovantes de um membro, evento ou categoria sem precisar do app.
- Arquivamento semestral/anual vira trivial: ao final de 2026, a pasta `2026/` pode ser movida para um "cofre" sem afetar dados correntes.
- Se um membro sai do time, sua pasta guarda todo o histórico — simples de baixar/compartilhar com ele se necessário.

**Custo desta estrutura:** lógica adicional em `comprovantes_repo.py` para garantir criação de pastas on-demand. Em troca: drive navegável por humanos + auditoria independente do app.

### 6.6 Migração futura (saindo do Sheets)

Se um dia o sistema migrar para um banco relacional (Postgres/Supabase), o esquema já está próximo do normalizado. Cada aba vira uma tabela, as FKs passam a ser reais, e a camada `repositories/` do app é reescrita. As telas e regras de negócio não mudam.

---

## 7. Telas e funcionalidades

O app é um Streamlit multipage. Cada tela vira um arquivo em `pages/`. A ordem dos arquivos (prefixo numérico) controla a ordem no menu lateral.

### 7.1 Dashboard (tela inicial)

**Arquivo:** `pages/1_Dashboard.py`

**Componentes:**

- **Header:** saudação ao usuário logado ("Olá, [nome]"), seletor de mês/ano de referência (default: mês corrente)
- **KPIs principais** (4 cards em linha):
  - Caixa do mês (entradas − saídas do mês selecionado). Cor verde se positivo, vermelha se negativo.
  - Inadimplência total (soma de valor devido nas cobranças em aberto de todos os meses)
  - Vencimentos nos próximos 7 dias (contagem + valor total)
  - Saldo acumulado do ano (entradas − saídas do ano corrente)
- **Gráfico:** linha da evolução do caixa nos últimos 6 meses (`st.line_chart`)
- **Gráfico secundário:** pizza/barra da distribuição de despesas por categoria no mês
- **Tabela:** últimas 10 transações (mistura de receitas e despesas), ordenada por data desc
- **Alertas:** mensagens destacadas se inadimplência > X% dos membros, ou se há comprovantes não anexados

### 7.2 Registrar pagamento

**Arquivo:** `pages/2_Registrar_Pagamento.py`

**Formulário:**

- Membro (dropdown com busca por nome, filtrado a `status=ativo`)
- Mês de referência (default: mês corrente; dropdown com últimos 12 meses)
- Valor esperado (pré-preenchido, ajustável)
- Aplicar multa de R$ 7 (checkbox; ativado automaticamente se `hoje > data_vencimento`, mas desmarcável)
- Valor pago (número; default igual ao valor esperado + multa se marcada)
- Data do pagamento (date picker; default: hoje)
- Observações (obrigatório se pagamento parcial; livre caso contrário)
- Comprovante (upload de PDF, PNG ou JPG; drag-and-drop)
- Botão "Salvar pagamento"

**Após salvar:**

- Se pagamento completa o valor → status vai para `pago`
- Se valor pago < esperado → status `parcial`, força observação
- Toast de confirmação, formulário reseta
- Cache do dashboard invalidado

### 7.3 Cobranças pendentes

**Arquivo:** `pages/3_Cobrancas_Pendentes.py`

**Filtros (no topo da tela, em colunas):**

- **Busca por nome:** campo de texto com busca parcial e case-insensitive (ex: digitar "jo" encontra "João", "Joana", "Ajoelmo"). Implementado via `st.text_input` + filtro em pandas.
- **Mês de referência:** dropdown (default: todos os meses em aberto)
- **Tipo de membro:** radio (atleta / associado / todos)
- **Status:** multi-select (pendente / parcial)
- **Faixa de atraso:** radio (todos / em dia / atrasado / atrasado > 7 dias)

**Tabela interativa (`st.dataframe`):**

- Colunas: Membro | Tipo | Mês referência | Valor devido | Dias em atraso | Última observação | Ações
- Ordenação padrão por dias em atraso (decrescente)
- Ordenação alternativa: por nome, por valor, por mês
- Coloração de linha: verde se no prazo, amarelo se < 7 dias em atraso, vermelho se ≥ 7 dias
- Paginação automática do Streamlit (25 linhas por página)

**Ações disponíveis:**

- Ao clicar em uma linha → botão "Registrar pagamento desta cobrança" (leva para tela 7.2 com campos pré-preenchidos via query params)
- Botão "Exportar filtro atual em CSV" (útil para diretor mandar lista de inadimplentes por WhatsApp pra presidência)

**Métricas no topo da tela:**

- Total em aberto (R$ X,XX) considerando os filtros aplicados
- Número de cobranças filtradas
- Número de membros distintos com pendência

### 7.4 Registrar despesa

**Arquivo:** `pages/4_Registrar_Despesa.py`

**Formulário:**

- Categoria (dropdown: coach, viagem_campeonato, uniforme, inscricao_campeonato, evento, outros)
- Descrição (texto curto)
- Valor
- Beneficiário (texto; opcional)
- Data
- Se categoria = "evento" → dropdown "Vincular a evento" (mostra eventos ativos)
- Comprovante (upload opcional)
- Observações
- Botão "Salvar despesa"

### 7.5 Eventos e vendas

**Arquivo:** `pages/5_Eventos_e_Vendas.py`

**Tela dividida em duas abas (`st.tabs`):**

**Aba "Eventos":**
- Lista de eventos (tabela): nome, data, receita, total de despesas vinculadas, lucro líquido, ações
- Botão "Novo evento" abre modal/expander com formulário
- Ao clicar em um evento → detalhamento com lista de despesas vinculadas

**Aba "Vendas de produtos":**
- Tabela de vendas: data, produto, quantidade, valor total
- Formulário rápido no topo para adicionar nova venda
- Métrica: total vendido no mês/ano

### 7.6 Histórico do membro

**Arquivo:** `pages/6_Historico_Membro.py`

**Componentes:**

- Dropdown de busca de membro
- Após selecionar:
  - Card com dados cadastrais
  - Tabela cronológica de todas as mensalidades (todas as linhas em `pagamentos` do membro)
  - Resumo: total pago no ano, saldo devedor, quantidade de atrasos históricos
  - Links clicáveis para comprovantes no Drive
  - Botão "Exportar histórico CSV" (download local)

### 7.7 Comportamentos globais da UI

- **Sidebar:** navegação entre telas + botão "Sair" + info do usuário logado
- **Tema:** Streamlit default (claro), com branding mínimo (nome do time no header)
- **Formatação:**
  - Valores: `R$ 1.234,56` (pt-BR)
  - Datas: `DD/MM/YYYY` na exibição (ISO no armazenamento)
  - Números: separador de milhar ponto, decimal vírgula
- **Feedback ao usuário:** `st.success` para sucesso, `st.error` para erro, `st.warning` para atenção, `st.info` para neutro
- **Estado de carregamento:** `st.spinner` em todas as operações que tocam o Google (uploads, escritas em lote)
- **Validação:** formulários só habilitam o botão "Salvar" quando campos obrigatórios estão preenchidos

---

## 8. Segurança e autenticação

### 8.1 Modelo de ameaças

O app trata dados **financeiros não-críticos** (mensalidades de baixo valor, comprovantes de PIX, registros de despesa). Não processa pagamentos, não tem acesso a contas bancárias, não armazena senhas de terceiros.

Ameaças relevantes:

| # | Ameaça | Probabilidade | Impacto | Mitigação |
|---|---|---|---|---|
| A1 | Pessoa não autorizada acessa a URL do app | Alta | Médio | Google OIDC + whitelist de emails (8.2) |
| A2 | Credenciais do Google APIs vazam publicamente | Baixa | Alto | Secrets no Streamlit Cloud (8.3) |
| A3 | Diretor perde acesso à conta Google e ninguém consegue entrar | Média | Médio | Múltiplos emails admin na whitelist (8.4) |
| A4 | Ex-diretor continua com acesso após troca de diretoria | Alta | Alto | Remoção de email da whitelist revoga acesso imediato (8.4) |
| A5 | Registro incorreto ou malicioso (erro ou má-fé) | Média | Baixo | Soft delete + auditoria (8.5) |
| A6 | Vazamento público do repositório GitHub | Média | Baixo se bem configurado | Nenhuma credencial no código (8.3) |

### 8.2 Autenticação de usuários

- **Mecanismo:** Google OIDC nativo do Streamlit (`st.login()`, disponível a partir do Streamlit 1.42)
- **Fluxo:** usuário clica "Entrar com Google" → redirecionado ao Google → autentica com sua conta Google → retorna ao app com identidade validada
- **Whitelist de emails:** o app só autoriza emails previamente cadastrados nos secrets do Streamlit Cloud; emails não listados veem tela de "acesso negado" após login
- **Senhas:** o app **nunca** armazena senhas (problema do Google)
- **Sessão:** gerenciada por cookie seguro criado pelo Streamlit, duração padrão de 30 dias (configurável)
- **Logout manual:** disponível na sidebar via `st.logout()`

**Configuração necessária (uma única vez no Sprint 0):**

1. Criar OAuth 2.0 Client no Google Cloud Console (mesmo projeto da Service Account)
2. Adicionar redirect URI apontando para o app no Streamlit Cloud
3. Copiar `client_id` e `client_secret` para os secrets do Streamlit (`[auth]` section)
4. Gerar `cookie_secret` aleatório de ≥32 bytes (para assinar o cookie de sessão)

**Roles iniciais:**

- `admin`: diretor financeiro (acesso total)
- `assistant`: assistentes de diretoria (acesso total no MVP; diferenciação futura)

A distinção entre roles é armazenada em um dicionário nos secrets (ex: `{"diretor@email.com": "admin", "assist@email.com": "assistant"}`).

### 8.3 Autenticação com Google APIs

- **Service Account** criada no Google Cloud Console (conta isolada, não pessoal)
- Escopos mínimos concedidos: `sheets.v4` (leitura/escrita) e `drive.v3` (escrita em pasta específica)
- A planilha e a pasta do Drive são **compartilhadas com o email da Service Account** (como se fosse um colaborador)
- Chave JSON da Service Account armazenada nos secrets do Streamlit Cloud (`st.secrets`)
- **Nunca commitar a chave no Git.** `.gitignore` bloqueia qualquer arquivo `*.json` de credenciais
- Revogação: se a chave for exposta, basta gerar nova chave no Google Cloud Console e atualizar os secrets

### 8.4 Ciclo de vida de acesso

**Onboarding de novo assistente/diretor:**

1. Diretor atual adiciona o email Google do novo usuário na whitelist de emails nos secrets do Streamlit Cloud
2. Redeploy automático do app (Streamlit Cloud detecta mudança em secrets)
3. Novo usuário já pode acessar: clica "Entrar com Google" e entra

**Off-boarding ao final do mandato:**

1. Diretor atual remove o email do ex-diretor/assistente da whitelist nos secrets
2. Acesso revogado imediatamente no próximo login do ex-usuário (whitelist é checada a cada sessão)
3. Para extra segurança em troca de diretoria, opcionalmente gera nova chave da Service Account (invalida qualquer cópia local que possa ter sido feita)

Essa abordagem elimina várias classes de problema que existiriam com senhas próprias: não há senhas esquecidas, não há senhas reutilizadas, não há senhas vazadas. Revogação é atômica.

### 8.5 Auditoria e integridade dos dados

- **Soft delete obrigatório:** nenhuma linha é fisicamente removida; o campo `ativo` controla visibilidade
- **Campos de auditoria em todas as tabelas:** `criado_em`, `criado_por` (email do usuário logado), `atualizado_em`, `atualizado_por`
- **Log de ações sensíveis:** escritas e exclusões geram entrada em uma aba `auditoria` (quem, quando, o que) — escopo para v1.1, não MVP

### 8.6 Exposição pública dos comprovantes

- Arquivos no Drive **não são públicos por default**
- O campo `link_comprovante` armazena um link que requer login Google para abrir, com permissão concedida apenas à Service Account e aos usuários do app
- Alternativa (definir na implementação): gerar link de visualização temporário via API quando o diretor clicar, sem tornar o arquivo público

### 8.7 Repositório do código

- GitHub **público** (requisito do Streamlit Community Cloud gratuito)
- Nada sensível no código:
  - Credenciais: apenas em `st.secrets` (não versionado)
  - IDs da planilha e pasta do Drive: podem ficar no código (são opacos, sem valor sem as credenciais)
- LICENSE: MIT ou similar (código livre, só os dados são privados)

---

## 9. Roadmap

### 9.1 Fases de desenvolvimento (MVP)

Divido em **sprints** de ~1 semana cada. Ordem escolhida para permitir uso incremental (mesmo antes de terminar tudo, partes já são úteis).

**Sprint 0 — Setup (estimativa: 1-2 dias)**

- Criar projeto Google Cloud
- Criar Service Account para acesso às APIs de Sheets e Drive
- Criar OAuth 2.0 Client para login de usuários via Google OIDC
- Criar planilha mestre no Google Sheets com as 6 abas da Seção 6.2 (cabeçalhos)
- Criar pasta no Google Drive para comprovantes
- Compartilhar planilha e pasta com o email da Service Account
- Criar repositório GitHub público
- Setup Streamlit Cloud (conectar ao repo)
- Configurar secrets do Streamlit: chave da Service Account, credenciais OAuth, whitelist de emails autorizados
- Estrutura inicial de pastas (Seção 5.4)

**Sprint 1 — Fundação (estimativa: 3-5 dias)**

- Módulo `auth.py`: integração com `st.login()` do Streamlit e validação de whitelist
- Módulo `config.py`: leitura de secrets e conexão com Google APIs via Service Account
- `repositories/base.py`: interface abstrata
- `repositories/membros_repo.py`: leitura da aba `membros`
- Tela placeholder "Home" mostrando "Olá, [nome]" (obtido do Google) e lista de membros (validação end-to-end: login Google → whitelist → leitura do Sheets → UI)

**Sprint 2 — Fluxo de pagamentos (estimativa: 5-7 dias)**

- `repositories/pagamentos_repo.py` + `repositories/configuracoes_repo.py`
- `services/calculo_dividas.py`: geração lazy de cobranças, cálculo de multa
- `services/upload_service.py`: upload ao Drive
- Tela **Registrar Pagamento** (7.2)
- Tela **Cobranças Pendentes** (7.3)

**Sprint 3 — Fluxo de despesas e eventos (estimativa: 4-5 dias)**

- `repositories/despesas_repo.py`, `repositories/eventos_repo.py`, `repositories/vendas_repo.py`
- Tela **Registrar Despesa** (7.4)
- Tela **Eventos e Vendas** (7.5)

**Sprint 4 — Dashboard e histórico (estimativa: 3-4 dias)**

- `services/dashboard_service.py`: agregações (caixa do mês, inadimplência, etc)
- Tela **Dashboard** (7.1)
- Tela **Histórico do Membro** (7.6)

**Sprint 5 — Polimento e deploy final (estimativa: 2-3 dias)**

- Revisão de UX (mensagens de erro, loading states, validações)
- Testes manuais de ponta a ponta
- Criação de usuário-admin inicial
- Documentação no README.md (como instalar, operar, fazer transição)
- Apresentação à diretoria

**Total estimado: 18-26 dias de desenvolvimento**, compatível com desenvolvimento em paralelo à faculdade (tempo parcial).

### 9.2 Versão 1.1 (pós-MVP, após uso real por 1-2 meses)

Ajustes e recursos que ganham prioridade após feedback real:

- Dashboard com gráficos avançados (tendências, projeções)
- Exportação de relatório em PDF para prestação de contas
- Log de auditoria em aba `auditoria`
- Notificações no app (inadimplentes destacados ao logar)
- Melhorias de UX conforme dores identificadas pelo uso real

### 9.3 Versão 2 (longo prazo)

Features que mudam a natureza do sistema:

- **Portal do atleta:** cada atleta loga e vê seu próprio status. Requer autenticação expandida e tela pública.
- **Diferenciação de permissões** entre diretor e assistentes
- **Envio automatizado de cobrança** via email/WhatsApp (API Z-API, WhatsApp Business, ou email simples)
- **Migração do Sheets para banco relacional** (Supabase/Postgres) se volume ou complexidade crescer significativamente
- **App mobile nativo** (se web responsivo se mostrar insuficiente)
- **Suporte multi-time** (transformar em SaaS para outros times universitários)

### 9.4 Riscos e mitigações

| Risco | Probabilidade | Mitigação |
|---|---|---|
| Atraso por sobrecarga acadêmica | Alta | Entregas por sprint permitem pausa sem perder tudo |
| Rate limits do Google Sheets atrapalham uso | Baixa | Cache agressivo + testes de carga no Sprint 5 |
| Transição de diretoria antes do MVP pronto | Média | Planilhas atuais continuam funcionando; app é aditivo |
| Streamlit Community Cloud descontinua plano gratuito | Baixa | Código é portável; migrar para Render ou Railway em < 1 dia |
| Novo diretor resiste a adotar o app | Média | Envolver futuro diretor na fase de testes do Sprint 5 |

---

## 10. Apêndice — decisões tomadas na discussão

Registro das decisões arquiteturais e de produto que foram debatidas explicitamente durante a fase de contextualização, para referência futura (inclusive para o próximo diretor entender "por que foi assim").

### 10.1 Por que web app e não desktop

Analisado em detalhe: desktop foi considerado pela premissa "funciona offline, sem custo de servidor". Descartado por três motivos:

1. **Custo de servidor é zero no web path escolhido** (Streamlit Community Cloud é gratuito para repositórios públicos)
2. **App desktop expõe credenciais:** executáveis gerados com PyInstaller podem ser descompilados trivialmente, e qualquer chave empacotada fica vulnerável
3. **Distribuição e atualização são dolorosas:** antivírus bloqueiam .exe não assinados, atualizações exigem redistribuição manual

Conclusão: web é mais seguro, mais barato de manter, e mais fácil de passar para o próximo diretor (só envia o link).

### 10.2 Por que Google Sheets e não banco relacional

Analisado: Sheets tem limitações (rate limits, menor performance, análise mais limitada). Escolhido ainda assim porque:

1. Diretoria já está migrando para o ecossistema Google (Sheets + Drive)
2. Permite **inspeção e edição manual** da planilha em caso de bug ou correção emergencial
3. Elimina dependência de conta paga em serviço de banco
4. Código estruturado com Repository Pattern (Seção 5.4) permite migrar para Postgres no futuro sem reescrever o app

### 10.3 Por que pagamento parcial na mesma linha (Opção A)

Analisado: alternativa era criar linhas separadas para cada recebimento (Opção B, rastreamento completo). Escolhida Opção A porque:

- Pagamento parcial é **exceção**, não regra no fluxo do time
- Cálculo de dívida vira trivial (`valor_original - valor_pago`)
- Análise temporal ainda é viável pelo campo `data_pagamento`
- Migração para Opção B é sempre possível no futuro se parciais virarem comuns

### 10.4 Por que geração lazy de cobranças mensais

Analisado: alternativas eram (a) job agendado externo e (b) botão manual pelo diretor. Escolhida **lazy generation** porque:

- Não depende de infraestrutura extra (Streamlit Cloud não tem agendador nativo)
- Transparente para o diretor (nunca precisa "lembrar" de gerar cobranças)
- Verificação é rápida e cacheada por sessão
- Implementação trivial em comparação às alternativas

### 10.5 Por que MVP sem portal do atleta

Analisado: valor é claro (tira carga do diretor em responder "quanto eu devo?"). Adiado porque:

- Aumenta complexidade de autenticação (de 2-3 usuários para ~30)
- Exige refinamento de permissões (atleta vê só a própria linha)
- Exige cuidado com exposição pública
- MVP entregue mais rápido sem isso

### 10.6 Por que autenticação apenas via Google (e não email/senha)

Originalmente planejado usar `streamlit-authenticator` com hash bcrypt de senhas próprias. Trocado para Google OIDC (`st.login()` nativo do Streamlit) porque:

1. **Elimina responsabilidade de armazenar senhas.** Não há hashes para vazar, não há senhas reutilizadas do usuário comprometendo outros sistemas.
2. **Off-boarding atômico.** Revogar acesso vira apenas "remover email da whitelist"; não exige redefinição de senhas ou redeploy elaborado.
3. **Experiência do usuário superior.** "Entrar com Google" é familiar, não exige criação de credencial nova.
4. **Streamlit 1.42+ suporta nativamente** — menos dependências de terceiros para manter.
5. **Diretores e assistentes já têm conta Google** — seja pessoal, seja da faculdade. Nenhuma conta nova precisa ser criada.

Trade-off: exige conta Google válida para acessar. Não é restrição real no contexto (100% dos usuários já têm).

### 10.7 Por que estrutura de pastas organizada por entidade no Drive

Originalmente planejado estrutura simplificada (uma pasta por tipo, arquivos identificados por UUID). Trocado para estrutura navegável por entidade (membro/evento/produto) porque:

1. **Facilita auditoria humana.** Presidente ou auditor pode navegar direto no Drive sem depender do app.
2. **Simplifica arquivamento.** Ao fim do ano, toda a estrutura anual pode ser movida em bloco.
3. **Histórico de um membro é uma pasta.** Se alguém sai do time, baixar/compartilhar o histórico dele vira trivial.
4. **Custo adicional de implementação é baixo.** Apenas a camada `comprovantes_repo.py` lida com criação dinâmica de pastas; o resto do código não muda.

---

**Sobre este documento:**

Este PRD foi co-autorado pelo diretor financeiro do Furiosos Cheer em abril/2026. A fase de contextualização levou 8 rodadas de perguntas antes da redação, garantindo que cada decisão tenha justificativa rastreável. Atualizações futuras devem preservar o formato e registrar no Apêndice qualquer mudança de rumo.
