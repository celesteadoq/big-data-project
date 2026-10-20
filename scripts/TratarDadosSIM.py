import glob
import os
import re
import sys

import pandas as pd

input_dir = "data/versao.original"
output_dir = "data/versao.resultado"
os.makedirs(output_dir, exist_ok=True)

# Causas de trânsito mantidas e transportes não rodoviários excluídos.
# Confira a lista impressa ao final da execução e ajuste se necessário.
PALAVRAS_CHAVE = "transporte|Pedestre|Ciclista|Motociclista|triciclo"
EXCLUIR = "água|aquátic|aére|aereo|espaci"

COLS_GENERO = ["Masc", "Fem", "Ign", "Total"]
COLS_RACA = ["Branca", "Preta", "Amarela", "Parda", "Indígena", "Ignorado", "Total"]


def extrair_ano(cabecalho, nome):
    for linha in cabecalho:
        if "Período:" in linha:
            anos = set(re.findall(r"\d{4}", linha.split("Período:")[1]))
            if len(anos) == 1:
                return int(anos.pop())
            raise ValueError(f"{nome}: período sem ano único: {linha.strip()!r}")
    raise ValueError(f"{nome}: linha 'Período:' não encontrada nas 3 primeiras linhas")


def para_int(serie, nome, coluna):
    texto = serie.astype(str).str.strip().replace("-", "0")  # "-" = zero no TABNET
    num = pd.to_numeric(texto, errors="coerce")
    invalido = num.isna() | (num % 1 != 0)  # NaN ou decimal (ex.: "1.234" com ponto de milhar)
    if invalido.any():
        ruins = list(texto[invalido].unique()[:5])
        raise ValueError(f"valores não inteiros em '{coluna}': {ruins}")
    return num.astype(int)


def salvar(lista, nome_saida, rotulo):
    if not lista:
        print(f"Nenhum arquivo de {rotulo} processado.")
        return False

    base = pd.concat(lista, ignore_index=True)
    dup = base.duplicated(["Ano", "Grupo CID10"], keep=False)
    if dup.any():
        raise ValueError(
            f"{rotulo}: pares (Ano, Grupo CID10) repetidos:\n"
            f"{base[dup].head(10).to_string()}"
        )

    caminho = os.path.join(output_dir, nome_saida)
    base.to_csv(caminho, index=False, sep=";", encoding="utf-8-sig")
    print(f"[SUCESSO] {rotulo}: {len(base)} linhas, anos {[int(a) for a in sorted(base['Ano'].unique())]} -> {caminho}")
    print("  Grupos incluídos:")
    for g in sorted(base["Grupo CID10"].unique()):
        print(f"   - {g}")
    return True


arquivos = sorted(glob.glob(os.path.join(input_dir, "sim_cnv_*.csv")))
print(f"Iniciando unificação de {len(arquivos)} arquivos do SIM...\n")

lista_genero, lista_raca = [], []
erros, ignorados = [], []

for arquivo in arquivos:
    nome = os.path.basename(arquivo)
    try:
        with open(arquivo, "r", encoding="latin1") as f:
            cabecalho = [f.readline() for _ in range(3)]
        ano = extrair_ano(cabecalho, nome)

        df = pd.read_csv(arquivo, encoding="latin1", skiprows=3, sep=";")
        if "Grupo CID10" not in df.columns:
            raise ValueError(f"{nome}: coluna 'Grupo CID10' ausente (colunas: {list(df.columns)})")

        df["Grupo CID10"] = df["Grupo CID10"].str.replace(r"^[.\s]+", "", regex=True).str.strip()
        grupo = df["Grupo CID10"]
        mantem = (
            grupo.str.contains(PALAVRAS_CHAVE, case=False, na=False)
            & ~grupo.str.contains(EXCLUIR, case=False, na=False)
        )
        df = df[mantem].copy()
        if df.empty:
            raise ValueError(f"{nome}: nenhum grupo de trânsito encontrado")

        if "Masc" in df.columns:
            cols, destino = COLS_GENERO, lista_genero
        elif "Branca" in df.columns:
            cols, destino = COLS_RACA, lista_raca
        else:
            ignorados.append(nome)
            continue

        faltando = [c for c in cols if c not in df.columns]
        if faltando:
            raise ValueError(f"{nome}: faltam colunas {faltando} (colunas: {list(df.columns)})")

        df.insert(0, "Ano", ano)
        df = df[["Ano", "Grupo CID10"] + cols].copy()
        for col in cols:
            df[col] = para_int(df[col], nome, col)
        destino.append(df)

    except Exception as e:
        erros.append(str(e) if str(e).startswith(nome) else f"{nome}: {e}")

if ignorados:
    print("Ignorados (sem coluna Masc nem Branca):", ignorados)

if erros:
    print("\nERROS (nada foi gravado):")
    for e in erros:
        print(" -", e)
    sys.exit(1)

print("\nGerando produtos finais unificados...")
ok_g = salvar(lista_genero, "tratado_sim_genero.csv", "Gênero")
ok_r = salvar(lista_raca, "tratado_sim_raca.csv", "Raça")
if not (ok_g or ok_r):
    sys.exit("Nenhuma base gerada. Verifique os arquivos sim_cnv_*.csv.")

print("\nProcesso concluído!")