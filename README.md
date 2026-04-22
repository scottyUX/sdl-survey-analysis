# SDL survey analysis (Stage-Aware TAM + AUM)

Python pipeline and static dashboard for a Qualtrics survey on **generative AI use across the software development lifecycle** (UCSC software engineering course context).

## Repository layout

| Path | Purpose |
|------|---------|
| `clean_survey_phase1.py` | Phase 1: load export, filter valid responses → `data/cleaned_survey.csv` |
| `build_analysis_dataset.py` | Phase 2: Likert → numeric, constructs → `data/analysis_dataset.csv` |
| `survey_phase3_analysis.py` | Phase 3: descriptive tables, correlations; CSVs → `data/`, figures → `assets/` |
| `generate_survey_dashboard.py` | Regenerate `index.html` from `data/*.csv` |
| `index.html` | Static dashboard (Chart.js + embedded stats; open with a local server) |
| `data/` | Pipeline CSVs (cleaned, analysis, Phase 3 summaries; row-level files gitignored) |
| `assets/` | Phase 3 figure PNGs (pipeline writes here by default) |
| `plans/` | Design notes / Cursor plans for each phase |
| `sigcse_paper/` | SIGCSE / Overleaf paper: `main.tex`, `refs.bib`, figure PDFs |

**Aggregates** committed under `data/` (no respondent IDs): `descriptive_statistics.csv`, `stage_level_summary.csv`, `correlation_matrix.csv`, `stage_au_aum_correlations.csv`, plus figure PNGs under `assets/`.

**Row-level CSVs** (`data/cleaned_survey.csv`, `data/analysis_dataset*.csv`) are **gitignored** by default so a public clone does not publish `ResponseId` or IP fields. Place your own Qualtrics export where the scripts expect it and rerun the pipeline locally.

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate   # optional
pip install -r requirements.txt

# Phase 1 — set input path inside clean_survey_phase1.py or use --input
python3 clean_survey_phase1.py

# Phase 2
python3 build_analysis_dataset.py

# Phase 3
python3 survey_phase3_analysis.py

# Dashboard HTML
python3 generate_survey_dashboard.py
python3 -m http.server 8765
# Open http://localhost:8765/index.html
```

## Requirements

See `requirements.txt` (pandas, numpy, matplotlib, seaborn). NumPy 1.26.x is pinned for compatibility with common conda scientific stacks; see `survey_phase3_analysis.py` docstring if you hit `_ARRAY_API` import errors.

## License

Add a `LICENSE` file if you redistribute; research use should follow your IRB / consent terms for the underlying survey data.
