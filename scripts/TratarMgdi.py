
import pandas as pd

arquivo_entrada = (
    "data/versao.original/mgdi_ms_g0g.csv"
)

arquivo_saida = "data/versao.resultado/mgdi_ms_g0g_tratado.csv"

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

colunas_texto = [
    "indicador",
    "uf",
    "nome_municipio",
    "sexo",
    "faixa_etaria",
]

colunas_numericas = [
    "ano",
    "codigo_municipio",
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


def corrigir_texto(valor):
    if not isinstance(valor, str):
        return valor

    if "Ã" in valor or "Â" in valor:
        try:
            return valor.encode("latin1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass

    return valor.strip()


primeiro_bloco = True

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
            f"Esperadas 16 colunas, encontradas "
            f"{len(bloco.columns)}."
        )

    bloco.columns = colunas

    for coluna in colunas_texto:
        bloco[coluna] = bloco[coluna].map(corrigir_texto)

    bloco = bloco.dropna(how="all")

    for coluna in colunas_numericas:
        bloco[coluna] = pd.to_numeric(
            bloco[coluna].str.strip(),
            errors="raise",
        )

    bloco.to_csv(
        arquivo_saida,
        sep=";",
        index=False,
        mode="w" if primeiro_bloco else "a",
        header=primeiro_bloco,
        encoding="utf-8",
    )

    primeiro_bloco = False

print("Tratamento concluído:", arquivo_saida)
