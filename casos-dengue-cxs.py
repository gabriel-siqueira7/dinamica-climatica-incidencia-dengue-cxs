import sys
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# 1. CONFIGURAÇÕES INICIAIS
CAMINHO_ARQUIVO = (r'C:\Users\gasiq\Documents\DocumentosProjetos-Programacao-github\dengue -CXS\dengue_53-40.csv')

# 2. CARREGAMENTO E INSPEÇÃO DO ARQUIVO
try:
    df_raw = pd.read_csv(CAMINHO_ARQUIVO, sep=None, engine="python")
    print(f"[OK] Arquivo carregado: {CAMINHO_ARQUIVO}")
    print(f"Linhas: {df_raw.shape[0]} | Colunas: {df_raw.shape[1]}\n")
except FileNotFoundError:
    print(f"[ERRO] Arquivo '{CAMINHO_ARQUIVO}' não encontrado.")
    print("Verifique se o CSV está salvo na mesma pasta deste script.")
    sys.exit()

df = df_raw.copy()

# 3. MAPEAMENTO DINÂMICO DE COLUNAS
colunas_map = {}

for col in ["data_iniSE", "data", "dt_notific", "DT_NOTIFIC", "data_inicio"]:
    if col in df.columns:
        colunas_map[col] = "data"
        break

for col in ["casos", "casos_est", "notificacoes", "CASOS", "nu_notific"]:
    if col in df.columns:
        colunas_map[col] = "casos"
        break

for col in ["tempmed", "temperatura", "temp_media", "TEMPMED", "tmed"]:
    if col in df.columns:
        colunas_map[col] = "temperatura"
        break

for col in ["umidmed", "umidade", "umid_relativa", "UMIDMED", "urmed"]:
    if col in df.columns:
        colunas_map[col] = "umidade"
        break

df = df.rename(columns=colunas_map)

colunas_necessarias = ["data", "casos", "temperatura", "umidade"]
faltantes = [col for col in colunas_necessarias if col not in df.columns]

if faltantes:
    print(f"[AVISO] Colunas não encontradas automaticamente: {faltantes}")
    print(f"Colunas presentes no CSV: {list(df_raw.columns)}")
    sys.exit()

# 4. TRATAMENTO E LIMPEZA DOS DADOS
df["data"] = pd.to_datetime(df["data"], errors="coerce")
df = df.dropna(subset=["data"]).sort_values("data").reset_index(drop=True)

for col in ["casos", "temperatura", "umidade"]:
    if df[col].dtype == object:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
        )
    df[col] = pd.to_numeric(df[col], errors="coerce")

df["casos"] = df["casos"].fillna(0).clip(lower=0)
df["temperatura"] = (
    df["temperatura"].interpolate(method="linear").bfill().ffill()
)
df["umidade"] = df["umidade"].interpolate(method="linear").bfill().ffill()


# 5. ENGENHARIA DE FEATURES (DEFASAGEM / LAG TEMPORAL)
# Lag de 3 semanas (21 dias): tempo médio de eclosão + ciclo viral extrínseco + sintomas
df["temp_lag3"] = df["temperatura"].shift(3)
df["umid_lag3"] = df["umidade"].shift(3)

df_clean = df.dropna(subset=["temp_lag3", "umid_lag3"]).reset_index(drop=True)

corr_temp = df_clean["casos"].corr(df_clean["temp_lag3"])
corr_umid = df_clean["casos"].corr(df_clean["umid_lag3"])
print(f"Correlação Casos vs. Temp. Média (Lag 3 sem): {corr_temp:.2f}")
print(f"Correlação Casos vs. Umidade Rel. (Lag 3 sem): {corr_umid:.2f}\n")


# 6. VISUALIZAÇÃO E METADADOS
sns.set_theme(style="whitegrid")
fig, (ax1, ax2) = plt.subplots(
    2,
    1,
    figsize=(13, 8.5),
    sharex=True,
    gridspec_kw={"height_ratios": [1.3, 1]},
)

# Painel 1: Incidência de Dengue
linha_casos = ax1.plot(
    df_clean["data"],
    df_clean["casos"],
    color="#d95f02",
    linewidth=2.2,
    marker="o",
    markersize=3.5,
    label="Casos Notificados (Semana t)",
)
ax1.fill_between(
    df_clean["data"], df_clean["casos"], color="#d95f02", alpha=0.18
)
ax1.set_ylabel(
    "Casos de Dengue (Semanal)", color="#d95f02", fontsize=11, fontweight="bold"
)
ax1.tick_params(axis="y", labelcolor="#d95f02")
ax1.legend(loc="upper left", frameon=True)

# Título Principal e Subtítulo Explicativo com a indicação do Lag
ax1.set_title(
    "Dinâmica Epidemiológica da Dengue vs. Variáveis Climáticas — Caxias do Sul/RS",
    fontsize=14,
    fontweight="bold",
    pad=18,
)
ax1.text(
    0.5,
    1.02,
    "Variáveis de temperatura e umidade com defasagem biológica de 3 semanas (Lag t - 3 sem)",
    transform=ax1.transAxes,
    ha="center",
    fontsize=10,
    color="#555555",
    style="italic",
)

# Caixa de Anotação Metodológica no Painel 1
texto_nota = (
    "Nota Metodológica:\n"
    "A defasagem de 3 semanas reflete o ciclo biológico do Aedes aegypti\n"
    "(eclosão, fase larval, incubação viral extrínseca e início dos sintomas)."
)
ax1.text(
    0.98,
    0.88,
    texto_nota,
    transform=ax1.transAxes,
    fontsize=8.5,
    ha="right",
    va="top",
    color="#333333",
    bbox=dict(
        boxstyle="round,pad=0.5",
        facecolor="#f8f9fa",
        edgecolor="#cccccc",
        alpha=0.9,
    ),
)

# Painel 2: Temperatura e Umidade com Eixo Duplo
cor_temp = "#cb181d"
cor_umid = "#2171b5"

linha_temp = ax2.plot(
    df_clean["data"],
    df_clean["temp_lag3"],
    color=cor_temp,
    linewidth=2.0,
    label="Temperatura Média (t - 3 sem) [°C]",
)
ax2.set_ylabel(
    "Temperatura (°C)", color=cor_temp, fontsize=11, fontweight="bold"
)
ax2.tick_params(axis="y", labelcolor=cor_temp)
ax2.set_xlabel("Semana Epidemiológica", fontsize=11)

ax2_twin = ax2.twinx()
linha_umid = ax2_twin.plot(
    df_clean["data"],
    df_clean["umid_lag3"],
    color=cor_umid,
    linewidth=1.8,
    linestyle="--",
    label="Umidade Relativa (t - 3 sem) [%]",
)
ax2_twin.set_ylabel(
    "Umidade Relativa (%)", color=cor_umid, fontsize=11, fontweight="bold"
)
ax2_twin.tick_params(axis="y", labelcolor=cor_umid)

# Legenda unificada para o eixo duplo no Painel 2
linhas_p2 = linha_temp + linha_umid
rotulos_p2 = [l.get_label() for l in linhas_p2]
ax2.legend(linhas_p2, rotulos_p2, loc="upper left", frameon=True)

# Delimitação precisa do eixo temporal
ax2.set_xlim(df_clean["data"].min(), df_clean["data"].max())

# Formatação temporal: marcas trimestrais
ax2.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b/%Y"))
fig.autofmt_xdate()

# Espaçamento para o rodapé
plt.tight_layout(rect=[0, 0.05, 1, 0.98])

# Inserção de Fonte e Autor no rodapé
fig.text(
    0.06,
    0.02,
    "Fonte: InfoDengue (Fiocruz / FGV) via SINAN/MS e ERA5/Copernicus",
    fontsize=9,
    color="#4a4a4a",
    style="italic",
    ha="left",
)

fig.text(
    0.94,
    0.02,
    "Autor: Gabriel Siqueira dos Santos",
    fontsize=9,
    color="#4a4a4a",
    fontweight="bold",
    ha="right",
)

# 7. EXPORTAÇÃO E EXIBIÇÃO
nome_saida = "grafico_resultado_dengue.png"
plt.savefig(nome_saida, dpi=300, bbox_inches="tight")
print(f"[OK] Gráfico final salvo com sucesso: {nome_saida}")
plt.show()