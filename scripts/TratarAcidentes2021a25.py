import glob
import os

import pandas as pd

input_dir = "data/versao.original"
output_dir = "data/versao.resultado"
os.makedirs(output_dir, exist_ok=True)

arquivos = sorted(glob.glob(os.path.join(input_dir, "acidentes202[1-5]*.csv")))
print("Arquivos encontrados:", [os.path.basename(a) for a in arquivos])

COLUNAS = [
    "id", "pesid", "id_veiculo", "data_inversa", "uf", "municipio",
    "causa_acidente", "tipo_acidente", "classificacao_acidente",
    "tipo_envolvido", "estado_fisico", "idade", "sexo", "mortos",
]

lista = []
for arquivo in arquivos:
    nome = os.path.basename(arquivo)
    print(f"Processando {nome}...")

    df = pd.read_csv(arquivo, encoding="latin1", sep=";", dtype=str, keep_default_na=False)

    faltando = [c for c in COLUNAS if c not in df.columns]
    if faltando:
        raise ValueError(f"{nome}: faltam as colunas {faltando}")

    df = df[COLUNAS].replace({"NA": pd.NA, "": pd.NA})  # "NA" = linha sem pessoa

    data = pd.to_datetime(df["data_inversa"], errors="coerce")
    if data.isna().any():
        print(f"  aviso: {data.isna().sum()} datas inválidas em {nome}")
    df["data_inversa"] = data
    df.insert(0, "ano", data.dt.year.astype("Int64"))

    for c in ["id", "pesid", "id_veiculo", "mortos"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")

    idade = pd.to_numeric(df["idade"], errors="coerce")
    df["idade"] = idade.where(idade.between(0, 110)).astype("Int64")

    lista.append(df)

base = pd.concat(lista, ignore_index=True)
saida = os.path.join(output_dir, "tratado_todos_acidentes2021a2025.csv")
base.to_csv(saida, index=False, sep=";", encoding="utf-8-sig")
print(f"[SUCESSO] {len(base):,} linhas -> {saida}")