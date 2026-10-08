import pandas as pd
df = pd.read_csv(r'C:\Users\gasiq\Documents\DocumentosProjetos-Programacao-github\dengue -CXS\dengue_53-40.csv', sep=None, engine='python')
print("Colunas disponíveis:", df.columns)
if 'municipio' in df.columns or 'nome' in df.columns or 'municipio_nome' in df.columns:
    print(df[['municipio_nome' if 'municipio_nome' in df.columns else df.columns[0]]].drop_duplicates())