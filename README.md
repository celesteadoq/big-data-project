# 📊 Projeto de Big Data & Engenharia de Dados: Análise de Trânsito

Este repositório contém a solução completa para o armazenamento, tratamento e infraestrutura como código (IaC) das bases de dados de trânsito, mortalidade (SIM), acidentes e indicadores do MGDI.

---

## 📁 Estrutura do Repositório

```text
.
├── scripts/                      # Código Python para ETL/Tratamento dos Dados
│   ├── 01_tratar_sim.py          # Tratamento e unificação da base SIM (Gênero e Raça)
│   ├── 02_tratar_acidentes.py    # Consolidação dos arquivos de acidentes (2021-2025)
│   └── 03_tratar_mgdi.py         # Tratamento da base de indicadores MGDI
├── data/                         # Diretório para armazenamento local dos dados
│   ├── versao.original/          # Recebe os arquivos .csv originais/brutos
│   └── versao.resultado/         # Diretório onde os CSVs tratados são gerados
├── main.tf                       # Provisionamento dos recursos Docker (Postgres e MinIO)
├── providers.tf                  # Definição dos provedores e versões do Terraform
├── variables.tf                  # Declaração das variáveis do Terraform
├── outputs.tf                    # Saídas com endpoints e strings de conexão
├── terraform.tfvars.example      # Modelo seguro para configuração de variáveis locais
├── .gitignore                    # Bloqueio de arquivos sensíveis e temporários
└── README.md                     # Documentação completa do projeto