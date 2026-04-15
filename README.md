# SDL survey analysis (Stage-Aware TAM + AUM)

Python pipeline and static dashboard for a Qualtrics survey on **generative AI use across the software development lifecycle** (UCSC software engineering course context).

## Repository layout

| Path | Purpose |
|------|---------|
| `clean_survey_phase1.py` | Phase 1: load export, filter valid responses, `cleaned_survey.csv` |
| `build_analysis_dataset.py` | Phase 2: Likert → numeric, per-stage PEOU/PU/BI/AU, AUM, literacy → `analysis_dataset.csv` |
| `survey_phase3_analysis.py` | Phase 3: descriptive tables, correlations, figures (PNG + CSV summaries) |
| `generate_survey_dashboard.py` | Regenerate `index.html` from the CSV outputs |
| `index.html` | Static dashboard (Chart.js + embedded stats; open with a local server) |
| `plans/` | Design notes / Cursor plans for each phase |

**Aggregates** committed here (no respondent IDs): `descriptive_statistics.csv`, `stage_level_summary.csv`, `correlation_matrix.csv`, `stage_au_aum_correlations.csv`, and figure PNGs.

**Row-level CSVs** (`cleaned_survey.csv`, `analysis_dataset*.csv`) are **gitignored** by default so a public clone does not publish `ResponseId` or IP fields. Place your own Qualtrics export where the scripts expect it and rerun the pipeline locally.

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
