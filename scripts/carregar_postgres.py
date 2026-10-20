import os
import re
import unicodedata

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

engine = create_engine(
    URL.create(
        "postgresql+psycopg2",
        username=os.environ.get("DB_USER", "postgres"),
        password=os.environ["DB_PASS"],  # obrigatória
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ.get("DB_PORT", "5432")),
        database=os.environ.get("DB_NAME", "db_transito_brasil"),
    )
)

PASTA = "data/versao.resultado"
INT = "Int64"

# arquivo -> (tabela, dtypes, colunas de data)
TABELAS = {
    "tratado_sim_genero.csv": ("tb_sim_genero", {}, []),
    "tratado_sim_raca.csv": ("tb_sim_raca", {}, []),
    "tratado_todos_acidentes2021a2025.csv": (
        "tb_acidentes",
        {"ano": INT, "id": INT, "pesid": INT, "id_veiculo": INT, "idade": INT, "mortos": INT},
        ["data_inversa"],
    ),
    "mgdi_ms_g0g_tratado.csv": (
        "tb_mgdi_indicadores",
        {c: INT for c in [
            "ano", "codigo_municipio", "obitos_transito", "obitos_pedestres",
            "obitos_ciclistas", "obitos_motociclistas", "obitos_automoveis_onibus",
            "obitos_demais_veiculos", "obitos_veiculos_nao_especificados",
            "populacao_estimada", "multiplicador"]},
        [],
    ),
}

POS_CARGA = {
    "tb_acidentes": [
        "ALTER TABLE tb_acidentes ALTER COLUMN data_inversa TYPE date",
        "CREATE INDEX IF NOT EXISTS ix_acid_ano_uf ON tb_acidentes (ano, uf)",
        "CREATE INDEX IF NOT EXISTS ix_acid_pessoa ON tb_acidentes (ano, id, pesid)",
    ],
    "tb_mgdi_indicadores": [
        "CREATE INDEX IF NOT EXISTS ix_mgdi_ano_uf ON tb_mgdi_indicadores (ano, uf)",
    ],
}


def snake(nome):
    nome = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    return re.sub(r"[^0-9a-zA-Z]+", "_", nome).strip("_").lower()


for arquivo, (tabela, dtypes, datas) in TABELAS.items():
    caminho = os.path.join(PASTA, arquivo)
    if not os.path.exists(caminho):
        print(f"Arquivo {arquivo} não encontrado em {PASTA}.")
        continue

    print(f"Carregando {arquivo} -> {tabela}...")
    primeiro, total = True, 0
    for bloco in pd.read_csv(caminho, sep=";", encoding="utf-8-sig", chunksize=100_000,
                             dtype=dtypes, parse_dates=datas):
        bloco.columns = [snake(c) for c in bloco.columns]
        bloco.to_sql(tabela, engine, if_exists="replace" if primeiro else "append",
                     index=False, chunksize=10_000)
        primeiro, total = False, total + len(bloco)

    with engine.begin() as conn:
        for ddl in POS_CARGA.get(tabela, []):
            conn.execute(text(ddl))
    print(f"  {total:,} linhas carregadas.")