"""
=============================================================================
Copa 2026 — Gráficos Auxiliares para o Relatório
=============================================================================
Gera dois gráficos usados no PDF do relatório:
  pipeline_diagram.png — arquitetura completa do pipeline (6 etapas)
  skills_radar.png     — radar de competências demonstradas no projeto

Não depende dos dados — pode ser executado de forma independente.
=============================================================================
"""

import warnings; warnings.filterwarnings("ignore")
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import os

OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

BLUE="#002776"; GREEN="#009C3B"; GRAY="#4A4A4A"
ORANGE="#E67E22"; RED="#C0392B"; PURPLE="#8E44AD"


def plot_pipeline_diagram():
    """Diagrama de arquitetura do pipeline em 6 etapas."""
    fig, ax = plt.subplots(figsize=(16, 6))
    ax.set_xlim(0, 16); ax.set_ylim(0, 6); ax.axis("off")

    boxes = [
        (1.0, 3.0, "DATA\nSOURCES",
         "Sofascore\nTransfermarkt\nCBF Calendar", BLUE),
        (3.8, 3.0, "DATA\nCLEANING",
         "player_id keys\nDuplicate removal\nFlag encoding", GRAY),
        (6.6, 3.0, "FEATURE\nENGINEERING",
         "20 features\n4 groups\nRecency weights", ORANGE),
        (9.4, 3.0, "ML MODEL\n(Regression)",
         "Gradient Boosting\nR²=0.999 · MAE=0.006\n5-Fold CV", GREEN),
        (12.2, 3.0, "ILP\nOPTIMIZATION",
         "PuLP + CBC\nPosition quotas\nOverrides", PURPLE),
        (15.0, 3.0, "SQUAD\nPREDICTION",
         "26 players\nSub-position\nconstrained", RED),
    ]

    for x, y, title, sub, color in boxes:
        bbox = FancyBboxPatch((x-1.2, y-1.2), 2.2, 2.4,
                              boxstyle="round,pad=0.1", linewidth=2,
                              edgecolor=color, facecolor=color+"22")
        ax.add_patch(bbox)
        ax.text(x-0.1, y+0.55, title, ha="center", va="center",
                fontsize=9, fontweight="bold", color=color)
        ax.text(x-0.1, y-0.3, sub, ha="center", va="center",
                fontsize=7, color=GRAY, linespacing=1.4)

    for i in range(len(boxes)-1):
        x1 = boxes[i][0]+1.1; x2 = boxes[i+1][0]-1.2
        ax.annotate("", xy=(x2, 3.0), xytext=(x1, 3.0),
                    arrowprops=dict(arrowstyle="->", lw=2, color=GRAY))

    ax.text(8.0, 5.6,
            "ML Pipeline — Brazil 2026 World Cup Squad Prediction",
            ha="center", fontsize=13, fontweight="bold", color=BLUE)
    ax.text(8.0, 0.2,
            "10 iterative versions · 422 records · 91 players · 16 FIFA windows · 4 managers",
            ha="center", fontsize=9, color=GRAY)
    ax.text(0.4, 5.0, "v1→v10\ncorrections", fontsize=7.5, color=GRAY, style="italic")
    ax.annotate("", xy=(8.0, 5.2), xytext=(0.9, 5.0),
                arrowprops=dict(arrowstyle="->", lw=1, color=GRAY, linestyle="dashed"))

    plt.tight_layout()
    path = f"{OUTPUT_DIR}/pipeline_diagram.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[AUX] {path} salvo.")


def plot_skills_radar():
    """Radar de competências demonstradas no projeto."""
    skills = [
        "Feature\nEngineering", "ML\nModeling", "Data\nCleaning",
        "Optimization\n(ILP)", "Business\nTranslation", "Statistical\nReasoning"
    ]
    values = [0.92, 0.88, 0.90, 0.85, 0.82, 0.88]
    N      = len(skills)
    values_plot = values + values[:1]
    angles = [n / float(N) * 2 * np.pi for n in range(N)] + [0]

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
    ax.plot(angles, values_plot, "o-", lw=2, color=GREEN)
    ax.fill(angles, values_plot, alpha=0.25, color=GREEN)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(skills, size=9, fontweight="bold")
    ax.set_ylim(0, 1)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["25%","50%","75%","100%"], size=7, color=GRAY)
    ax.set_title("Skills Demonstrated in this Project",
                 size=12, fontweight="bold", color=BLUE, pad=20)
    ax.spines["polar"].set_color(GRAY)
    ax.grid(color=GRAY, alpha=0.3)

    plt.tight_layout()
    path = f"{OUTPUT_DIR}/skills_radar.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[AUX] {path} salvo.")


if __name__ == "__main__":
    plot_pipeline_diagram()
    plot_skills_radar()
    print("[AUX] Gráficos auxiliares gerados.")
