# 📊 Projeto de Big Data & Engenharia de Dados: Análise Integrada de Trânsito e Mortalidade

Este repositório contém a solução completa de Engenharia de Dados para ingestão, tratamento, modelagem e provisionamento de infraestrutura como código (IaC) das bases de acidentes de trânsito, dados de mortalidade (SIM/DATASUS) e indicadores de saúde (MGDI).

---

## 1. 📁 Dados Utilizados

A solução consolida dados de três fontes públicas oficiais do governo brasileiro:

* **1. Sistema de Informações sobre Mortalidade (SIM / MS - DATASUS)**
  * **Identificação:** Arquivos `sim_cnv_*.csv`.
  * **Recorte/Período:** Série histórica por grupo do CID10 e desagregação demográfica.
  * **Características:** Arquivos estruturados em formato CSV exportados do TABNET com metadados no cabeçalho, codificação em `latin1`, contendo contagem de óbitos categorizados por **Gênero** (Masc, Fem, Ign) e **Raça/Cor** (Branca, Preta, Amarela, Parda, Indígena).

* **2. Acidentes de Trânsito Rodoviário (PRF)**
  * **Identificação:** Arquivos `acidentes20*.csv`.
  * **Recorte/Período:** Anos de **2021 a 2025**.
  * **Características:** Microdados contendo registros de ocorrências por data (`data_inversa`), localização (`uf`, `municipio`), causa/tipo de acidente, perfil do envolvido (`idade`, `sexo`, `tipo_envolvido`) e severidade (`estado_fisico`, `mortos`).

* **3. Indicadores de Óbitos no Trânsito (MGDI / Ministério da Saúde)**
  * **Identificação:** Arquivo `mgdi_ms_g0g.csv`.
  * **Recorte/Período:** Dados municipais consolidados de óbitos no trânsito e estimativas populacionais.
  * **Características:** Base volumosa contendo indicadores de mortalidade por tipo de veículo (pedestres, ciclistas, motociclistas, automóveis/ônibus) e faixas etárias.

---

## 2. 🧹 Tratamento Realizado (ETL)

### Problemas e Características Identificados:
1. **Inconsistência de Encodings e Caracteres:** Mistura de arquivos codificados em `latin1` e `utf-8`, com ocorrência de *mojibake* (ex: caracteres desformatados como `Ã` e `Â`).
2. **Metadados em Cabeçalhos:** Os arquivos do SIM contêm linhas de metadados no topo antes da tabela de dados reais.
3. **Valores Ausentes e Formatação Numérica:** Uso do hífen (`-`) para indicar contagem zero e inconsistência de tipos numéricos.
4. **Volumetria do MGDI:** Arquivo extenso exigindo processamento otimizado de memória.

### Decisões e Transformações Aplicadas:
* **`scripts/01_tratar_sim.py`:** 
  * Leitura com `skiprows=3` e parsing dinâmico do período/ano contido nos cabeçalhos.
  * Filtragem por Expressão Regular (Regex) no campo `Grupo CID10` para extrair apenas causas ligadas ao trânsito (`transporte|Pedestre|Ciclista|Motociclista|triciclo`).
  * Substituição de `-` por `0` e conversão segura para tipos numéricos (`pd.to_numeric`).
  * Separação em duas bases tratadas: `tratado_sim_genero.csv` e `tratado_sim_raca.csv`.

* **`scripts/02_tratar_acidentes.py`:**
  * Parsing da coluna `data_inversa` para extração do campo numérico `Ano`.
  * Seleção estrita das colunas essenciais (`causa_acidente`, `tipo_acidente`, `classificacao_acidente`, `estado_fisico`, `mortos`, etc.).
  * Tratamento de nulos em atributos categóricos (preenchimento de `sexo` ausente como `'Não Informado'`).
  * Consolidação anual em uma base única `tratado_todos_acidentes2021a2025.csv`.

* **`scripts/03_tratar_mgdi.py`:**
  * Processamento em blocos de memória (`chunksize=100_000`) para otimização de performance.
  * Correção de acentuação e encode via função personalizada (`corrigir_texto`).
  * Padronização de esquemas de colunas e exclusão de linhas totalmente vazias (`dropna(how="all")`).
  * Exportação para `mgdi_ms_g0g_tratado.csv`.

---

## 3. 📐 Modelagem dos Dados

A arquitetura adota uma estratégia de **Armazenamento em Camadas (Data Lake + Relacional)**:

```text
[Dados Brutos / Bronze]       [Dados Tratados / Silver]      [Camada Analítica / Gold]
 data/versao.original/   ──>    data/versao.resultado/   ──>   PostgreSQL & MinIO S3
 (CSV sem padronização)        (CSVs limpos em UTF-8)         (Tabelas estruturadas)