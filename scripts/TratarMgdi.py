import os

import pandas as pd

arquivo_entrada = "data/versao.original/mgdi_ms_g0g.csv"
arquivo_saida = "data/versao.resultado/mgdi_ms_g0g_tratado.csv"
arquivo_tmp = arquivo_saida + ".tmp"

os.makedirs(os.path.dirname(arquivo_saida), exist_ok=True)

colunas = [
    "indicador",
    "ano",
    "uf",
    "codigo_municipio",
    "nome_municipio",
    "sexo",
    "faixa_etaria",
    "obitos_transito",
    "obitos_pedestres",
    "obitos_ciclistas",
    "obitos_motociclistas",
    "obitos_automoveis_onibus",
    "obitos_demais_veiculos",
    "obitos_veiculos_nao_especificados",
    "populacao_estimada",
    "multiplicador",
]

colunas_texto = ["indicador", "uf", "nome_municipio", "sexo", "faixa_etaria"]

colunas_numericas = [c for c in colunas if c not in colunas_texto]

# Colunas categóricas cujos valores distintos serão listados ao final,
# para você checar se há linhas de total misturadas com o detalhe.
colunas_diagnostico = ["indicador", "uf", "sexo", "faixa_etaria"]


def corrigir_texto(valor):
    if not isinstance(valor, str):
        return valor

    valor = valor.strip()
    if "Ã" in valor or "Â" in valor:
        try:
            return valor.encode("latin1").decode("utf-8").strip()
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass

    return valor


def para_numerico(serie):
    num = pd.to_numeric(serie.str.strip(), errors="raise")
    if (num.dropna() % 1 == 0).all():
        return num.astype("Int64")  # evita "2020.0" no CSV
    return num


valores_unicos = {c: set() for c in colunas_diagnostico}
primeiro_bloco = True
total_linhas = 0

try:
    for bloco in pd.read_csv(
        arquivo_entrada,
        sep=",",
        encoding="utf-8-sig",
        chunksize=100_000,
        dtype=str,
        on_bad_lines="error",
    ):
        if len(bloco.columns) != len(colunas):
            raise ValueError(
                f"Esperadas {len(colunas)} colunas, encontradas {len(bloco.columns)}."
            )

        bloco.columns = colunas

        for coluna in colunas_texto:
            bloco[coluna] = bloco[coluna].map(corrigir_texto)

        bloco = bloco.dropna(how="all")

        for coluna in colunas_numericas:
            bloco[coluna] = para_numerico(bloco[coluna])

        for coluna in colunas_diagnostico:
            valores_unicos[coluna].update(bloco[coluna].dropna().unique())

        bloco.to_csv(
            arquivo_tmp,
            sep=";",
            index=False,
            mode="w" if primeiro_bloco else "a",
            header=primeiro_bloco,
            encoding="utf-8",
        )

        primeiro_bloco = False
        total_linhas += len(bloco)
except Exception:
    if os.path.exists(arquivo_tmp):
        os.remove(arquivo_tmp)  # não deixa CSV parcial no disco
    raise

os.replace(arquivo_tmp, arquivo_saida)

print(f"Tratamento concluído: {total_linhas:,} linhas -> {arquivo_saida}")
print("\nValores distintos (procure por 'Total', 'Brasil' ou similares):")
for coluna, valores in valores_unicos.items():
    lista = sorted(valores)
    extra = f" ... (+{len(lista) - 40})" if len(lista) > 40 else ""
    print(f"  {coluna}: {lista[:40]}{extra}")