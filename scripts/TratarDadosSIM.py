import pandas as pd
import glob
import os

input_dir =  "data/versao.original"  
output_dir = "data/versao.resultado"
os.makedirs(output_dir, exist_ok=True)

arquivos = glob.glob(os.path.join(input_dir, "sim_cnv_*.csv"))
print(f"Iniciando unificação de {len(arquivos)} arquivos do SIM...\n")

lista_genero = []
lista_raca = []

for arquivo in arquivos:
    nome_arquivo = os.path.basename(arquivo)
    try:
        with open(arquivo, 'r', encoding='latin1') as f:
            cabecalho_linhas = [f.readline() for _ in range(3)]
        
        ano_extraido = "Desconhecido"
        for linha in cabecalho_linhas:
            if "Período:" in linha:
                ano_extraido = linha.split("Período:")[1].strip()

        df = pd.read_csv(arquivo, encoding='latin1', skiprows=3, sep=';')
        df['Ano'] = ano_extraido
        
        if 'Grupo CID10' in df.columns:
            df['Grupo CID10'] = df['Grupo CID10'].str.replace(r'^[.\s]+', '', regex=True).str.strip()
        
        palavras_chave = 'transporte|Pedestre|Ciclista|Motociclista|triciclo'
        df_filtrado = df[df['Grupo CID10'].str.contains(palavras_chave, case=False, na=False)].copy()
        
        if 'Masc' in df_filtrado.columns:
            cols_valores = ['Masc', 'Fem', 'Ign', 'Total']
            for col in cols_valores:
                if col in df_filtrado.columns:
                    df_filtrado[col] = pd.to_numeric(df_filtrado[col].astype(str).str.replace('-', '0'), errors='coerce').fillna(0)
            lista_genero.append(df_filtrado)
            
        elif 'Branca' in df_filtrado.columns:
            cols_valores = ['Branca', 'Preta', 'Amarela', 'Parda', 'Indígena', 'Ignorado', 'Total']
            for col in cols_valores:
                if col in df_filtrado.columns:
                    df_filtrado[col] = pd.to_numeric(df_filtrado[col].astype(str).str.replace('-', '0'), errors='coerce').fillna(0)
            lista_raca.append(df_filtrado)
            
    except Exception as e:
        print(f"Erro ao processar {nome_arquivo}: {e}")


print("\nGerando produtos finais unificados...")

if lista_genero:
    df_geral_genero = pd.concat(lista_genero, ignore_index=True)
    cols_ord = ['Ano', 'Grupo CID10'] + [c for c in df_geral_genero.columns if c not in ['Ano', 'Grupo CID10']]
    df_geral_genero = df_geral_genero[cols_ord]
    
    path_geral_genero = os.path.join(output_dir, "tratado_sim_genero.csv")
    df_geral_genero.to_csv(path_geral_genero, index=False, sep=';', encoding='utf-8-sig')
    print(f"[SUCESSO] Base unificada de Gênero gerada: {path_geral_genero}")

if lista_raca:
    df_geral_raca = pd.concat(lista_raca, ignore_index=True)
    cols_ord_raca = ['Ano', 'Grupo CID10'] + [c for c in df_geral_raca.columns if c not in ['Ano', 'Grupo CID10']]
    df_geral_raca = df_geral_raca[cols_ord_raca]
    
    path_geral_raca = os.path.join(output_dir, "tratado_sim_raca.csv")
    df_geral_raca.to_csv(path_geral_raca, index=False, sep=';', encoding='utf-8-sig')
    print(f"[SUCESSO] Base unificada de Raça gerada: {path_geral_raca}")

print("\nProcesso concluído! Apenas as bases unificadas foram geradas na pasta 'data/versao.resultado'.")