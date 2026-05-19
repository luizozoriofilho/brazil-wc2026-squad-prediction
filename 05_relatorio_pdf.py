"""Build PT and EN versions of the enhanced report — v2 fixes."""
import warnings; warnings.filterwarnings("ignore")
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, PageBreak, HRFlowable, Image as RLImage, KeepTogether)
from datetime import datetime
from PIL import Image as PILImg
import os, sys

OUTDIR = "/mnt/user-data/outputs"
LANG   = sys.argv[1] if len(sys.argv)>1 else "pt"

BLUE  =colors.HexColor("#002776"); GREEN=colors.HexColor("#009C3B")
GRAY  =colors.HexColor("#4A4A4A"); RED  =colors.HexColor("#C0392B")
ORANGE=colors.HexColor("#E67E22"); PURPLE=colors.HexColor("#8E44AD")
LGRAY =colors.HexColor("#F5F5F5"); LLGREEN=colors.HexColor("#E8F5E9")
LLBLUE=colors.HexColor("#E3F2FD"); LLYELL=colors.HexColor("#FFFDE7")
SKILL_BG=colors.HexColor("#F3E5F5")

doc = SimpleDocTemplate(
    f"{OUTDIR}/copa2026_{'PT' if LANG=='pt' else 'EN'}.pdf",
    pagesize=A4, leftMargin=2*cm, rightMargin=2*cm,
    topMargin=2*cm, bottomMargin=2*cm)

sty = getSampleStyleSheet()
def ps(name, parent="Normal", **kw):
    return ParagraphStyle(name+LANG, parent=sty[parent], **kw)

# ── cell style: small text that wraps properly inside tables ──────────────────
cell_sty  = ps("cell",  fontSize=8,   leading=11, spaceAfter=0)
cell_bold = ps("cellb", fontSize=8,   leading=11, spaceAfter=0, fontName="Helvetica-Bold")
cell_hdr  = ps("cellh", fontSize=8,   leading=11, spaceAfter=0,
               fontName="Helvetica-Bold", textColor=colors.white)
cell_gray = ps("cellg", fontSize=8,   leading=11, spaceAfter=0, textColor=GRAY,
               fontName="Helvetica-Oblique")

S = {
    "cover_title": ps("ct","Title",fontSize=22,textColor=BLUE,alignment=TA_CENTER,spaceAfter=4,leading=28),
    "cover_sub"  : ps("cs",fontSize=12,textColor=GREEN,alignment=TA_CENTER,spaceAfter=3),
    "h1"         : ps("h1","Heading1",fontSize=13,textColor=BLUE,spaceBefore=14,spaceAfter=4,leading=17),
    "h2"         : ps("h2","Heading2",fontSize=10.5,textColor=GREEN,spaceBefore=9,spaceAfter=3),
    "body"       : ps("bd",fontSize=9.5,leading=14,spaceAfter=5,alignment=TA_JUSTIFY),
    "cap"        : ps("cp",fontSize=8,textColor=GRAY,alignment=TA_CENTER,spaceAfter=8),
    "bul"        : ps("bl",fontSize=9.5,leading=14,leftIndent=14,spaceAfter=3),
    "note"       : ps("nt",fontSize=8.5,textColor=GRAY,leading=12,spaceAfter=4,leftIndent=10),
    "code"       : ps("cd",fontName="Courier",fontSize=8,leading=11,spaceAfter=4,
                       leftIndent=10,backColor=colors.HexColor("#F8F8F8")),
    "skill_title": ps("sk",fontSize=10,textColor=BLUE,fontName="Helvetica-Bold",
                       spaceAfter=2,spaceBefore=4),
    "center"     : ps("cn",fontSize=9,alignment=TA_CENTER),
}

def hr(c=BLUE,w=1): return HRFlowable(width="100%",thickness=w,color=c,spaceAfter=5,spaceBefore=4)
def sp(n=8): return Spacer(1,n)
def P(t,s="body"): return Paragraph(t,S[s])
def B(t): return P(f"• {t}","bul")

def img(path, width=15*cm):
    try:
        with PILImg.open(path) as im: w,h=im.size
        return RLImage(path,width=width,height=width*h/w)
    except: return P(f"[img: {path}]","note")

def C(text, bold=False, gray=False, center=False):
    """Wrap table cell text in a Paragraph so it wraps cleanly."""
    if gray:   return Paragraph(str(text), cell_gray)
    if bold:   return Paragraph(str(text), cell_bold)
    if center:
        st = ps(f"cc{text[:4]}", fontSize=8, leading=11, spaceAfter=0, alignment=TA_CENTER)
        return Paragraph(str(text), st)
    return Paragraph(str(text), cell_sty)

def CH(text):
    """Header cell."""
    return Paragraph(str(text), cell_hdr)

def tbl(data, cws, hbg="#002776", alt="#F0F4FF", ac=None):
    """Build table. data[0] = header row; remaining = data rows.
       All cells are wrapped in Paragraph for clean word-wrap."""
    wrapped = []
    for ri, row in enumerate(data):
        wrow = []
        for ci, cell in enumerate(row):
            if isinstance(cell, str):
                if ri == 0:
                    wrow.append(CH(cell))
                else:
                    wrow.append(C(cell))
            else:
                wrow.append(cell)   # already a Paragraph/Flowable
        wrapped.append(wrow)

    t = Table(wrapped, colWidths=cws, repeatRows=1)
    st = [
        ("BACKGROUND",  (0,0), (-1,0),  colors.HexColor(hbg)),
        ("FONTSIZE",    (0,0), (-1,-1), 8),
        ("GRID",        (0,0), (-1,-1), 0.4, colors.HexColor("#CCCCCC")),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor(alt)]),
        ("VALIGN",      (0,0), (-1,-1), "TOP"),
        ("TOPPADDING",  (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 5),
        ("RIGHTPADDING",(0,0), (-1,-1), 5),
    ]
    if ac:
        for col, al in ac.items():
            st.append(("ALIGN", (col,0), (col,-1), al))
    t.setStyle(TableStyle(st))
    return t

def skill_box(skills_list, title):
    inner = [[C(f"{s[0]}: {s[1]}")] for s in skills_list]
    # Bold the skill name part manually
    inner2 = [[Paragraph(f"<b>{s[0]}</b>: {s[1]}", cell_sty)] for s in skills_list]
    inner_t = Table(
        [[Paragraph(f"<b>{title}</b>", S["skill_title"])]] + inner2,
        colWidths=[16*cm])
    inner_t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#EDE7F6")),
        ("BACKGROUND",(0,1),(-1,-1),SKILL_BG),
        ("BOX",(0,0),(-1,-1),1,PURPLE),
        ("TOPPADDING",(0,0),(-1,-1),5),
        ("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),8),
        ("RIGHTPADDING",(0,0),(-1,-1),8),
    ]))
    return inner_t

# ── TRANSLATIONS ──────────────────────────────────────────────────────────────
def t_cover_title():
    return ("SELEÇÃO BRASILEIRA\nCopa do Mundo FIFA 2026" if LANG=="pt"
            else "BRAZILIAN NATIONAL TEAM\nFIFA World Cup 2026")
def t_cover_sub():
    return ("Previsão de Convocação — Pipeline de Machine Learning (v10)" if LANG=="pt"
            else "Squad Selection Prediction — Machine Learning Pipeline (v10)")

story = []

# ═══════════════════════════════════════════════════════════════════════════════
# CAPA
# ═══════════════════════════════════════════════════════════════════════════════
story += [sp(20), P("⚽  "+t_cover_title(),"cover_title"), sp(6), hr(GREEN,2), sp(6)]
story += [P(t_cover_sub(),"cover_sub"), sp(4)]
author = ("Projeto de portfólio — Análise de Dados & Machine Learning" if LANG=="pt"
          else "Portfolio project — Data Analytics & Machine Learning")
story += [P(author,"center"), sp(12)]

capa_rows = ([["Técnico","Carlo Ancelotti (desde junho/2025)"],
              ["Período","19/12/2022 – 31/03/2026"],
              ["Dataset","422 registros · 91 jogadores · 16 janelas FIFA"],
              ["Modelo","Gradient Boosting Regressor"],
              ["Target","Média de recência Ancelotti (ajustado por lesão)"],
              ["Otimização","ILP via PuLP — cotas por sub-posição"],
              ["Convocação real","18/05/2026 · Museu do Amanhã · Rio de Janeiro"],
              ["Gerado em",datetime.now().strftime("%d/%m/%Y %H:%M")]]
             if LANG=="pt" else
             [["Manager","Carlo Ancelotti (since June 2025)"],
              ["Period","Dec/2022 – Mar/2026"],
              ["Dataset","422 records · 91 players · 16 FIFA windows"],
              ["Model","Gradient Boosting Regressor"],
              ["Target","Ancelotti recency-weighted mean (injury-adjusted)"],
              ["Optimization","ILP via PuLP — sub-position quotas"],
              ["Real call-up","May 18, 2026 · Museu do Amanhã · Rio de Janeiro"],
              ["Generated",datetime.now().strftime("%Y-%m-%d %H:%M")]])
story.append(tbl(capa_rows,[5*cm,11*cm]))
story += [sp(10)]

skills = ([("Python","Pandas, scikit-learn, XGBoost, PuLP, Matplotlib, ReportLab"),
           ("Machine Learning","Regressão supervisionada, validação cruzada, feature engineering"),
           ("Otimização","Programação Linear Inteira (ILP) com restrições de negócio"),
           ("Engenharia de Dados","Limpeza, deduplicação, imputação, agregação temporal"),
           ("Análise de Domínio","Conhecimento de futebol integrado para corrigir o modelo"),
           ("Comunicação","Relatório auditável com 10 versões documentadas")]
          if LANG=="pt" else
          [("Python","Pandas, scikit-learn, XGBoost, PuLP, Matplotlib, ReportLab"),
           ("Machine Learning","Supervised regression, cross-validation, feature engineering"),
           ("Optimization","Integer Linear Programming with real-world business constraints"),
           ("Data Engineering","Cleaning, deduplication, imputation, temporal aggregation"),
           ("Domain Analysis","Football domain knowledge integrated to correct model behavior"),
           ("Communication","Auditable report with 10 documented iterations")])
sk_title = "Tech Stack & Competências" if LANG=="pt" else "Tech Stack & Skills"
story.append(skill_box(skills, sk_title))
story.append(PageBreak())

# ═══════════════════════════════════════════════════════════════════════════════
# 0. BUSINESS CONTEXT
# ═══════════════════════════════════════════════════════════════════════════════
if LANG=="pt":
    story += [P("0. Contexto e Problema de Negócio","h1"),hr(),
        P("Este projeto demonstra ML aplicado a um problema real de seleção e ranking: "
          "prever quais 91 jogadores elegíveis serão incluídos em um grupo de 26. "
          "O domínio é futebol, mas o problema é generalista — qualquer processo de "
          "seleção com dados históricos segue a mesma lógica."),
        P("<b>Por que este projeto é relevante para data scientists?</b>")]
    buls = ["Dataset longitudinal (múltiplas observações por entidade ao longo do tempo) — requer agregação temporal cuidadosa.",
            "Target não está diretamente no dataset — é construído a partir de heurísticas de domínio.",
            "Regras de negócio rígidas (cotas por posição) precisam ser integradas via otimização combinatória, não só via ML.",
            "Problemas de qualidade de dados reais: chaves duplicadas, NULLs estruturais, variável-alvo com circularidade.",
            "Decisões de modelagem afetam diretamente o output — cada versão documenta o raciocínio."]
else:
    story += [P("0. Business Context & Problem Statement","h1"),hr(),
        P("This project demonstrates ML applied to a real-world selection and ranking problem: "
          "predicting which 91 eligible players will make a 26-man squad. "
          "The domain is football, but the problem is general — any selection process "
          "with historical evaluation data follows the same logic."),
        P("<b>Why is this project relevant for data scientists?</b>")]
    buls = ["Longitudinal dataset (multiple observations per entity over time) — requires careful temporal aggregation.",
            "Target variable is not directly in the dataset — it is constructed from domain heuristics.",
            "Hard business rules (position quotas) must be integrated via combinatorial optimization, not just ML.",
            "Real data quality issues: duplicate keys, structural NULLs, circular target variable.",
            "Modeling decisions directly impact output — each version documents the full reasoning."]
for b in buls: story.append(B(b))
story.append(PageBreak())

# ═══════════════════════════════════════════════════════════════════════════════
# 1. PIPELINE ARCHITECTURE
# ═══════════════════════════════════════════════════════════════════════════════
if LANG=="pt":
    story += [P("1. Arquitetura do Pipeline","h1"),hr(),
        P("Pipeline desenvolvido em 10 versões iterativas, cada uma corrigindo um problema "
          "identificado por análise crítica dos resultados ou validação com especialista de domínio.")]
else:
    story += [P("1. Pipeline Architecture","h1"),hr(),
        P("Pipeline developed across 10 iterative versions, each correcting a problem "
          "identified through critical result analysis or domain expert validation.")]
story.append(img(f"{OUTDIR}/pipeline_diagram.png", width=16*cm))
cap1 = ("Fig. 1 — Arquitetura completa. Overrides de domínio aplicados antes do ILP." if LANG=="pt"
        else "Fig. 1 — Full pipeline architecture. Domain overrides applied before ILP.")
story.append(P(cap1,"cap"))
story.append(img(f"{OUTDIR}/skills_radar.png", width=9*cm))
cap2 = ("Fig. 2 — Competências aplicadas no projeto." if LANG=="pt"
        else "Fig. 2 — Skills applied across this project.")
story.append(P(cap2,"cap"))
story.append(PageBreak())

# ═══════════════════════════════════════════════════════════════════════════════
# 2. DATASET  (sem seção 2.2)
# ═══════════════════════════════════════════════════════════════════════════════
if LANG=="pt":
    story += [P("2. Dataset","h1"),hr(),
        P("422 registros — 1 linha por jogador × janela FIFA. Apenas jogadores "
          "convocados ao menos uma vez aparecem. O modelo infere negativos pela ausência.")]
    dim = [["Dimensão","Valor","Observação"],
           ["Linhas","422","1 removida (Danilo duplicado — erro de exportação)"],
           ["Jogadores únicos","91","Chave: player_id (ex: Bremer1997)"],
           ["Janelas FIFA","16","Mar/23 – Mar/26"],
           ["Técnicos","4","Menezes, Diniz, Dorival Jr., Ancelotti"],
           ["Fontes","2","Sofascore (performance) + Transfermarkt (DOB, market value)"]]
else:
    story += [P("2. Dataset","h1"),hr(),
        P("422 records — 1 row per player × FIFA window. Only players called up "
          "at least once appear. The model infers negatives from absence.")]
    dim = [["Dimension","Value","Note"],
           ["Rows","422","1 removed (duplicate Danilo — export bug)"],
           ["Unique players","91","Key: player_id (e.g. Bremer1997)"],
           ["FIFA windows","16","Mar/23 – Mar/26"],
           ["Managers","4","Menezes, Diniz, Dorival Jr., Ancelotti"],
           ["Sources","2","Sofascore (performance) + Transfermarkt (DOB, market value)"]]
story.append(tbl(dim,[4*cm,2.5*cm,9.5*cm]))
story.append(PageBreak())

# ═══════════════════════════════════════════════════════════════════════════════
# 3. FEATURE ENGINEERING
# ═══════════════════════════════════════════════════════════════════════════════
if LANG=="pt":
    story += [P("3. Feature Engineering","h1"),hr(),
        P("As 422 linhas são agregadas em 91 (1 por jogador). 20 features em 4 grupos:")]
    fe = [["Grupo","Features","Racional"],
          ["G1 — Ancelotti (core)","n_anc, mean_rec, coverage, called_l3, avg_sr, anc_mpw",
           "Decisão direta do técnico que vai à Copa — peso dominante no modelo"],
          ["G2 — Forma pelo Clube","w_avg_sc, w_min_c, avg_gpc, lt_enc, inj",
           "Nível de atividade e performance recente no clube"],
          ["G3 — Histórico NT","tmnt, wmnt, tgnt, asnt, comp_weight",
           "Experiência e desempenho acumulado pela seleção no ciclo"],
          ["G4 — Contexto","has_alt_pos, n_calls_total, rep_rate, age",
           "Versatilidade, histórico geral e idade na Copa"]]
    rw_t = "Pesos de Recência"
    rw_b = ("Cada janela recebe peso proporcional à proximidade da Copa. "
            "Ancelotti: Jun/25=0.60 → Mar/26=1.00 (total=4.00). "
            "Anteriores: Mar/23=0.02 → Mar/25=0.40.")
else:
    story += [P("3. Feature Engineering","h1"),hr(),
        P("422 rows aggregated into 91 (1 per player). 20 features across 4 groups:")]
    fe = [["Group","Features","Rationale"],
          ["G1 — Ancelotti (core)","n_anc, mean_rec, coverage, called_l3, avg_sr, anc_mpw",
           "Direct call-up decision from the World Cup manager — dominant weight"],
          ["G2 — Club Form","w_avg_sc, w_min_c, avg_gpc, lt_enc, inj",
           "Activity level and recent performance at club"],
          ["G3 — NT History","tmnt, wmnt, tgnt, asnt, comp_weight",
           "Accumulated NT experience and performance during the cycle"],
          ["G4 — Context","has_alt_pos, n_calls_total, rep_rate, age",
           "Versatility, overall history and age at World Cup"]]
    rw_t = "Recency Weights"
    rw_b = ("Each window receives a weight proportional to its proximity to the WC. "
            "Ancelotti: Jun/25=0.60 → Mar/26=1.00 (total=4.00). "
            "Earlier: Mar/23=0.02 → Mar/25=0.40.")
story.append(tbl(fe,[3.5*cm,6*cm,6.5*cm]))
story += [sp(8), P(rw_t,"h2"), P(rw_b)]
story.append(PageBreak())

# ═══════════════════════════════════════════════════════════════════════════════
# 4. TARGET VARIABLE
# ═══════════════════════════════════════════════════════════════════════════════
if LANG=="pt":
    story += [P("4. Variável-Alvo","h1"),hr(),
        P("4.1 Evolução em 10 versões","h2")]
    tgt = [["Versão","Target","Problema identificado"],
           ["v1–v2","called_march_2026 (binário)",
            "Circularidade: Gabriel Sara (1 conv.) > Bruno Guimarães (4 conv.)"],
           ["v3","sum(pesos) / 4.00",
            "Penalizava lesionados: Ederson (0.475) abaixo de Hugo Souza (0.750)"],
           ["v7","sum(pesos) / n_conv. para TODOS",
            "Inflava jogadores com 1 conv.: Sara, Bremer, Rayan → prob=1.000"],
           ["v9–v10","÷ n_conv. SÓ para Alisson, Ederson, Bremer; demais ÷ 4.00",
            "Solução cirúrgica — resolve os 3 casos sem afetar os demais"]]
    story += [P("4.2 Fórmula final","h2")]
    story.append(P("Para Alisson, Ederson e Bremer (lesão documentada):", "note"))
    story.append(P("target = sum(ANC_W[w] for w in called_windows) / n_called", "code"))
    story.append(P("Para todos os demais jogadores:", "note"))
    story.append(P("target = sum(ANC_W[w] for w in called_windows) / 4.00", "code"))
    gk_title = "Resultado para goleiros"
    gk_data = [["Goleiro","Janelas Ancelotti","Denominador","Target","Prob."],
               ["Bento","5/5 (todas)","4.00","1.000","0.997"],
               ["Ederson","2/5 (Nov/25+Mar/26)","1.90 (÷n)","0.950","0.946"],
               ["Alisson","3/5 (Jun+Set+Mar)","2.30 (÷n)","0.767","0.764"],
               ["Hugo Souza","4/5 orig. (sem Mar/26 subst.)","4.00","0.750","0.749"]]
else:
    story += [P("4. Target Variable","h1"),hr(),
        P("4.1 Evolution across 10 versions","h2")]
    tgt = [["Version","Target","Problem identified"],
           ["v1–v2","called_march_2026 (binary)",
            "Circular: Gabriel Sara (1 call) > Bruno Guimarães (4 calls)"],
           ["v3","sum(weights) / 4.00",
            "Penalized injured players: Ederson (0.475) below Hugo Souza (0.750)"],
           ["v7","sum(weights) / n_calls for ALL",
            "Inflated single-call players: Sara, Bremer, Rayan → prob=1.000"],
           ["v9–v10","÷ n_calls ONLY for Alisson, Ederson, Bremer; others ÷ 4.00",
            "Surgical fix — resolves 3 cases without affecting anyone else"]]
    story += [P("4.2 Final formula","h2")]
    story.append(P("For Alisson, Ederson and Bremer (documented injuries):", "note"))
    story.append(P("target = sum(ANC_W[w] for w in called_windows) / n_called", "code"))
    story.append(P("For all other players:", "note"))
    story.append(P("target = sum(ANC_W[w] for w in called_windows) / 4.00", "code"))
    gk_title = "Result for goalkeepers"
    gk_data = [["Goalkeeper","Ancelotti windows","Denominator","Target","Prob."],
               ["Bento","5/5 (all)","4.00","1.000","0.997"],
               ["Ederson","2/5 (Nov/25+Mar/26)","1.90 (÷n)","0.950","0.946"],
               ["Alisson","3/5 (Jun+Sep+Mar)","2.30 (÷n)","0.767","0.764"],
               ["Hugo Souza","4/5 orig. (no Mar/26 sub.)","4.00","0.750","0.749"]]

story.append(tbl(tgt,[1.8*cm,4.5*cm,9.7*cm]))
story += [sp(8), P(gk_title,"h2")]
story.append(tbl(gk_data,[3*cm,4.5*cm,3*cm,2*cm,2*cm],
                 ac={2:"CENTER",3:"CENTER",4:"CENTER"}))
story.append(PageBreak())

# ═══════════════════════════════════════════════════════════════════════════════
# 5. MODELS
# ═══════════════════════════════════════════════════════════════════════════════
if LANG=="pt":
    story += [P("5. Modelos de Machine Learning","h1"),hr(),
        P("Problema reformulado como regressão contínua (0–1). 4 modelos com CV 5-fold:")]
    mdl = [["Modelo","Configuração","R²","MAE"],
           ["Ridge Regression","alpha=1.0","0.998","0.011"],
           ["Random Forest","n=200, max_depth=4, min_leaf=3","0.990","0.017"],
           ["Gradient Boosting ★","n=200, depth=3, lr=0.05, sub=0.8","0.999","0.006"],
           ["SVR","RBF kernel, C=1.0, eps=0.05","0.897","0.075"]]
    mn1 = ("<b>Gradient Boosting</b> selecionado: maior R² e menor MAE. "
           "R²≈0.999 reflete alta colinearidade entre target e features Ancelotti — "
           "ML contribui nas margens (ordenação de jogadores com scores similares).")
    mn2 = "Com N=91, regularização aplicada em todos os modelos."
else:
    story += [P("5. Machine Learning Models","h1"),hr(),
        P("Problem reformulated as continuous regression (0–1). 4 models with 5-fold CV:")]
    mdl = [["Model","Configuration","R²","MAE"],
           ["Ridge Regression","alpha=1.0","0.998","0.011"],
           ["Random Forest","n=200, max_depth=4, min_leaf=3","0.990","0.017"],
           ["Gradient Boosting ★","n=200, depth=3, lr=0.05, sub=0.8","0.999","0.006"],
           ["SVR","RBF kernel, C=1.0, eps=0.05","0.897","0.075"]]
    mn1 = ("<b>Gradient Boosting</b> selected: highest R² and lowest MAE. "
           "R²≈0.999 reflects high collinearity between target and Ancelotti features — "
           "ML contributes at the margins (ordering players with similar raw scores).")
    mn2 = "With N=91 samples, regularization applied throughout."

story.append(tbl(mdl,[5.5*cm,6.5*cm,2*cm,2*cm],ac={2:"CENTER",3:"CENTER"}))
story += [sp(6), P(mn1), P(mn2,"note")]
story.append(img(f"{OUTDIR}/ml_01.png", width=14.5*cm))
story.append(P("Fig. 3 — " + ("Comparação de métricas (versão classificação, v2)." if LANG=="pt"
               else "Metric comparison (classification version, v2)."),"cap"))
story.append(img(f"{OUTDIR}/ml_04.png", width=12*cm))
story.append(P("Fig. 4 — " + ("Importância das features. n_anc e coverage dominam." if LANG=="pt"
               else "Feature importance. n_anc and coverage dominate."),"cap"))
story.append(PageBreak())

# ═══════════════════════════════════════════════════════════════════════════════
# 6. ILP
# ═══════════════════════════════════════════════════════════════════════════════
if LANG=="pt":
    story += [P("6. Otimização ILP","h1"),hr(),
        P("Programação Linear Inteira (PuLP + CBC) converte probabilidades em 26 jogadores, "
          "maximizando a soma das probabilidades e respeitando cotas por sub-posição."),
        P("6.1 Por que ILP e não só ranking?","h2"),
        P("Um ranking simples não garante cotas de posição. Sem ILP o modelo poderia "
          "selecionar 5 laterais direitos e 0 goleiros — matematicamente correto mas inutilizável. "
          "O ILP força as restrições de negócio dentro da otimização."),
        P("6.2 Cotas por sub-posição","h2"),
        P("Versões anteriores usavam posição genérica. A separação por lado foi adicionada "
          "após o ILP selecionar 5 laterais direitos e 4 zagueiros esquerdos.")]
    ilp = [["Grupo","Min","Max","Decisão de design"],
           ["Goalkeeper","3","3","Fixo — sempre 3 goleiros em Copa"],
           ["CB_R (Zag. Dir.)","2","2","Separado por lado após erro v5"],
           ["CB_L (Zag. Esq.)","2","2","Separado por lado após erro v5"],
           ["RB (Lat. Dir.)","2","2","Danilo (override 1.0) + 1 mais"],
           ["LB (Lat. Esq.)","2","2","Separado após 5 lat. dir. em v6"],
           ["Midfielder","4","6","Flexível — 2 vagas flutuantes"],
           ["Forward","9","11","Restante — mín. 9 com 6 meias"],
           ["TOTAL","26","26",""]]
    story += [P("6.3 Overrides manuais","h2")]
    ovr = [["Jogador","Override","Motivo"],
           ["Danilo1991","1.00","Confirmado pelo Ancelotti publicamente"],
           ["Neymar1992","0.40","Calculado via análise de notícias (16/05/2026)"],
           ["Rodrygo2001","0.00","Lesão confirmada"],
           ["ÉderMilitão1998","0.00","Lesão confirmada"],
           ["Estêvão2007","0.00","Lesão confirmada (7 conv. Ancelotti)"]]
else:
    story += [P("6. ILP Optimization","h1"),hr(),
        P("Integer Linear Programming (PuLP + CBC) converts probabilities into 26 players, "
          "maximizing the sum of probabilities while respecting sub-position quotas."),
        P("6.1 Why ILP and not just ranking?","h2"),
        P("A simple ranking does not enforce position quotas. Without ILP the model "
          "could select 5 right-backs and 0 goalkeepers — mathematically optimal but unusable. "
          "ILP enforces business constraints within the optimization."),
        P("6.2 Sub-position quotas","h2"),
        P("Earlier versions used generic position. Side-of-field separation was added "
          "after ILP selected 5 right-backs and 4 left centre-backs.")]
    ilp = [["Group","Min","Max","Design decision"],
           ["Goalkeeper","3","3","Fixed — always 3 GKs in a WC squad"],
           ["CB_R (Right CB)","2","2","Side separation after v5 bug"],
           ["CB_L (Left CB)","2","2","Side separation after v5 bug"],
           ["RB (Right back)","2","2","Danilo (override 1.0) + 1 more"],
           ["LB (Left back)","2","2","Separated after 5 right-backs in v6"],
           ["Midfielder","4","6","Flexible — 2 floating spots"],
           ["Forward","9","11","Remainder — min. 9 with 6 midfielders"],
           ["TOTAL","26","26",""]]
    story += [P("6.3 Manual overrides","h2")]
    ovr = [["Player","Override","Reason"],
           ["Danilo1991","1.00","Publicly confirmed by Ancelotti"],
           ["Neymar1992","0.40","Calculated from news analysis (May 16, 2026)"],
           ["Rodrygo2001","0.00","Confirmed injury"],
           ["ÉderMilitão1998","0.00","Confirmed injury"],
           ["Estêvão2007","0.00","Confirmed injury (had 7 Ancelotti calls)"]]

story.append(tbl(ilp,[3*cm,1.2*cm,1.2*cm,10.6*cm],ac={1:"CENTER",2:"CENTER"}))
story += [sp(6)]
story.append(tbl(ovr,[4.5*cm,2*cm,9.5*cm],alt="#FFEBEE"))
story.append(PageBreak())

# ═══════════════════════════════════════════════════════════════════════════════
# 7. NEYMAR
# ═══════════════════════════════════════════════════════════════════════════════
if LANG=="pt":
    story += [P("7. Caso Especial: Neymar","h1"),hr(),
        P("Modelo atribui prob≈0.000 ao Neymar (zero janelas Ancelotti; dados só de 2023-2025). "
          "A probabilidade 0.40 foi calculada por análise qualitativa de notícias."),
        P("Sinais coletados (16/05/2026):","h2")]
    news = [["Fonte","Sinal","Dir."],
            ["Ancelotti (direta)","Melhorou muito, está jogando com continuidade","↑ Forte"],
            ["Ancelotti filho","Se está na lista é porque está melhorando","↑"],
            ["Mauro Beting","Nunca esteve tão próximo da convocação","↑"],
            ["André Rizek","Improvável que Ancelotti leve. Não joga para estar nos 26","↓ Forte"],
            ["Contexto","13 países credenciados — pressão internacional enorme","↑ neutro"],
            ["Contexto","Santos abaixo do esperado na temporada","↓"]]
    story.append(P("5 sinais positivos (incluindo do técnico) × 3 negativos → <b>0.40</b> — "
                   "possível mas não provável. Suficiente para o ILP incluí-lo na 9ª vaga de atacante.","note"))
else:
    story += [P("7. Special Case: Neymar","h1"),hr(),
        P("Model assigns prob≈0.000 to Neymar (zero Ancelotti windows; data only from 2023-2025). "
          "The 0.40 probability was calculated through qualitative news analysis."),
        P("Signals collected (May 16, 2026):","h2")]
    news = [["Source","Signal","Dir."],
            ["Ancelotti (direct)","Improved a lot, playing with continuity","↑ Strong"],
            ["Ancelotti's son","If he's on the list it's because he's improving","↑"],
            ["Mauro Beting","Never been this close to a call-up","↑"],
            ["André Rizek","Unlikely Ancelotti will take him. Not good enough for the 26","↓ Strong"],
            ["Context","13 countries credentialed — huge international pressure","↑ neutral"],
            ["Context","Santos performing below expectations this season","↓"]]
    story.append(P("5 positive signals (including the manager) × 3 negative → <b>0.40</b> — "
                   "possible but not likely. Sufficient for ILP to include him as the 9th forward.","note"))

story.append(tbl(news,[3.5*cm,9.5*cm,2*cm],ac={2:"CENTER"}))
story.append(PageBreak())

# ═══════════════════════════════════════════════════════════════════════════════
# 8. ITERATION HISTORY
# ═══════════════════════════════════════════════════════════════════════════════
if LANG=="pt":
    story += [P("8. Histórico de Iterações","h1"),hr(),
        P("10 versões iterativas. Cada erro encontrado e corrigido demonstra o processo "
          "real de desenvolvimento de um pipeline de ML.")]
    corr = [["Versão","Problema","Correção"],
            ["v1","player_name como chave — dois Danilos confundidos","player_id como chave primária"],
            ["v2","Target binário com circularidade (Sara > Bruno G.)","Target contínuo: weighted Ancelotti presence"],
            ["v3","Posições canônicas incorretas","Posição mais frequente por player_id"],
            ["v4","Hugo Souza inflado; Ederson penalizado por lesão","Feature anc_min_per_win; cobertura por lista original"],
            ["v5","ILP: 4 zagueiros esquerdos (sem distinção de lado)","Classificação CB_R / CB_L com player_ids exatos"],
            ["v6","ILP: 5 laterais direitos (sem distinção de lado)","Classificação RB / LB; cotas ILP por lado"],
            ["v7","mean_rec para TODOS inflava n=1 (prob=1.000)","Penalidade n=1 global — rejeitada por efeitos colaterais"],
            ["v8","Penalidade global excessiva — Rayan/Endrick injustiçados","Ajuste só para Alisson e Ederson (÷ n_conv.)"],
            ["v9","Bremer penalizado por lesão ACL","Bremer adicionado à lista de lesão abonada"],
            ["v10","Neymar com override arbitrário (0.30)","Probabilidade 0.40 calculada por análise de notícias"]]
else:
    story += [P("8. Iteration History","h1"),hr(),
        P("10 iterative versions. Each bug found and fixed demonstrates the "
          "real process of building a production-ready ML pipeline.")]
    corr = [["Version","Problem","Fix"],
            ["v1","player_name as key — two Danilos confused","player_id as primary key"],
            ["v2","Binary target with circularity (Sara > Bruno G.)","Continuous target: weighted Ancelotti presence"],
            ["v3","Incorrect canonical positions","Most frequent position per player_id"],
            ["v4","Hugo Souza inflated; Ederson penalized for injury","anc_min_per_win feature; coverage from original list"],
            ["v5","ILP: 4 left centre-backs (no side distinction)","CB_R / CB_L classification with exact player_ids"],
            ["v6","ILP: 5 right-backs (no side distinction)","RB / LB classification; ILP quotas per side"],
            ["v7","mean_rec for ALL inflated n=1 players (prob=1.000)","Global n=1 penalty — rejected due to side effects"],
            ["v8","Global penalty excessive — Rayan/Endrick unfairly hurt","Adjustment only for Alisson and Ederson (÷ n_calls)"],
            ["v9","Bremer penalized for ACL injury","Bremer added to injury-aboned list"],
            ["v10","Neymar with arbitrary override (0.30)","0.40 calculated from news analysis"]]

story.append(tbl(corr,[1.5*cm,7*cm,7.5*cm]))
story.append(PageBreak())

# ═══════════════════════════════════════════════════════════════════════════════
# 9. FINAL SQUAD
# ═══════════════════════════════════════════════════════════════════════════════
pos_pt = {"Goalkeeper":"Goleiro","CB_R":"Zag. Dir.","CB_L":"Zag. Esq.",
          "RB":"Lat. Dir.","LB":"Lat. Esq.","Midfielder":"Meia","Forward":"Atacante"}
pos_en = {"Goalkeeper":"GK","CB_R":"Right CB","CB_L":"Left CB",
          "RB":"Right back","LB":"Left back","Midfielder":"Midfielder","Forward":"Forward"}
pm = pos_pt if LANG=="pt" else pos_en

if LANG=="pt":
    story += [P("9. Lista Final — 26 Convocados + Próximos","h1"),hr(),
        P("ILP v10 com todas as correções. Convocação real: 18/05/2026.")]
    shdr = ["#","Jogador","Sub-posição","Target","n Anc.","Prob.","Obs."]
    ob = {"inj":"lesão abonada","conf":"confirmado","nws":"notícias 16/05","nxt":"próximo"}
else:
    story += [P("9. Final Squad — 26 Players + Next in Line","h1"),hr(),
        P("ILP v10 with all corrections applied. Real call-up: May 18, 2026.")]
    shdr = ["#","Player","Sub-position","Target","n Anc.","Prob.","Note"]
    ob = {"inj":"injury aboned","conf":"confirmed","nws":"news 16/05","nxt":"next"}

rows_sq = [shdr,
    ["1","Bento",pm["Goalkeeper"],"1.000","5","0.997",""],
    ["2","Ederson",pm["Goalkeeper"],"0.950","2","0.946",ob["inj"]],
    ["3","Alisson",pm["Goalkeeper"],"0.767","3","0.764",ob["inj"]],
    ["↳","Hugo Souza",pm["Goalkeeper"],"0.750","4","0.749",ob["nxt"]],
    ["4","Bremer",pm["CB_R"],"1.000","1","0.993",ob["inj"]],
    ["5","Marquinhos",pm["CB_R"],"0.800","4","0.804",""],
    ["↳","Fabrício Bruno",pm["CB_R"],"0.600","3","0.605",ob["nxt"]],
    ["6","Gabriel Magalhães",pm["CB_L"],"0.850","4","0.851",""],
    ["7","Lucas Beraldo",pm["CB_L"],"0.350","2","0.352",""],
    ["↳","Alexsandro Ribeiro",pm["CB_L"],"0.325","2","0.325",ob["nxt"]],
    ["8","Danilo",pm["RB"],"0.625","3","1.000",ob["conf"]],
    ["9","Wesley",pm["RB"],"1.000","5","0.999",""],
    ["↳","Vanderson",pm["RB"],"0.325","2","0.324",ob["nxt"]],
    ["10","Alex Sandro",pm["LB"],"0.625","3","0.627",""],
    ["11","Douglas Santos",pm["LB"],"0.625","3","0.622",""],
    ["↳","Caio Henrique",pm["LB"],"0.600","3","0.595",ob["nxt"]],
    ["12","Casemiro",pm["Midfielder"],"1.000","5","0.998",""],
    ["13","Andrey Santos",pm["Midfielder"],"0.800","4","0.800",""],
    ["14","Bruno Guimarães",pm["Midfielder"],"0.750","4","0.752",""],
    ["15","Lucas Paquetá",pm["Midfielder"],"0.600","3","0.602",""],
    ["16","Fabinho",pm["Midfielder"],"0.475","2","0.479",""],
    ["17","Joelinton",pm["Midfielder"],"0.375","2","0.368",""],
    ["↳","Danilo (BOT)",pm["Midfielder"],"0.250","1","0.253",ob["nxt"]],
    ["18","Matheus Cunha",pm["Forward"],"1.000","5","0.998",""],
    ["19","Luiz Henrique",pm["Forward"],"0.850","4","0.849",""],
    ["20","Vinícius Júnior",pm["Forward"],"0.825","4","0.823",""],
    ["21","G. Martinelli",pm["Forward"],"0.775","4","0.774",""],
    ["22","Richarlison",pm["Forward"],"0.750","4","0.743",""],
    ["23","João Pedro",pm["Forward"],"0.650","3","0.652",""],
    ["24","Raphinha",pm["Forward"],"0.575","3","0.579",""],
    ["25","Neymar",pm["Forward"],"0.000","0","0.400",ob["nws"]],
    ["26","Endrick",pm["Forward"],"0.250","1","0.254",""],
    ["↳","Igor Thiago",pm["Forward"],"0.250","1","0.254",ob["nxt"]],
]

# Build squad table with Paragraphs (no overlapping)
pc = {pm["Goalkeeper"]:LLGREEN, pm["CB_R"]:LLBLUE, pm["CB_L"]:colors.HexColor("#DDEEFF"),
      pm["RB"]:LLYELL, pm["LB"]:colors.HexColor("#FFF8E1"),
      pm["Midfielder"]:colors.HexColor("#F3E5F5"), pm["Forward"]:colors.HexColor("#FBE9E7")}

wrapped_sq = []
for ri, row in enumerate(rows_sq):
    is_next = (row[0]=="↳")
    wrow = []
    for ci, cell in enumerate(row):
        if ri == 0:
            wrow.append(CH(str(cell)))
        elif is_next:
            wrow.append(C(str(cell), gray=True))
        else:
            wrow.append(C(str(cell)))
    wrapped_sq.append(wrow)

sq_t = Table(wrapped_sq, colWidths=[0.8*cm,4.3*cm,2.5*cm,1.8*cm,1.5*cm,1.5*cm,3.1*cm],
             repeatRows=1)
sq_style = [
    ("BACKGROUND",(0,0),(-1,0),BLUE),
    ("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#CCCCCC")),
    ("VALIGN",(0,0),(-1,-1),"TOP"),
    ("TOPPADDING",(0,0),(-1,-1),4),
    ("BOTTOMPADDING",(0,0),(-1,-1),4),
    ("LEFTPADDING",(0,0),(-1,-1),4),
    ("RIGHTPADDING",(0,0),(-1,-1),4),
    ("ALIGN",(3,0),(5,-1),"CENTER"),
    ("ALIGN",(0,0),(0,-1),"CENTER"),
]
for i, row in enumerate(rows_sq[1:], 1):
    bg = pc.get(row[2], colors.white)
    sq_style.append(("BACKGROUND",(0,i),(-1,i),bg))
sq_t.setStyle(TableStyle(sq_style))
story.append(sq_t)
note_sq = ("↳ = próximo mais provável · n Anc. = convocações originais pelo Ancelotti" if LANG=="pt"
           else "↳ = next most likely · n Anc. = original Ancelotti call-ups")
story.append(P(note_sq,"note"))
story.append(PageBreak())

story.append(img(f"{OUTDIR}/copa2026_v10_ranking.png", width=15*cm))
story.append(P("Fig. 5 — " + ("Probabilidade — 91 jogadores. Verde = selecionado pelo ILP." if LANG=="pt"
               else "Probability — 91 players. Green border = ILP selected."),"cap"))
story.append(img(f"{OUTDIR}/copa2026_form_heatmap.png", width=15*cm))
story.append(P("Fig. 6 — " + ("Heatmap de performance por posição (período Mar/26)." if LANG=="pt"
               else "Performance heatmap by position (Mar/26 period)."),"cap"))
story.append(PageBreak())

# ═══════════════════════════════════════════════════════════════════════════════
# 10. LIMITATIONS + NEXT STEPS
# ═══════════════════════════════════════════════════════════════════════════════
if LANG=="pt":
    story += [P("10. Limitações e Próximos Passos","h1"),hr(),P("10.1 Limitações","h2")]
    lims = [("N=91","Limite inferior para ML supervisionado. Regularização aplicada em todos os modelos."),
            ("Apenas positivos","Dataset sem jogadores nunca convocados. ~1440 linhas com negativos explícitos."),
            ("5 janelas Ancelotti","Preferências táticas específicas do técnico da Copa sub-representadas."),
            ("Neymar sem dados","Sem dados de clube 2025-2026. Override por notícias — não dados brutos."),
            ("Contexto não modelado","Lesões de última hora, dinâmica de vestiário, preferências táticas.")]
    story += [P("10.2 Próximos Passos","h2")]
    steps = [("Validação 18/05","Precision@26 e Recall@26 quando a lista oficial sair."),
             ("Coletar negativos","~1440 linhas com jogadores não convocados por janela."),
             ("market_value_eur","JOIN com data_players_brazil via sofascore_id."),
             ("Dashboard Streamlit","Filtros, squad builder, radar de jogador."),
             ("11 seleções","Argentina, França, Alemanha etc.")] 
else:
    story += [P("10. Limitations & Next Steps","h1"),hr(),P("10.1 Known Limitations","h2")]
    lims = [("N=91","Lower bound for supervised ML. Regularization applied throughout."),
            ("Positives only","No players never called up. ~1440 rows with explicit negatives."),
            ("5 Ancelotti windows","WC manager's specific tactical preferences under-represented."),
            ("No Neymar data","No 2025-2026 club data. Override via news — not raw data."),
            ("Unmodeled context","Last-minute injuries, locker room dynamics, tactical preferences.")]
    story += [P("10.2 Next Steps","h2")]
    steps = [("Validate May 18","Precision@26 and Recall@26 when the real squad is announced."),
             ("Collect negatives","~1440 rows including uncalled players per window."),
             ("market_value_eur","JOIN with data_players_brazil via sofascore_id."),
             ("Streamlit dashboard","Filters, squad builder, player radar."),
             ("11 national teams","Argentina, France, Germany etc.")]

for title, desc in lims: story.append(B(f"<b>{title}:</b> {desc}"))
story += [sp(6)]
for title, desc in steps: story.append(B(f"<b>{title}:</b> {desc}"))

# FOOTER
story += [sp(10), hr(GREEN,2), sp(4)]
footer = (f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')} | "
          "Python · Pandas · scikit-learn · XGBoost · PuLP · ReportLab · Matplotlib · SQLite"
          if LANG=="pt" else
          f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
          "Python · Pandas · scikit-learn · XGBoost · PuLP · ReportLab · Matplotlib · SQLite")
story.append(P(footer,"note"))
story.append(P("Validação real: 18/05/2026 · Museu do Amanhã · Rio de Janeiro" if LANG=="pt"
               else "Real validation: May 18, 2026 · Museu do Amanhã · Rio de Janeiro","note"))

doc.build(story)
print(f"PDF {LANG.upper()} OK.")
