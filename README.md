# SDL survey analysis (Stage-Aware TAM + AUM)

Python pipeline and static dashboard for a Qualtrics survey on **generative AI use across the software development lifecycle** (UCSC software engineering course context).

## Repository layout

| Path | Purpose |
|------|---------|
| `clean_survey_phase1.py` | Phase 1: load export, filter valid responses → `data/cleaned_survey.csv` |
| `build_analysis_dataset.py` | Phase 2: Likert → numeric, constructs → `data/analysis_dataset.csv` |
| `survey_phase3_analysis.py` | Phase 3: descriptive tables, correlations; CSVs → `data/`, figures → `assets/` |
| `stats_reliability.py` | Phase 4: Cronbach's α for three-item AUM scales per stage |
| `stats_inference.py` | Phase 5: Friedman tests + Bonferroni Wilcoxon post-hocs (AU & AUM) |
| `generate_survey_dashboard.py` | Regenerate `index.html` from `data/*.csv` |
| `run_all.sh` | One-command pipeline (Phases 1–6) |
| `index.html` | Static dashboard (Chart.js + embedded stats; open with a local server) |
| `data/` | Pipeline CSVs (cleaned, analysis, Phase 3 summaries; row-level files gitignored) |
| `assets/` | Phase 3 figure PNGs (pipeline writes here by default) |
| `plans/` | Design notes / Cursor plans for each phase |
| `sigcse_paper/` | SIGCSE / Overleaf paper: `main.tex`, `refs.bib`, figure PDFs |

**Aggregates** committed under `data/` (no respondent IDs): `descriptive_statistics.csv`, `stage_level_summary.csv`, `correlation_matrix.csv`, `stage_au_aum_correlations.csv`, `aum_reliability.csv`, `friedman_results.csv`, `wilcoxon_aum_posthoc.csv`, plus figure PNGs under `assets/`.

**Row-level CSVs** (`data/cleaned_survey.csv`, `data/analysis_dataset*.csv`) are **gitignored** by default so a public clone does not publish `ResponseId` or IP fields. Place your own Qualtrics export where the scripts expect it and rerun the pipeline locally.

## Data cleaning rules (Phase 1)

Responses are kept only when **all** of the following hold (matches the SIGCSE paper):

| Rule | Criterion |
|------|-----------|
| Complete | `Finished = True` and `Progress = 100%` |
| Minimum engagement | Duration **> 120 seconds** |
| Not abandoned | Duration **≤ 7200 seconds** (2 hours) |
| Unique | Deduplicated by `ResponseId` |

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate   # optional
pip install -r requirements.txt
chmod +x run_all.sh

# Full pipeline (pass Qualtrics export path, or rely on default in clean_survey_phase1.py)
./run_all.sh /path/to/qualtrics_export.csv

# Or step by step:
python3 clean_survey_phase1.py --input /path/to/qualtrics_export.csv
python3 build_analysis_dataset.py
python3 survey_phase3_analysis.py
python3 stats_reliability.py
python3 stats_inference.py
python3 generate_survey_dashboard.py
python3 -m http.server 8765
# Open http://localhost:8765/index.html
```

## Paper replication targets

After cleaning, compare outputs to the SIGCSE paper (see `sigcse_paper/main.tex`):

- **Cronbach's α** per stage (AUM): `data/aum_reliability.csv` — paper range α ≈ .665–.897
- **Friedman** on AUM across stages: `data/friedman_results.csv` — paper χ²(5) ≈ 66.13, p < .001
- **Wilcoxon post-hocs** (AUM): `data/wilcoxon_aum_posthoc.csv`
- **Overall Pearson AU–AUM**: `data/correlation_matrix.csv` — paper r ≈ 0.690 at N = 85

## Requirements

See `requirements.txt` (pandas, numpy, scipy, matplotlib, seaborn). NumPy 1.26.x is pinned for compatibility with common conda scientific stacks; see `survey_phase3_analysis.py` docstring if you hit `_ARRAY_API` import errors.

## License

Add a `LICENSE` file if you redistribute; research use should follow your IRB / consent terms for the underlying survey data.
