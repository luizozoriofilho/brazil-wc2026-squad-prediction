# Copa do Mundo FIFA 2026 — Previsão de Convocação da Seleção Brasileira

Pipeline completo de Machine Learning para prever os 26 convocados do Brasil para a Copa do Mundo 2026.

## Sobre o Projeto

- **Dataset:** 422 registros · 91 jogadores únicos · 16 janelas FIFA (dez/2022 – mar/2026)
- **Técnico previsto:** Carlo Ancelotti (assumiu jun/2025)
- **Modelo:** Gradient Boosting Regressor (R²=0.999, MAE=0.006)
- **Otimização:** ILP via PuLP com cotas por sub-posição (lado do campo)
- **Validação real:** Convocação divulgada em 18/05/2026

## Estrutura dos Arquivos

```
01_pipeline_copa2026.py   → Pipeline principal: dados, features, modelo, ILP
02_eda_plots.py           → Gráficos exploratórios (EDA)
03_form_analysis.py       → Análise de forma recente por posição
04_auxiliary_plots.py     → Diagrama do pipeline e radar de competências
05_relatorio_pdf.py       → Gerador do relatório técnico em PDF (PT e EN)
```

## Ordem de Execução

```bash
pip install pandas numpy scikit-learn xgboost pulp matplotlib seaborn reportlab pillow

python 01_pipeline_copa2026.py    # gera outputs/copa2026_predictions.csv
python 02_eda_plots.py            # gera gráficos EDA
python 03_form_analysis.py        # gera heatmap de forma por posição
python 04_auxiliary_plots.py      # gera diagrama do pipeline
python 05_relatorio_pdf.py pt     # gera relatório em português
python 05_relatorio_pdf.py en     # gera relatório em inglês
```

## Inovações Técnicas

| # | Problema | Solução |
|---|----------|---------|
| v1 | `player_name` como chave — dois Danilos confundidos | `player_id` como chave primária |
| v2 | Target binário com circularidade | Target contínuo: média ponderada de recência |
| v3 | Posições canônicas incorretas | Posição mais frequente por `player_id` |
| v4 | Hugo Souza inflado; Ederson penalizado por lesão | Feature `anc_min_per_win`; cobertura por lista original |
| v5 | ILP selecionou 4 zagueiros esquerdos | Classificação `CB_R` / `CB_L` com player_ids exatos |
| v6 | ILP selecionou 5 laterais direitos | Classificação `RB` / `LB`; cotas ILP por lado |
| v7–v8 | Penalidade n=1 inflava/deflavia jogadores | Ajuste seletivo apenas para Alisson e Ederson |
| v9 | Bremer penalizado por lesão ACL | Denominador ajustado (÷ n_chamado) |
| v10 | Override arbitrário para Neymar | Probabilidade 0.40 via análise de notícias |

## Target Variable

Para **Alisson, Ederson e Bremer** (ausências por lesão comprovada):
```
target = sum(ANC_W[w] for w in called_windows) / n_called_windows
```

Para **todos os demais**:
```
target = sum(ANC_W[w] for w in called_windows) / 4.00
```

## Lista Prevista (26 jogadores)

| Sub-posição | Jogadores |
|-------------|-----------|
| Goleiro | Bento · Ederson · Alisson |
| Zag. Direito | Bremer · Marquinhos |
| Zag. Esquerdo | Gabriel Magalhães · Lucas Beraldo |
| Lat. Direito | Danilo · Wesley |
| Lat. Esquerdo | Alex Sandro · Douglas Santos |
| Meia | Casemiro · Andrey Santos · Bruno Guimarães · Paquetá · Fabinho · Joelinton |
| Atacante | Matheus Cunha · Luiz Henrique · Vinícius Jr. · Martinelli · Richarlison · João Pedro · Raphinha · Neymar · Endrick |

## Tech Stack

`Python` · `Pandas` · `scikit-learn` · `XGBoost` · `PuLP` · `Matplotlib` · `Seaborn` · `ReportLab` · `SQLite`

---
*Projeto de portfólio — Data Analytics & Machine Learning*
