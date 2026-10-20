import os
import pandas as pd
from sqlalchemy import create_engine

# Conexão com o PostgreSQL rodando no Docker local
# Ajuste 'senha_postgres' para a senha que você colocou no terraform.tfvars
DB_USER = "postgres"
DB_PASS = "SuaSenhaSeguraPostgres123" 
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "db_transito_brasil"

# Cria a string de conexão
engine = create_engine(f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

pasta_resultados = "data/versao.resultado"

# Mapeamento dos arquivos CSV tratados para o nome final das tabelas
tabelas = {
    "tratado_sim_genero.csv": "tb_sim_genero",
    "tratado_sim_raca.csv": "tb_sim_raca",
    "tratado_todos_acidentes2021a2025.csv": "tb_acidentes",
    "mgdi_ms_g0g_tratado.csv": "tb_mgdi_indicadores"
}

for arquivo_csv, nome_tabela in tabelas.items():
    caminho_csv = os.path.join(pasta_resultados, arquivo_csv)
    
    if os.path.exists(caminho_csv):
        print(f"Carregando {arquivo_csv} para a tabela '{nome_tabela}'...")
        df = pd.read_csv(caminho_csv)
        
        # Envia o dataframe direto para o PostgreSQL criando a tabela automaticamente
        df.to_sql(name=nome_tabela, con=engine, if_exists="replace", index=False)
        print(f" Tabela '{nome_tabela}' criada com sucesso!")
    else:
        print(f" Arquivo {arquivo_csv} não encontrado em {pasta_resultados}.")

print("\n🚀 Carga finalizada com sucesso no PostgreSQL!")