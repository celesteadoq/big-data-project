import pandas as pd
import glob
import os

input_dir = "data/versao.original"
output_dir = "data/versao.resultado"
os.makedirs(output_dir, exist_ok=True)

padrao_busca = os.path.join(input_dir, "acidentes20*.csv")
arquivos_acidentes = glob.glob(padrao_busca)

print(f"Total de arquivos de acidentes encontrados: {len(arquivos_acidentes)}\n")

lista_consolidada = []

for arquivo in arquivos_acidentes:
    nome_arquivo = os.path.basename(arquivo)
    try:
        print(f"Processando: {nome_arquivo}...")
        
        df = pd.read_csv(arquivo, encoding='latin1', sep=';', on_bad_lines='skip')
        
        if 'data_inversa' in df.columns:
            df['data_inversa'] = pd.to_datetime(df['data_inversa'], errors='coerce')
            df['Ano'] = df['data_inversa'].dt.year.fillna(0).astype(int)
        
        colunas_essenciais = [
            'Ano', 'data_inversa', 'uf', 'municipio', 'causa_acidente', 
            'tipo_acidente', 'classificacao_acidente', 'tipo_envolvido', 
            'estado_fisico', 'idade', 'sexo', 'mortos'
        ]
        
        colunas_presentes = [c for c in colunas_essenciais if c in df.columns]
        df_filtrado = df[colunas_presentes].copy()
        
        if 'sexo' in df_filtrado.columns:
            df_filtrado['sexo'] = df_filtrado['sexo'].fillna('Não Informado')
            
        lista_consolidada.append(df_filtrado)
        
    except Exception as e:
        print(f"Erro ao processar {nome_arquivo}: {e}")

if lista_consolidada:
    base_geral = pd.concat(lista_consolidada, ignore_index=True)
    
  
    path_detalhado = os.path.join(output_dir, "tratado_todos_acidentes2021a2025.csv")
    
    base_geral.to_csv(path_detalhado, index=False, sep=';', encoding='utf-8-sig')

    
    print("\n[SUCESSO] Todos os arquivos de acidentes foram tratados e unificados!")
    print(f"-> Base detalhada salva em: {path_detalhado}")
else:
    print("Nenhum arquivo válido foi processado. Verifique se os arquivos 'acidentes20*.csv' estão na pasta 'data/versao.original/'.")