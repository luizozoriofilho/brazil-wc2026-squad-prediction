"""
=============================================================================
Copa 2026 — Análise de Forma Recente por Posição (Período Mar/26)
=============================================================================
Compara todos os jogadores dentro da mesma sub-posição usando métricas
de performance do período de março/2026:
  - Score clube ponderado por recência
  - Minutos recentes (últimas 4 janelas)
  - League tier (nível da liga)
  - Minutos pela seleção no ciclo Ancelotti
  - Score pela seleção ponderado

Score de Forma = 40%×score_clube + 25%×minutos_recentes + 20%×liga + 15%×NT

Saídas:
  copa2026_form_heatmap.png   — heatmap de performance por sub-posição
  copa2026_forma_vs_ancelotti — scatter forma × convocações Ancelotti
=============================================================================
"""

import warnings; warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from sklearn.preprocessing import MinMaxScaler
import os

DATA_PATH  = "call_up_history_brazil.csv"
OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

GREEN="#009C3B"; BLUE="#002776"; GRAY="#4A4A4A"; RED="#C0392B"
ORANGE="#E67E22"; PURPLE="#8E44AD"; YELLOW="#F39C12"; TEAL="#1A5276"

WINDOW_ORDER = [
    "01/03/2023","01/06/2023","01/09/2023","01/10/2023","01/11/2023",
    "01/03/2024","01/06/2024","01/09/2024","01/10/2024","01/11/2024",
    "01/03/2025","01/06/2025","01/09/2025","01/10/2025","01/11/2025","01/03/2026"
]
RECENCY_W   = dict(zip(WINDOW_ORDER, [
    0.02,0.04,0.06,0.08,0.10,0.15,0.20,0.25,
    0.30,0.35,0.40,0.60,0.70,0.80,0.90,1.00]))
ANC_W       = {"01/06/2025":0.60,"01/09/2025":0.70,"01/10/2025":0.80,
               "01/11/2025":0.90,"01/03/2026":1.00}
RECENT_WINS = ["01/09/2025","01/10/2025","01/11/2025","01/03/2026"]

TIER_SCORE  = {1.0:5,2.0:4,3.0:5,4.0:3,9.0:2}
TIER_MANUAL = {"Bento1999":1,"Ibañez1998":1,"Fabinho1993":1,
               "Ederson1993":3,"GabrielSara1999":3,
               "DouglasSantos1994":2,"LuizHenrique2001":2}

CB_RIGHT={"Bremer1997","FabrícioBruno1996","Marquinhos1994",
          "Ibañez1998","Nino1997","ÉderMilitão1998"}
CB_LEFT={"AlexsandroRibeiro1999","GabrielMagalhães1997","LeoPereira1996",
         "LucasBeraldo2003","Murillo2002","RobertRenan2003","Murilo1997","LéoOrtiz1996"}
RB={"Danilo1991","EmersonRoyal1999","Vanderson2001",
    "YanCouto2002","Wesley2003","Kaiki2003","Vitinho1999"}
LB={"AlexTelles1992","RenanLodi1998","AyrtonLucas1997","CaioHenrique1997",
    "CarlosAugusto1999","Wendell1993","Abner2000","AlexSandro1991",
    "DouglasSantos1994","William1995","GuilhermeArana1997","Arthur2003",
    "PauloHenrique1996","LucianoJuba1999"}

def pos_group(pid, pos):
    if pos=="Centre-back": return "CB_R" if pid in CB_RIGHT else "CB_L"
    if pos=="Full-back":   return "RB"   if pid in RB else "LB"
    return pos

def wa(v,w):
    m=~np.isnan(v); return np.average(v[m],weights=w[m]) if m.sum()>0 else np.nan
def ws(v,w):
    m=~np.isnan(v); return float(np.dot(np.array(v)[m],np.array(w)[m])) if m.sum()>0 else 0.0


def build_form_dataset(df, df_anc_orig, canonical_pos):
    rows = []
    for pid, grp in df.groupby("player_id"):
        grp  = grp.sort_values("date_call_up")
        last = grp.iloc[-1]
        pos  = canonical_pos.get(pid,"Forward")
        pg   = pos_group(pid, pos)

        n_anc    = len(df_anc_orig[df_anc_orig["player_id"]==pid])
        in_mar26 = int(len(grp[grp["month_matches"]=="01/03/2026"])>0)

        # Score clube — recency-weighted (todas janelas)
        v_sc = grp["avg_score_club"].values.astype(float)
        w_sc = grp["recency_w"].values.astype(float)
        w_avg_sc = wa(v_sc, w_sc)

        # Score clube — apenas últimas 4 janelas
        rec = grp[grp["month_matches"].isin(RECENT_WINS)]
        avg_sc_recent = wa(rec["avg_score_club"].values.astype(float),
                           rec["recency_w"].values.astype(float)) if len(rec)>0 else np.nan
        min_recent = rec["minutes_played_club"].sum() if len(rec)>0 else 0

        # League tier
        lt_enc = TIER_MANUAL.get(pid, None)
        if lt_enc is None:
            lt_row = grp[grp["month_matches"]=="01/03/2026"]["league_tier"]
            if len(lt_row)==0: lt_row = grp["league_tier"].dropna()
            lt_raw = float(lt_row.values[0]) if len(lt_row)>0 and not pd.isna(lt_row.values[0]) else np.nan
            lt_enc = TIER_SCORE.get(lt_raw, 1)

        # NT no ciclo Ancelotti
        anc_rows = grp[grp["month_matches"].isin(ANC_W.keys())]
        tmnt_anc = anc_rows["minutes_played_national_team"].sum()
        wmnt     = ws(grp["minutes_played_national_team"].values.astype(float), w_sc)
        asnt_anc = wa(anc_rows["avg_score_national_team"].values.astype(float),
                      anc_rows["recency_w"].values.astype(float))

        rows.append(dict(
            player_id=pid, player_name=last["player_name"],
            pos=pos, pos_group=pg, n_anc=n_anc, in_mar26=in_mar26,
            w_avg_sc=w_avg_sc, avg_sc_recent=avg_sc_recent,
            min_recent=min_recent, lt_enc=lt_enc,
            tmnt_anc=tmnt_anc, wmnt=wmnt, asnt_anc=asnt_anc,
        ))

    pdf = pd.DataFrame(rows)
    for col in ["w_avg_sc","avg_sc_recent","asnt_anc"]:
        pdf[col] = pdf.groupby("pos_group")[col].transform(lambda x: x.fillna(x.median()))

    # Form score normalizado por sub-posição
    scaler = MinMaxScaler()
    parts  = []
    for pg, g in pdf.groupby("pos_group"):
        sub   = g[["avg_sc_recent","min_recent","lt_enc","wmnt"]].fillna(0)
        normd = scaler.fit_transform(sub) if sub.shape[0]>1 else np.zeros((1,4))
        score = normd @ [0.40, 0.25, 0.20, 0.15]
        parts.append(pd.Series(score*100, index=g.index))
    pdf["form_score"] = pd.concat(parts).sort_index()
    return pdf


def plot_heatmap(pdf):
    ORDER    = ["Goalkeeper","CB_R","CB_L","RB","LB","Midfielder","Forward"]
    PG_PT    = {"Goalkeeper":"Goleiro","CB_R":"Zag. Dir.","CB_L":"Zag. Esq.",
                "RB":"Lat. Dir.","LB":"Lat. Esq.","Midfielder":"Meia","Forward":"Atacante"}
    PG_COLOR = {"Goalkeeper":GREEN,"CB_R":BLUE,"CB_L":TEAL,"RB":ORANGE,
                "LB":YELLOW,"Midfielder":PURPLE,"Forward":RED}
    FEAT_COLS   = ["avg_sc_recent","min_recent","lt_enc","wmnt","asnt_anc","form_score"]
    FEAT_LABELS = ["Score\nClube","Min.\nRecentes","Liga\n(tier)","Min.\nNT","Score\nNT","Forma\nTotal"]

    from matplotlib.colors import LinearSegmentedColormap
    widths = [len(pdf[pdf["pos_group"]==pg]) for pg in ORDER]
    fig, axes = plt.subplots(1, len(ORDER), figsize=(26,10),
                             gridspec_kw={"width_ratios": widths})
    fig.suptitle("Comparação de Performance por Posição — Período de Março/2026\n"
                 "Score de Forma: 40% score clube · 25% minutos · 20% liga · 15% NT",
                 fontsize=11, fontweight="bold", color=BLUE, y=1.01)

    scaler = MinMaxScaler()
    for ax, pg in zip(axes, ORDER):
        grp  = pdf[pdf["pos_group"]==pg].sort_values("form_score",ascending=False).copy()
        cmap = LinearSegmentedColormap.from_list("pos",["#FFFFFF", PG_COLOR[pg]])
        mat  = grp[FEAT_COLS].copy()
        for col in FEAT_COLS:
            mn, mx = mat[col].min(), mat[col].max()
            mat[col] = (mat[col]-mn)/(mx-mn) if mx>mn else 0.5
        ax.imshow(mat.values, aspect="auto", cmap=cmap, vmin=0, vmax=1)
        ax.set_xticks(range(len(FEAT_LABELS)))
        ax.set_xticklabels(FEAT_LABELS, fontsize=6.5)
        labels = []
        for _, r in grp.iterrows():
            tag = "✓" if r["in_mar26"] else ""
            anc = f"({int(r['n_anc'])}✦)" if r["n_anc"]>0 else "(0)"
            labels.append(f"{r['player_name'][:18]} {anc}{tag}")
        ax.set_yticks(range(len(grp))); ax.set_yticklabels(labels, fontsize=6.5)
        ax.set_title(PG_PT[pg], fontsize=8, fontweight="bold", color=BLUE, pad=4)
        vals_fmt = [("avg_sc_recent",".0f"),("min_recent",".0f"),("lt_enc",".0f"),
                    ("wmnt",".0f"),("asnt_anc",".0f"),("form_score",".1f")]
        for i,(_, r) in enumerate(grp.iterrows()):
            for j,(col,fmt) in enumerate(vals_fmt):
                v = r[col] if not pd.isna(r[col]) else 0
                ax.text(j,i,format(v,fmt),ha="center",va="center",fontsize=5.5,
                        color="black" if mat.values[i,j]<0.6 else "white")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/copa2026_form_heatmap.png",dpi=150,bbox_inches="tight")
    plt.close()
    print("[FORM] copa2026_form_heatmap.png salvo.")


def plot_scatter(pdf):
    ORDER  = ["Goalkeeper","CB_R","CB_L","RB","LB","Midfielder","Forward"]
    PG_PT  = {"Goalkeeper":"Goleiro","CB_R":"Zag. Dir.","CB_L":"Zag. Esq.",
              "RB":"Lat. Dir.","LB":"Lat. Esq.","Midfielder":"Meia","Forward":"Atacante"}
    fig, axes = plt.subplots(2,4,figsize=(20,10))
    axes = axes.flatten()
    fig.suptitle("Forma Recente × Chamadas Ancelotti — Possíveis Surpresas\n"
                 "Quadrante sup. esquerdo = alto form, baixo histórico Ancelotti",
                 fontsize=11, fontweight="bold", color=BLUE)
    for ax, pg in zip(axes[:len(ORDER)], ORDER):
        g  = pdf[pdf["pos_group"]==pg].copy()
        sc = [GREEN if r["in_mar26"] else RED for _,r in g.iterrows()]
        ax.scatter(g["n_anc"], g["form_score"], c=sc, s=80,
                   alpha=0.85, edgecolors="white", lw=0.5, zorder=3)
        for _, r in g.iterrows():
            ax.annotate(r["player_name"].split()[0],
                        xy=(r["n_anc"],r["form_score"]),
                        fontsize=6.5, ha="left", va="bottom",
                        xytext=(2,2), textcoords="offset points")
        ax.axvline(1.5,color=GRAY,linestyle="--",alpha=0.4,lw=1)
        ax.axhline(g["form_score"].median(),color=GRAY,linestyle="--",alpha=0.4,lw=1)
        ax.set_xlabel("Convocações Ancelotti",fontsize=8)
        ax.set_ylabel("Score de Forma (0-100)",fontsize=8)
        ax.set_title(PG_PT[pg],fontweight="bold",color=BLUE,fontsize=9)
        ax.legend(handles=[mpatches.Patch(color=GREEN,label="Mar/26"),
                            mpatches.Patch(color=RED,  label="Fora")],fontsize=7)
        ax.grid(alpha=0.25)
    axes[len(ORDER)].axis("off")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/copa2026_forma_vs_ancelotti.png",dpi=150,bbox_inches="tight")
    plt.close()
    print("[FORM] copa2026_forma_vs_ancelotti.png salvo.")


if __name__ == "__main__":
    df = pd.read_csv(DATA_PATH, sep=";")
    for col in ["original_call_up_list","out_injury","replacement","is_currently_injured"]:
        df[col] = (df[col]=="x").astype(int)
    df["recency_w"] = df["month_matches"].map(RECENCY_W)

    canonical_pos = (df.groupby(["player_id","player_main_position"]).size()
        .reset_index(name="n").sort_values("n",ascending=False)
        .drop_duplicates("player_id").set_index("player_id")["player_main_position"])
    df_anc = df[(df["coach"]=="Carlo Ancelotti")&(df["original_call_up_list"]==1)]

    print("[FORM] Calculando scores de forma...")
    form_df = build_form_dataset(df, df_anc, canonical_pos)
    form_df.to_csv(f"{OUTPUT_DIR}/copa2026_form_scores.csv", index=False)

    plot_heatmap(form_df)
    plot_scatter(form_df)
    print("[FORM] Concluído.")
