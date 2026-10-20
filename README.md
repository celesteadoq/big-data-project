# 📊 Análise Integrada de Trânsito e Mortalidade no Brasil

![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-ETL-150458?logo=pandas&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)
![MinIO](https://img.shields.io/badge/MinIO-S3%20Data%20Lake-C72E49?logo=minio&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-IaC-7B42BC?logo=terraform&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Containers-2496ED?logo=docker&logoColor=white)

Solução completa de **Engenharia de Dados** para ingestão, tratamento, modelagem, carga relacional e provisionamento de infraestrutura como código (IaC) a partir de três bases públicas oficiais do governo brasileiro: acidentes rodoviários (**PRF**), mortalidade (**SIM/DATASUS**) e indicadores de óbitos no trânsito (**MGDI / Ministério da Saúde**).

---

## Sumário

- [Visão Geral](#visão-geral)
- [Arquitetura](#arquitetura)
- [Estrutura do Repositório](#estrutura-do-repositório)
- [1. Dados Utilizados](#1-dados-utilizados)
- [2. Tratamento Realizado (ETL)](#2-tratamento-realizado-etl)
- [3. Modelagem dos Dados](#3-modelagem-dos-dados)
- [4. Infraestrutura como Código (IaC)](#4-infraestrutura-como-código-iac)
- [5. Justificativa das Escolhas Tecnológicas](#5-justificativa-das-escolhas-tecnológicas)
- [6. Guia de Execução e Reprodução](#6-guia-de-execução-e-reprodução)
- [7. Exemplos de Consultas SQL](#7-exemplos-de-consultas-sql)
- [8. Solução de Problemas](#8-solução-de-problemas)
- [9. Segurança](#9-segurança)
- [10. Próximos Passos](#10-próximos-passos)
- [Licença e Autoria](#licença-e-autoria)

---

## Visão Geral

O projeto responde a uma pergunta central: **como integrar fontes heterogêneas de dados de trânsito e saúde pública em uma base analítica confiável e reproduzível?**

Para isso, a solução:

1. **Ingere** arquivos CSV brutos com problemas reais de qualidade (encodings mistos, metadados no cabeçalho, valores ausentes representados por símbolos).
2. **Trata** e padroniza os dados com scripts Python, preservando os arquivos originais.
3. **Modela** os dados em tabelas relacionais prontas para análise.
4. **Provisiona** a infraestrutura (PostgreSQL + MinIO) de forma declarativa com Terraform e Docker.
5. **Carrega** os dados tratados no PostgreSQL de maneira automatizada.

---

## Arquitetura

O projeto adota **armazenamento em camadas** (Data Lake + Relacional), no padrão Bronze / Silver / Gold:

```text
[Dados Brutos / Bronze]      [Dados Tratados / Silver]      [Camada Analítica / Gold]
 data/versao.original/  ──>   data/versao.resultado/   ──>   PostgreSQL & MinIO S3
 (CSVs brutos imutáveis)      (CSVs limpos em UTF-8)         (Tabelas estruturadas)
```

| Camada | Local | Conteúdo |
|--------|-------|----------|
| **Bronze** | `data/versao.original/` | Arquivos originais, sem alterações (imutáveis, para auditoria) |
| **Silver** | `data/versao.resultado/` | CSVs limpos, padronizados e em UTF-8 |
| **Gold** | PostgreSQL (`db_transito_brasil`) e MinIO | Tabelas estruturadas para consulta e dashboards |

---

## Estrutura do Repositório

```text
big-data-project/
├── data/
│   ├── versao.original/          # Bronze: CSVs brutos (SIM, PRF, MGDI)
│   └── versao.resultado/         # Silver: CSVs tratados
├── scripts/
│   ├── TratarDadosSIM.py         # ETL do SIM/DATASUS
│   ├── TratarAcidentes2021a25.py # ETL dos acidentes PRF (2021-2025)
│   ├── TratarMgdi.py             # ETL do MGDI (processamento em chunks)
│   └── carregar_postgres.py      # Carga das tabelas no PostgreSQL
├── main.tf                       # Infraestrutura (Docker via Terraform)
├── terraform.tfvars.example      # Modelo das variáveis sensíveis
├── .gitignore                    # Bloqueia terraform.tfvars e artefatos locais
└── README.md
```

---

## 1. Dados Utilizados

A solução consolida dados de três fontes públicas oficiais:

### 1.1 Sistema de Informações sobre Mortalidade (SIM / MS – DATASUS)

| Item | Descrição |
|------|-----------|
| **Arquivos** | `sim_cnv_*.csv` |
| **Recorte** | Série histórica por grupo de causa básica (CID-10) e desagregação demográfica |
| **Formato** | CSV exportado do TABNET, com metadados no cabeçalho e codificação `latin1` |
| **Dimensões** | Óbitos por **Gênero** (Masc, Fem, Ign) e **Raça/Cor** (Branca, Preta, Amarela, Parda, Indígena, Ignorado) |

### 1.2 Acidentes de Trânsito Rodoviário (PRF)

| Item | Descrição |
|------|-----------|
| **Arquivos** | `acidentes2021.csv` a `acidentes2025.csv` |
| **Recorte** | Anos de **2021 a 2025** |
| **Conteúdo** | Microdados por data (`data_inversa`), localização (`uf`, `municipio`), causa/tipo do acidente, perfil do envolvido (`idade`, `sexo`, `tipo_envolvido`) e severidade (`estado_fisico`, `mortos`) |

### 1.3 Indicadores de Óbitos no Trânsito (MGDI / Ministério da Saúde)

| Item | Descrição |
|------|-----------|
| **Arquivo** | `mgdi_ms_g0g.csv` |
| **Recorte** | Dados municipais consolidados de óbitos no trânsito e estimativas populacionais |
| **Conteúdo** | Mortalidade por modalidade de transporte (pedestres, ciclistas, motociclistas, automóveis/ônibus) e faixas etárias |
| **Observação** | Base volumosa; exige processamento em blocos para não esgotar a memória RAM |

---

## 2. Tratamento Realizado (ETL)

### 2.1 Problemas Identificados

| # | Problema | Impacto |
|---|----------|---------|
| 1 | **Inconsistência de encodings** (`latin1` e `utf-8` misturados) | Erros de *mojibake* (ex.: `Ã`, `Â`) |
| 2 | **Cabeçalhos e metadados** nos arquivos do SIM | Linhas informativas antes da tabela real |
| 3 | **Valores ausentes e formatação** | Hífen (`-`) usado para indicar zero; tipos numéricos inconsistentes |
| 4 | **Volumetria elevada** (MGDI) | Alto consumo de RAM ao manipular a base em memória |

### 2.2 Scripts e Transformações

#### `scripts/TratarDadosSIM.py`
- Leitura ignorando o cabeçalho de metadados (`skiprows=3`) e extração do ano via expressão regular.
- Filtragem por regex no campo `Grupo CID10` para manter apenas causas ligadas ao trânsito: `transporte|Pedestre|Ciclista|Motociclista|triciclo`.
- Substituição de `-` por `0` e conversão segura para inteiros (`pd.to_numeric`).
- **Saídas:** `data/versao.resultado/tratado_sim_genero.csv` e `data/versao.resultado/tratado_sim_raca.csv`.

#### `scripts/TratarAcidentes2021a25.py`
- *Parsing* da coluna `data_inversa` para criar a coluna numérica `Ano`.
- Seleção estrita dos atributos essenciais (`causa_acidente`, `tipo_acidente`, `classificacao_acidente`, `estado_fisico`, `mortos`, entre outros).
- Normalização de nulos em atributos categóricos (`sexo` ausente preenchido como `'Não Informado'`).
- Consolidação dos cinco anos em uma única base.
- **Saída:** `data/versao.resultado/tratado_todos_acidentes2021a2025.csv`.

#### `scripts/TratarMgdi.py`
- Processamento otimizado em blocos de memória (`chunksize=100_000`).
- Função personalizada para correção de acentuação e padronização de encodings.
- Exclusão de registros totalmente vazios (`dropna(how="all")`).
- **Saída:** `data/versao.resultado/mgdi_ms_g0g_tratado.csv`.

#### `scripts/carregar_postgres.py`
- Leitura das bases tratadas em `data/versao.resultado/`.
- Carga automatizada dos DataFrames via `SQLAlchemy` / `psycopg`, criando as tabelas diretamente no PostgreSQL.

### 2.3 Fluxo de Execução do ETL

```text
SIM (latin1, metadados)  ──> TratarDadosSIM.py          ──> tratado_sim_genero.csv
                                                         └─> tratado_sim_raca.csv
PRF (2021–2025)          ──> TratarAcidentes2021a25.py  ──> tratado_todos_acidentes2021a2025.csv
MGDI (volumoso)          ──> TratarMgdi.py (chunks)     ──> mgdi_ms_g0g_tratado.csv
                                         │
                                         ▼
                              carregar_postgres.py ──> PostgreSQL (db_transito_brasil)
```

---

## 3. Modelagem dos Dados

### Banco Relacional: `db_transito_brasil`

#### `tb_sim_genero`
| Coluna | Tipo |
|--------|------|
| `Ano` | INT |
| `Grupo CID10` | VARCHAR |
| `Masc` | INT |
| `Fem` | INT |
| `Ign` | INT |
| `Total` | INT |

#### `tb_sim_raca`
| Coluna | Tipo |
|--------|------|
| `Ano` | INT |
| `Grupo CID10` | VARCHAR |
| `Branca` | INT |
| `Preta` | INT |
| `Amarela` | INT |
| `Parda` | INT |
| `Indigena` | INT |
| `Ignorado` | INT |
| `Total` | INT |

#### `tb_acidentes`
| Coluna | Tipo |
|--------|------|
| `Ano` | INT |
| `data_inversa` | DATE |
| `uf` | VARCHAR |
| `municipio` | VARCHAR |
| `causa_acidente` | VARCHAR |
| `tipo_acidente` | VARCHAR |
| `classificacao_acidente` | VARCHAR |
| `tipo_envolvido` | VARCHAR |
| `estado_fisico` | VARCHAR |
| `idade` | INT |
| `sexo` | VARCHAR |
| `mortos` | INT |

#### `tb_mgdi_indicadores`
| Coluna | Tipo |
|--------|------|
| `indicador` | VARCHAR |
| `ano` | INT |
| `uf` | VARCHAR |
| `codigo_municipio` | INT |
| `nome_municipio` | VARCHAR |
| `sexo` | VARCHAR |
| `faixa_etaria` | VARCHAR |
| `obitos_transito` | INT |
| `obitos_pedestres` | INT |
| `obitos_ciclistas` | INT |
| `obitos_motociclistas` | INT |

### Relacionamentos Analíticos

As tabelas não possuem chaves estrangeiras formais (são fatos agregados de fontes distintas), mas podem ser cruzadas por **ano** e **UF**:

```text
tb_acidentes.Ano / uf  ◄──►  tb_mgdi_indicadores.ano / uf
tb_sim_genero.Ano      ◄──►  tb_sim_raca.Ano  (mesmo Grupo CID10)
```

---

## 4. Infraestrutura como Código (IaC)

A infraestrutura é provisionada de forma declarativa com **Terraform** sobre contêineres **Docker**.

### Serviços

| Serviço | Imagem | Função | Portas |
|---------|--------|--------|--------|
| **PostgreSQL** | `postgres:15-alpine` | Banco relacional analítico | `5432` |
| **MinIO** | `coollabsio/minio:latest` | Data Lake local compatível com a API AWS S3 | `9000` (API) / `9001` (Console Web) |

### Recursos definidos em `main.tf`

| Recurso | Descrição |
|---------|-----------|
| `docker_network.transito_network` | Rede interna isolada (`rede_dados_transito`) |
| `docker_volume.postgres_data` | Volume persistente do PostgreSQL |
| `docker_volume.minio_data` | Volume persistente do MinIO |
| `docker_container.postgres_db` | Contêiner do PostgreSQL (porta externa `5432`) |
| `docker_container.minio_s3` | Contêiner do MinIO (portas `9000` e `9001`) |

---

## 5. Justificativa das Escolhas Tecnológicas

| Decisão | Justificativa |
|---------|---------------|
| **Python + Pandas + SQLAlchemy** | Suporte nativo a *parsing* de encodings e expressões regulares; integração direta com PostgreSQL via SQLAlchemy e drivers `psycopg`. |
| **Processamento em chunks** | A leitura em blocos (`chunksize=100_000`) da base MGDI evita falhas por falta de memória (*Out-Of-Memory*) e permite rodar em qualquer ambiente. |
| **Arquitetura em camadas (Bronze / Silver / Gold)** | Preserva o arquivo bruto para auditoria, isola os CSVs saneados e expõe somente dados consolidados na camada analítica. |
| **PostgreSQL 15** | Ideal para consultas estruturadas com agregações (`GROUP BY`), cruzamentos por UF/município e integração com ferramentas de BI. |
| **MinIO (S3 local)** | Simula o armazenamento de objetos da nuvem (AWS S3) sem custo de infraestrutura. |
| **Terraform + Docker** | Reprodutibilidade exata: banco e Data Lake sobem de forma unificada e determinística, com versionamento da infraestrutura. |

---

## 6. Guia de Execução e Reprodução

### Pré-requisitos

- **Docker Engine / Docker Desktop** em execução
- **Terraform** v1.5+
- **Python 3** instalado
- Bases originais disponíveis (SIM, PRF e MGDI)

### Passo a Passo

**1. Clonar o repositório**

```bash
git clone https://github.com/celesteadoq/big-data-project.git
cd big-data-project
```

**2. Configurar as variáveis de segurança**

Copie o arquivo de exemplo para criar o arquivo local (ignorado pelo `.gitignore`):

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edite o `terraform.tfvars` e defina suas senhas e credenciais.

**3. Provisionar a infraestrutura**

```bash
terraform init
terraform apply -auto-approve
```

**4. Instalar as dependências do Python**

```bash
pip3 install pandas psycopg2-binary psycopg sqlalchemy --break-system-packages
```

> 💡 **Alternativa recomendada:** use um ambiente virtual para não alterar o Python do sistema:
> ```bash
> python3 -m venv .venv
> source .venv/bin/activate        # Windows: .venv\Scripts\activate
> pip install pandas psycopg2-binary psycopg sqlalchemy
> ```

**5. Executar os scripts de tratamento (ETL)**

Com as bases originais em `data/versao.original/`:

```bash
python3 scripts/TratarDadosSIM.py
python3 scripts/TratarAcidentes2021a25.py
python3 scripts/TratarMgdi.py
```

**6. Carregar as tabelas no PostgreSQL**

```bash
python3 scripts/carregar_postgres.py
```

**7. Acessar os serviços**

| Serviço | Endereço | Observação |
|---------|----------|------------|
| **PostgreSQL** | `localhost:5432` | Banco: `db_transito_brasil` |
| **MinIO (Console)** | http://localhost:9001 | Use as credenciais definidas no `terraform.tfvars` |
| **MinIO (API S3)** | http://localhost:9000 | Compatível com clientes AWS S3 |

### Verificando a Carga

```bash
psql -h localhost -p 5432 -U <seu_usuario> -d db_transito_brasil -c "\dt"
```

### Encerrando o Ambiente

```bash
terraform destroy
```

> ⚠️ Isso remove os contêineres e a rede. Confira no `main.tf` se os volumes também serão removidos antes de executar, caso queira preservar os dados.

---

## 7. Exemplos de Consultas SQL

> Os nomes de colunas com maiúsculas ou espaços (`Ano`, `Grupo CID10`) precisam de aspas duplas no PostgreSQL.

**Total de mortos em acidentes por ano**

```sql
SELECT "Ano", SUM(mortos) AS total_mortos
FROM tb_acidentes
GROUP BY "Ano"
ORDER BY "Ano";
```

**Top 10 UFs com mais mortos (2021–2025)**

```sql
SELECT uf, SUM(mortos) AS total_mortos
FROM tb_acidentes
GROUP BY uf
ORDER BY total_mortos DESC
LIMIT 10;
```

**Principais causas de acidentes**

```sql
SELECT causa_acidente, COUNT(*) AS ocorrencias
FROM tb_acidentes
GROUP BY causa_acidente
ORDER BY ocorrencias DESC
LIMIT 10;
```

**Óbitos no trânsito por gênero e ano (SIM)**

```sql
SELECT "Ano",
       SUM("Masc") AS masculino,
       SUM("Fem")  AS feminino,
       SUM("Total") AS total
FROM tb_sim_genero
GROUP BY "Ano"
ORDER BY "Ano";
```

**Óbitos por raça/cor (SIM)**

```sql
SELECT "Ano",
       SUM("Branca") AS branca,
       SUM("Preta")  AS preta,
       SUM("Parda")  AS parda
FROM tb_sim_raca
GROUP BY "Ano"
ORDER BY "Ano";
```

**Óbitos de motociclistas por UF (MGDI)**

```sql
SELECT uf, ano, SUM(obitos_motociclistas) AS obitos_motos
FROM tb_mgdi_indicadores
GROUP BY uf, ano
ORDER BY ano, obitos_motos DESC;
```

**Cruzamento PRF × MGDI por UF e ano**

```sql
SELECT a."Ano", a.uf,
       SUM(a.mortos)            AS mortos_prf,
       SUM(m.obitos_transito)   AS obitos_mgdi
FROM tb_acidentes a
JOIN tb_mgdi_indicadores m
  ON m.uf = a.uf AND m.ano = a."Ano"
GROUP BY a."Ano", a.uf
ORDER BY a."Ano", a.uf;
```

> ⚠️ O cruzamento acima é ilustrativo: as fontes têm metodologias diferentes (a PRF cobre apenas rodovias federais; o MGDI/SIM cobre óbitos em todo o território). Se `tb_mgdi_indicadores` tiver várias linhas por UF/ano, agregue-a em uma subconsulta antes do `JOIN` para evitar duplicação de valores.

---

## 8. Solução de Problemas

| Sintoma | Causa provável | Solução |
|---------|----------------|---------|
| Caracteres como `Ã` ou `Â` nos dados | Leitura com encoding incorreto | Confirme que o arquivo bruto é `latin1` e use os scripts de tratamento antes da carga |
| `Cannot connect to the Docker daemon` | Docker não está em execução | Inicie o Docker Desktop / serviço do Docker |
| `connection refused` na porta `5432` | Contêiner parado ou porta ocupada por outro PostgreSQL | Verifique com `docker ps`; pare o serviço local ou altere a porta externa no `main.tf` |
| `MemoryError` ao processar o MGDI | Leitura da base inteira em memória | Mantenha o `chunksize=100_000` (ou reduza-o) |
| `error: externally-managed-environment` no `pip` | Python gerenciado pelo sistema | Use `--break-system-packages` ou, preferencialmente, um ambiente virtual |
| Erro de autenticação no PostgreSQL | Credenciais divergentes do `terraform.tfvars` | Use exatamente os valores definidos no `terraform.tfvars` |
| Arquivo `data/versao.resultado/` vazio | Etapa de ETL não executada ou bases ausentes | Confirme os arquivos em `data/versao.original/` e rode os scripts de tratamento |

---

## 9. Segurança

- O arquivo **`terraform.tfvars`** contém credenciais e **nunca deve ser versionado** (já está no `.gitignore`).
- Use apenas o **`terraform.tfvars.example`** com valores fictícios no repositório.
- Os serviços expõem portas em `localhost` para uso **local/desenvolvimento**. Não exponha `5432`, `9000` ou `9001` diretamente na internet.
- Utilize senhas fortes e diferentes para o PostgreSQL e o MinIO.
- Os dados são públicos e agregados/anonimizados pelas fontes oficiais, mas respeite os termos de uso de cada órgão.

---

## 10. Próximos Passos

- [ ] Orquestração do pipeline completo (ex.: Apache Airflow ou Prefect)
- [ ] Envio automatizado dos CSVs tratados ao bucket MinIO
- [ ] Criação de chaves, índices e tabelas-dimensão (UF, município, tempo) no PostgreSQL
- [ ] Testes de qualidade de dados (ex.: Great Expectations)
- [ ] Dashboard analítico (Metabase, Superset ou Power BI)
- [ ] Pipeline de CI para validar scripts e `terraform validate`

---

## Fontes de Dados

- **DATASUS / TABNET** – Sistema de Informações sobre Mortalidade (SIM): https://datasus.saude.gov.br
- **Polícia Rodoviária Federal (PRF)** – Dados abertos de acidentes: https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos
- **Ministério da Saúde** – Indicadores MGDI de óbitos no trânsito

---

## Licença e Autoria

- **Repositório:** [celesteadoq/big-data-project](https://github.com/celesteadoq/big-data-project)
- **Licença:** _defina aqui a licença do projeto (ex.: MIT)._

Contribuições, sugestões e *issues* são bem-vindas.