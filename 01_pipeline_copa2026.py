"""
=============================================================================
Copa do Mundo FIFA 2026 — Previsão de Convocação | Pipeline Principal (v10)
=============================================================================
Autor      : Luiz Eduardo
Dataset    : call_up_history_brazil.csv (422 linhas, 91 jogadores, 16 janelas)
Período    : 19/12/2022 – 31/03/2026  |  Técnico Copa: Carlo Ancelotti
Modelo     : Gradient Boosting Regressor
Target     : Média ponderada de recência das janelas Ancelotti
             (denominador ajustado para Alisson, Ederson e Bremer — lesão abonada)
Otimização : ILP via PuLP — cotas por sub-posição (lado do campo)
=============================================================================
Correções documentadas (v1 → v10):
  v1  player_id como chave primária (não player_name)
  v2  Target reformulado: weighted Ancelotti presence (não binário)
  v3  Posição canônica: mais frequente por player_id
  v4  Hugo Souza corrigido: cobertura por lista original; feature anc_min_per_win
  v5  Zagueiros separados por lado: CB_R / CB_L
  v6  Laterais separados por lado: RB / LB
  v7  Penalidade n=1 global rejeitada (efeitos colaterais)
  v8  Ajuste de denominador apenas para Alisson e Ederson
  v9  Bremer adicionado ao ajuste por lesão
  v10 Neymar: probabilidade 0.40 baseada em análise de notícias (16/05/2026)
=============================================================================
"""

import warnings; warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import pulp
import os
from datetime import datetime
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.metrics import r2_score

# ── CONFIGURAÇÃO ──────────────────────────────────────────────────────────────
DATA_PATH = "call_up_history_brazil.csv"   # ajuste o caminho se necessário
OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

WC_DATE = datetime(2026, 6, 11)   # início da Copa 2026

# Janelas FIFA e pesos de recência
WINDOW_ORDER = [
    "01/03/2023","01/06/2023","01/09/2023","01/10/2023","01/11/2023",
    "01/03/2024","01/06/2024","01/09/2024","01/10/2024","01/11/2024",
    "01/03/2025","01/06/2025","01/09/2025","01/10/2025","01/11/2025","01/03/2026"
]
RECENCY_W = dict(zip(WINDOW_ORDER, [
    0.02, 0.04, 0.06, 0.08, 0.10, 0.15, 0.20, 0.25,
    0.30, 0.35, 0.40, 0.60, 0.70, 0.80, 0.90, 1.00
]))

# Janelas do Ancelotti com pesos individuais
ANC_W = {
    "01/06/2025": 0.60,
    "01/09/2025": 0.70,
    "01/10/2025": 0.80,
    "01/11/2025": 0.90,
    "01/03/2026": 1.00,
}
TOTAL_ANC_W = sum(ANC_W.values())   # 4.00
LAST3_W = {"01/09/2025", "01/10/2025", "01/11/2025"}

# League tier encoding (valores numéricos no CSV)
# 1=Premier League, 2=Serie A, 3=La Liga, 4=Ligue 1, 9=Brasil
TIER_SCORE = {1.0: 5, 2.0: 4, 3.0: 5, 4.0: 3, 9.0: 2}

# Override manual de league_tier para 7 jogadores com ligas não mapeadas
TIER_MANUAL = {
    "Bento1999"         : 1,   # Al-Nassr (Arábia Saudita)
    "Ibañez1998"        : 1,   # Al-Ahli (Arábia Saudita)
    "Fabinho1993"       : 1,   # Al-Ittihad (Arábia Saudita)
    "Ederson1993"       : 3,   # Fenerbahçe (Turquia → other_europe)
    "GabrielSara1999"   : 3,   # Galatasaray (Turquia → other_europe)
    "DouglasSantos1994" : 2,   # Zenit (Rússia → other)
    "LuizHenrique2001"  : 2,   # Zenit (Rússia → other)
}

# ── CLASSIFICAÇÃO POR LADO DO CAMPO ──────────────────────────────────────────
# Full-backs
RIGHT_BACKS = {
    "Danilo1991", "EmersonRoyal1999", "Vanderson2001",
    "YanCouto2002", "Wesley2003", "Kaiki2003", "Vitinho1999"
}
LEFT_BACKS = {
    "AlexTelles1992", "RenanLodi1998", "AyrtonLucas1997", "CaioHenrique1997",
    "CarlosAugusto1999", "Wendell1993", "Abner2000", "AlexSandro1991",
    "DouglasSantos1994", "William1995", "GuilhermeArana1997", "Arthur2003",
    "PauloHenrique1996", "LucianoJuba1999"
}

# Centre-backs (conforme lista fornecida pelo especialista de domínio)
CB_RIGHT = {
    "Bremer1997", "FabrícioBruno1996", "Marquinhos1994",
    "Ibañez1998", "Nino1997", "ÉderMilitão1998"
}
CB_LEFT = {
    "AlexsandroRibeiro1999", "GabrielMagalhães1997", "LeoPereira1996",
    "LucasBeraldo2003", "Murillo2002", "RobertRenan2003",
    "Murilo1997", "LéoOrtiz1996"
}

def get_pos_group(player_id: str, position: str) -> str:
    """Mapeia player_id + posição para grupo de sub-posição do ILP."""
    if position == "Centre-back":
        return "CB_R" if player_id in CB_RIGHT else "CB_L"
    if position == "Full-back":
        return "RB" if player_id in RIGHT_BACKS else "LB"
    return position   # Goalkeeper, Midfielder, Forward


# ── AJUSTE DE DENOMINADOR POR LESÃO ──────────────────────────────────────────
# Para estes jogadores, ausências em janelas Ancelotti são comprovadamente por lesão.
# O denominador do target usa n_chamado em vez de TOTAL_ANC_W (4.00).
INJURY_ADJUSTED = {"Alisson1992", "Ederson1993", "Bremer1997"}


# ── OVERRIDES MANUAIS (aplicados após predição do modelo, antes do ILP) ───────
OVERRIDES = {
    "Danilo1991"      : 1.00,   # confirmado publicamente por Ancelotti
    "Neymar1992"      : 0.40,   # análise de notícias 16/05/2026 (ver 09_neymar_analysis.py)
    "Rodrygo2001"     : 0.00,   # lesão confirmada
    "ÉderMilitão1998" : 0.00,   # lesão confirmada
    "Estêvão2007"     : 0.00,   # lesão confirmada (7 convocações Ancelotti)
}

# ── COTAS ILP POR SUB-POSIÇÃO ─────────────────────────────────────────────────
ILP_QUOTAS = {
    "Goalkeeper" : (3, 3),   # fixo
    "CB_R"       : (2, 2),   # zagueiro direito
    "CB_L"       : (2, 2),   # zagueiro esquerdo
    "RB"         : (2, 2),   # lateral direito (Danilo garantido + 1)
    "LB"         : (2, 2),   # lateral esquerdo
    "Midfielder" : (4, 6),   # flexível
    "Forward"    : (9, 11),  # restante
}


# =============================================================================
# 1. CARREGAR E PRÉ-PROCESSAR DADOS
# =============================================================================
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";")
    df["date_call_up"] = pd.to_datetime(df["date_call_up"], format="mixed")
    df["birth_date"]   = pd.to_datetime(df["birth_date"], dayfirst=True)
    for col in ["original_call_up_list", "out_injury", "replacement", "is_currently_injured"]:
        df[col] = (df[col] == "x").astype(int)
    df["recency_w"] = df["month_matches"].map(RECENCY_W)
    return df


def get_canonical_position(df: pd.DataFrame) -> pd.Series:
    """Posição mais frequente por player_id (evita confusão com jogadores polivalentes)."""
    return (
        df.groupby(["player_id", "player_main_position"])
          .size()
          .reset_index(name="n")
          .sort_values("n", ascending=False)
          .drop_duplicates("player_id")
          .set_index("player_id")["player_main_position"]
    )


# =============================================================================
# 2. VARIÁVEL-ALVO
# =============================================================================
def compute_target(player_id: str, df_anc_orig: pd.DataFrame) -> float:
    """
    Target = média ponderada de recência das janelas Ancelotti em que o jogador
    foi convocado na lista original.

    Para jogadores com lesão abonada (INJURY_ADJUSTED):
        target = sum(pesos janelas chamado) / n_chamado      (÷ n)
    Para todos os demais:
        target = sum(pesos janelas chamado) / TOTAL_ANC_W    (÷ 4.00)

    Isso elimina a penalidade por ausências causadas por lesão documentada
    sem afetar o cálculo dos demais jogadores.
    """
    called_weights = [
        w for win, w in ANC_W.items()
        if len(df_anc_orig[
            (df_anc_orig["player_id"] == player_id) &
            (df_anc_orig["month_matches"] == win)
        ]) > 0
    ]
    if not called_weights:
        return 0.0
    if player_id in INJURY_ADJUSTED:
        return sum(called_weights) / len(called_weights)   # ÷ n_chamado
    return sum(called_weights) / TOTAL_ANC_W               # ÷ 4.00


# =============================================================================
# 3. FEATURE ENGINEERING
# =============================================================================
def weighted_avg(values: np.ndarray, weights: np.ndarray) -> float:
    mask = ~np.isnan(values)
    return float(np.average(values[mask], weights=weights[mask])) if mask.sum() > 0 else np.nan

def weighted_sum(values: np.ndarray, weights: np.ndarray) -> float:
    mask = ~np.isnan(values)
    return float(np.dot(values[mask], weights[mask])) if mask.sum() > 0 else 0.0


def build_features(df: pd.DataFrame, df_anc_orig: pd.DataFrame,
                   canonical_pos: pd.Series) -> pd.DataFrame:
    """
    Agrega 422 linhas (jogador × janela) em 91 linhas (1 por jogador).
    Retorna DataFrame com todas as features e o target.

    Grupos de features:
      G1 — Ancelotti:  n_anc, mean_rec, coverage, called_l3, avg_sr, anc_mpw
      G2 — Clube:      w_avg_sc, w_min_c, avg_gpc, lt_enc, inj
      G3 — NT:         tmnt, wmnt, tgnt, asnt, comp_w
      G4 — Contexto:   has_alt, nct, rep_rate, age
    """
    rows = []

    for player_id, grp in df.groupby("player_id"):
        grp  = grp.sort_values("date_call_up")
        last = grp.iloc[-1]
        pos  = canonical_pos.get(player_id, "Forward")
        pg   = get_pos_group(player_id, pos)

        # Idade na Copa
        birth = last["birth_date"]
        age   = (WC_DATE - birth).days / 365.25 if pd.notna(birth) else np.nan

        # Target
        target = compute_target(player_id, df_anc_orig)

        # ── G1: Features Ancelotti ────────────────────────────────────────────
        ag       = df_anc_orig[df_anc_orig["player_id"] == player_id]
        n_anc    = len(ag)
        cw       = [w for win, w in ANC_W.items()
                    if len(df_anc_orig[(df_anc_orig["player_id"] == player_id) &
                                       (df_anc_orig["month_matches"] == win)]) > 0]
        mean_rec = sum(cw) / len(cw) if cw else 0.0
        coverage = sum(cw) / TOTAL_ANC_W
        called_l3 = int(any(
            len(df_anc_orig[(df_anc_orig["player_id"] == player_id) &
                            (df_anc_orig["month_matches"] == w)]) > 0
            for w in LAST3_W
        ))
        avg_sr = ag["starter_rate"].mean()
        avg_sr = 0.0 if pd.isna(avg_sr) else avg_sr

        # Minutos NT por janela Ancelotti disponível (captura GKs que nunca jogam)
        anc_rows    = grp[grp["month_matches"].isin(ANC_W.keys())]
        anc_nt_min  = anc_rows["minutes_played_national_team"].sum()
        anc_n_win   = max(len(anc_rows), 1)
        anc_mpw     = anc_nt_min / anc_n_win

        # ── G2: Forma pelo clube ──────────────────────────────────────────────
        v_sc      = grp["avg_score_club"].values.astype(float)
        w_sc      = grp["recency_w"].values.astype(float)
        w_avg_sc  = weighted_avg(v_sc, w_sc)
        w_min_c   = weighted_sum(grp["minutes_played_club"].values.astype(float), w_sc)
        avg_gpc   = grp["games_club"].mean()

        # League tier (Mar/26 prioritário, manual override se necessário)
        lt_enc = TIER_MANUAL.get(player_id, None)
        if lt_enc is None:
            lt_row = grp[grp["month_matches"] == "01/03/2026"]["league_tier"]
            lt_raw = (float(lt_row.values[0])
                      if len(lt_row) > 0 and not pd.isna(lt_row.values[0])
                      else np.nan)
            lt_enc = TIER_SCORE.get(lt_raw, 1)

        inj = int(grp["is_currently_injured"].max() == 1)

        # ── G3: Histórico pela Seleção ────────────────────────────────────────
        # Excluímos Mar/26 para NT features de treino (evitar leakage)
        gnt  = grp[grp["month_matches"] != "01/03/2026"]
        tmnt = gnt["minutes_played_national_team"].sum()
        wmnt = weighted_sum(
            gnt["minutes_played_national_team"].values.astype(float),
            gnt["recency_w"].values.astype(float)
        )
        tgnt  = gnt["games_nt"].sum()
        v_nt  = gnt["avg_score_national_team"].values.astype(float)
        w_nt  = gnt["recency_w"].values.astype(float)
        asnt  = weighted_avg(v_nt, w_nt)
        comp_map = {"friendly": 1, "world cup qualifiers": 3, "continental tournament": 2}
        comp_w = gnt["competition"].map(comp_map).mean()
        comp_w = 0.0 if pd.isna(comp_w) else comp_w

        # ── G4: Contexto ─────────────────────────────────────────────────────
        has_alt  = int(grp["player_first_alternative_position"].notna().any())
        nct      = len(grp)
        rep_rate = grp["replacement"].mean()

        rows.append(dict(
            player_id=player_id,
            player_name=last["player_name"],
            pos=pos,
            pos_group=pg,
            age=age,
            target=target,
            # G1
            n_anc=n_anc, mean_rec=mean_rec, coverage=coverage,
            called_l3=called_l3, avg_sr=avg_sr, anc_mpw=anc_mpw,
            # G2
            w_avg_sc=w_avg_sc, w_min_c=w_min_c, avg_gpc=avg_gpc,
            lt_enc=lt_enc, inj=inj,
            # G3
            tmnt=tmnt, wmnt=wmnt, tgnt=tgnt, asnt=asnt, comp_w=comp_w,
            # G4
            has_alt=has_alt, nct=nct, rep_rate=rep_rate,
        ))

    out = pd.DataFrame(rows)

    # Imputação de NaN (por posição para score clube; mediana geral para NT score)
    out["w_avg_sc"] = out.groupby("pos")["w_avg_sc"].transform(
        lambda x: x.fillna(x.median()))
    out["asnt"] = out["asnt"].fillna(out["asnt"].median())
    out["age"]  = out["age"].fillna(out["age"].median())

    return out


# =============================================================================
# 4. TREINO E AVALIAÇÃO DO MODELO
# =============================================================================
FEATURES = [
    "n_anc", "mean_rec", "coverage", "called_l3", "avg_sr", "anc_mpw",
    "w_avg_sc", "w_min_c", "avg_gpc", "lt_enc", "inj",
    "tmnt", "wmnt", "tgnt", "asnt", "comp_w",
    "has_alt", "nct", "rep_rate", "age"
]


def train_model(X: pd.DataFrame, y: pd.Series) -> Pipeline:
    """Treina Gradient Boosting Regressor com StandardScaler."""
    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("model", GradientBoostingRegressor(
            n_estimators=200, max_depth=3, learning_rate=0.05,
            subsample=0.8, random_state=42
        ))
    ])
    pipe.fit(X, y)
    return pipe


def evaluate_model(pipe: Pipeline, X: pd.DataFrame, y: pd.Series) -> dict:
    """Cross-validation 5-fold e métricas."""
    cv   = KFold(n_splits=5, shuffle=True, random_state=42)
    y_cv = cross_val_predict(pipe, X, y, cv=cv)
    r2   = r2_score(y, np.clip(y_cv, 0, 1))
    mae  = float(np.mean(np.abs(y - np.clip(y_cv, 0, 1))))
    print(f"[MODEL] R²={r2:.4f}  MAE={mae:.4f}")
    return {"r2": r2, "mae": mae}


# =============================================================================
# 5. PREDIÇÃO COPA 2026 + OVERRIDES
# =============================================================================
def predict_copa(pipe: Pipeline, pdf: pd.DataFrame) -> pd.DataFrame:
    """Aplica modelo e overrides manuais."""
    copa = pdf.copy()
    copa["prob"] = np.clip(pipe.predict(copa[FEATURES]), 0, 1)
    for pid, val in OVERRIDES.items():
        copa.loc[copa["player_id"] == pid, "prob"] = val
    return copa


# =============================================================================
# 6. ILP — SELEÇÃO DOS 26
# =============================================================================
def run_ilp(copa: pd.DataFrame) -> pd.DataFrame:
    """
    Maximiza soma das probabilidades selecionando exatamente 26 jogadores,
    respeitando cotas mínimas e máximas por sub-posição.
    """
    prob_d = copa.set_index("player_id")["prob"].to_dict()
    pg_d   = copa.set_index("player_id")["pos_group"].to_dict()
    pids   = copa["player_id"].tolist()

    prob_lp = pulp.LpProblem("Copa2026_Squad", pulp.LpMaximize)
    xv      = {p: pulp.LpVariable(f"x_{i}", cat="Binary")
               for i, p in enumerate(pids)}

    # Objetivo
    prob_lp += pulp.lpSum(prob_d[p] * xv[p] for p in pids)

    # Total de jogadores = 26
    prob_lp += pulp.lpSum(xv[p] for p in pids) == 26

    # Cotas por sub-posição
    for grp_name, (mn, mx) in ILP_QUOTAS.items():
        in_grp = [p for p in pids if pg_d[p] == grp_name]
        prob_lp += pulp.lpSum(xv[p] for p in in_grp) >= mn
        prob_lp += pulp.lpSum(xv[p] for p in in_grp) <= mx

    prob_lp.solve(pulp.PULP_CBC_CMD(msg=0))
    print(f"[ILP] Status: {pulp.LpStatus[prob_lp.status]}")

    selected = [p for p in pids if pulp.value(xv[p]) == 1]
    copa["selected"] = copa["player_id"].isin(selected).astype(int)
    return copa


# =============================================================================
# 7. MAIN
# =============================================================================
if __name__ == "__main__":
    print("=" * 65)
    print("COPA 2026 — PREVISÃO DE CONVOCAÇÃO | PIPELINE v10")
    print("=" * 65)

    # Carregar dados
    df = load_data(DATA_PATH)
    print(f"[LOAD] {len(df)} linhas | {df['player_id'].nunique()} jogadores únicos")

    # Sub-conjuntos úteis
    canonical_pos = get_canonical_position(df)
    df["pos_group"] = df["player_id"].apply(
        lambda pid: get_pos_group(pid, canonical_pos.get(pid, "Forward"))
    )
    df_anc_orig = df[
        (df["coach"] == "Carlo Ancelotti") & (df["original_call_up_list"] == 1)
    ]

    # Feature engineering
    print("\n[FE] Construindo features por jogador...")
    pdf = build_features(df, df_anc_orig, canonical_pos)
    print(f"[FE] {len(pdf)} jogadores | Target range: [{pdf['target'].min():.3f}, {pdf['target'].max():.3f}]")

    # Treino
    X = pdf[FEATURES].copy()
    y = pdf["target"].copy()
    print("\n[MODEL] Treinando Gradient Boosting Regressor...")
    pipe = train_model(X, y)
    metrics = evaluate_model(pipe, X, y)

    # Predição
    print("\n[PREDICT] Gerando probabilidades Copa 2026...")
    copa = predict_copa(pipe, pdf)

    # ILP
    print("\n[ILP] Otimizando lista de 26 jogadores...")
    copa = run_ilp(copa)

    # Resultado
    squad = copa[copa["selected"] == 1].sort_values(
        ["pos_group", "prob"], ascending=[True, False]
    )

    PG_PT = {
        "Goalkeeper": "Goleiro",    "CB_R": "Zag. Dir.", "CB_L": "Zag. Esq.",
        "RB": "Lat. Dir.",          "LB": "Lat. Esq.",
        "Midfielder": "Meia",       "Forward": "Atacante"
    }
    ORDER = ["Goalkeeper", "CB_R", "CB_L", "RB", "LB", "Midfielder", "Forward"]

    print("\n" + "=" * 65)
    print("LISTA PREVISTA — COPA 2026 (26 jogadores)")
    print("=" * 65)
    for pg in ORDER:
        grp = squad[squad["pos_group"] == pg]
        for _, r in grp.iterrows():
            ov = " [OVERRIDE]" if r["prob"] in [0.0, 0.40, 1.00] else ""
            print(f"  {PG_PT[pg]:<14} | {r['player_name']:<26} | "
                  f"prob={r['prob']:.3f} | n_anc={int(r['n_anc'])}{ov}")

    # Exportar resultados
    out_path = os.path.join(OUTPUT_DIR, "copa2026_predictions.csv")
    copa.sort_values("prob", ascending=False).to_csv(out_path, index=False)
    print(f"\n[SAVE] Resultado salvo em: {out_path}")
    print(f"[DONE] R²={metrics['r2']:.4f} | MAE={metrics['mae']:.4f}")
