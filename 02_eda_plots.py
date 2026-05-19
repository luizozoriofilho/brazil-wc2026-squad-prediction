"""
=============================================================================
Copa 2026 — Análise Exploratória de Dados (EDA)
=============================================================================
Gera 4 gráficos exploratórios:
  eda_01_overview.png    — Convocações por janela, posição e técnico
  eda_02_dists.png       — Distribuição das features-chave por classe
  eda_03_correlation.png — Matriz de correlação features × target
  eda_04_top_players.png — Top 20 por conv. Ancelotti e score clube

Dependências: matplotlib, seaborn, pandas, numpy
Executar após 01_pipeline_copa2026.py (usa o CSV e o DataFrame de features)
=============================================================================
"""

import warnings; warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns
import os

# ── CONFIGURAÇÃO ──────────────────────────────────────────────────────────────
DATA_PATH  = "call_up_history_brazil.csv"
FEATS_PATH = "outputs/copa2026_predictions.csv"   # gerado por 01_pipeline
OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

GREEN="#009C3B"; BLUE="#002776"; GRAY="#4A4A4A"
RED="#C0392B";  ORANGE="#E67E22"; YELLOW="#F39C12"

WINDOW_ORDER = [
    "01/03/2023","01/06/2023","01/09/2023","01/10/2023","01/11/2023",
    "01/03/2024","01/06/2024","01/09/2024","01/10/2024","01/11/2024",
    "01/03/2025","01/06/2025","01/09/2025","01/10/2025","01/11/2025","01/03/2026"
]
WLABELS = [
    "Mar/23","Jun/23","Set/23","Out/23","Nov/23",
    "Mar/24","Jun/24","Set/24","Out/24","Nov/24",
    "Mar/25","Jun/25","Set/25","Out/25","Nov/25","Mar/26"
]
ANCELOTTI_W = {"01/06/2025","01/09/2025","01/10/2025","01/11/2025","01/03/2026"}
WCOLORS = [GREEN if w in ANCELOTTI_W else BLUE for w in WINDOW_ORDER]

COACHES_ORDER = ["Ramon Menezes","Fernando Diniz","Dorival Júnior","Carlo Ancelotti"]
COACH_COLORS  = [GRAY, GRAY, BLUE, GREEN]

sns.set_style("whitegrid")
plt.rcParams.update({"font.size": 10})


def load_data():
    df = pd.read_csv(DATA_PATH, sep=";")
    for col in ["original_call_up_list", "out_injury", "replacement"]:
        df[col] = (df[col] == "x").astype(int)
    pdf = pd.read_csv(FEATS_PATH)
    return df, pdf


def plot_overview(df):
    """Fig 1 — Visão geral: janelas, posições, técnicos."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle("EDA — Visão Geral das Convocações (2023–2026)",
                 fontsize=14, fontweight="bold", color=BLUE)

    conv = df.groupby("month_matches")["player_id"].count().reindex(WINDOW_ORDER)
    axes[0].bar(range(16), conv.values, color=WCOLORS)
    axes[0].set_xticks(range(16))
    axes[0].set_xticklabels(WLABELS, fontsize=7, rotation=45, ha="right")
    axes[0].set_title("Convocados por Janela", fontweight="bold", color=BLUE)
    axes[0].set_ylabel("Nº jogadores")
    axes[0].legend(handles=[
        mpatches.Patch(color=GREEN, label="Ancelotti"),
        mpatches.Patch(color=BLUE,  label="Técnicos anteriores")
    ], fontsize=9)

    pos_cnt = df[df["original_call_up_list"]==1]["player_main_position"].value_counts()
    axes[1].pie(pos_cnt.values, labels=pos_cnt.index, autopct="%1.0f%%",
                colors=[GREEN, BLUE, YELLOW, ORANGE, RED][:len(pos_cnt)],
                startangle=90, textprops={"fontsize": 9})
    axes[1].set_title("Por Posição (lista original)", fontweight="bold", color=BLUE)

    c_cnt = df[df["original_call_up_list"]==1].groupby("coach")["player_id"].count()
    axes[2].barh(
        [c.replace(" ", "\n") for c in COACHES_ORDER],
        [c_cnt.get(c, 0) for c in COACHES_ORDER],
        color=COACH_COLORS
    )
    axes[2].set_title("Convocações por Técnico", fontweight="bold", color=BLUE)
    axes[2].set_xlabel("Nº convocações")
    for i, v in enumerate([c_cnt.get(c, 0) for c in COACHES_ORDER]):
        axes[2].text(v + 0.5, i, str(v), va="center", fontweight="bold")

    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/eda_01_overview.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("[EDA] eda_01_overview.png salvo.")


def plot_feature_dists(pdf):
    """Fig 2 — Distribuição das features mais discriminativas por classe."""
    features = [
        ("n_anc",    "Conv. Ancelotti"),
        ("avg_sr",   "Taxa Titular Anc."),
        ("w_avg_sc", "Score Clube Pond."),
        ("tmnt",     "Min. Seleção (ciclo)"),
    ]
    # Usa coluna 'in_mar26' (1 = estava em Mar/26) se existir; senão usa target > 0.5
    target_col = "in_mar26" if "in_mar26" in pdf.columns else None
    if target_col is None:
        pdf = pdf.copy()
        pdf["_cls"] = (pdf["target"] > 0.5).astype(int)
        target_col = "_cls"

    fig, axes = plt.subplots(1, 4, figsize=(18, 5))
    fig.suptitle("EDA — Features-Chave por Classe (Mar/26)",
                 fontsize=13, fontweight="bold", color=BLUE)

    for ax, (feat, lbl) in zip(axes, features):
        g0 = pdf[pdf[target_col] == 0][feat].dropna()
        g1 = pdf[pdf[target_col] == 1][feat].dropna()
        ax.hist(g0, bins=15, alpha=0.65, color=GRAY,  label="Não conv.", density=True)
        ax.hist(g1, bins=15, alpha=0.75, color=GREEN, label="Convocado",  density=True)
        ax.axvline(g0.mean(), color=GRAY,  linestyle="--", lw=1.5)
        ax.axvline(g1.mean(), color=GREEN, linestyle="--", lw=1.5)
        ax.set_title(lbl, fontweight="bold")
        ax.set_xlabel("Valor"); ax.set_ylabel("Densidade")
        ax.legend(fontsize=9)

    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/eda_02_dists.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("[EDA] eda_02_dists.png salvo.")


def plot_correlation(pdf):
    """Fig 3 — Matriz de correlação features × target."""
    FEATURES = [
        "n_anc","mean_rec","coverage","called_l3","avg_sr","anc_mpw",
        "w_avg_sc","w_min_c","avg_gpc","lt_enc","inj",
        "tmnt","wmnt","tgnt","asnt","comp_w",
        "has_alt","nct","rep_rate","age","target"
    ]
    available = [f for f in FEATURES if f in pdf.columns]
    corr = pdf[available].corr()
    mask = np.triu(np.ones_like(corr, dtype=bool))
    cmap = LinearSegmentedColormap.from_list("br", ["#C0392B", "#FFFFFF", "#009C3B"])

    fig, ax = plt.subplots(figsize=(14, 11))
    sns.heatmap(corr, mask=mask, cmap=cmap, center=0, vmin=-1, vmax=1,
                annot=True, fmt=".2f", linewidths=0.5, ax=ax, annot_kws={"size": 7})
    ax.set_title("Matriz de Correlação — Features + Target",
                 fontsize=13, fontweight="bold", color=BLUE, pad=12)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/eda_03_correlation.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("[EDA] eda_03_correlation.png salvo.")


def plot_top_players(pdf):
    """Fig 4 — Top 20 por conv. Ancelotti e score clube ponderado."""
    target_col = "in_mar26" if "in_mar26" in pdf.columns else "selected"
    if target_col not in pdf.columns:
        pdf = pdf.copy(); pdf["_t"] = (pdf["target"] > 0.5).astype(int); target_col = "_t"

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    fig.suptitle("EDA — Top Jogadores", fontsize=13, fontweight="bold", color=BLUE)

    for ax, (col, lbl) in zip(axes, [("n_anc", "Conv. Ancelotti"),
                                      ("w_avg_sc", "Score Clube Pond.")]):
        top = pdf.nlargest(20, col)[["player_name", col, target_col]]
        bc  = [GREEN if c == 1 else BLUE for c in top[target_col]]
        ax.barh(top["player_name"][::-1], top[col][::-1], color=bc[::-1])
        ax.set_title(f"Top 20 — {lbl}", fontweight="bold")
        ax.set_xlabel(lbl)
        ax.legend(handles=[
            mpatches.Patch(color=GREEN, label="Conv. Mar/26 ou Selecionado"),
            mpatches.Patch(color=BLUE,  label="Não selecionado")
        ], fontsize=9)

    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/eda_04_top_players.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("[EDA] eda_04_top_players.png salvo.")


if __name__ == "__main__":
    print("[EDA] Carregando dados...")
    df, pdf = load_data()
    plot_overview(df)
    plot_feature_dists(pdf)
    plot_correlation(pdf)
    plot_top_players(pdf)
    print("[EDA] Todos os gráficos gerados.")
