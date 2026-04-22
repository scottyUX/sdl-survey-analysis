# SIGCSE Virtual 2026 — Overleaf Upload Package

## Contents
- `main.tex` — paper source (anonymized, ACM sigconf, 2-column)
- `refs.bib` — BibTeX references (13 entries)
- `fig1_au_aum_lines.pdf` — AU and AUM across SDLC stages
- `fig2_corr_by_stage.pdf` — AU–AUM correlation by stage (with significance)
- `fig3_scatter.pdf` — Overall AU vs AUM scatter
- `fig4_heatmap.pdf` — Correlation matrix

## How to upload to Overleaf

1. Go to https://www.overleaf.com and click **"New Project" → "Upload Project"**
2. Zip all 6 files above, or upload individually via the file menu
3. In Overleaf, set the main document to `main.tex`
4. Set the compiler to **pdfLaTeX** (Menu → Settings → Compiler)
5. Click **Recompile** — it should build cleanly

Alternatively, use the ACM SIGCONF template on Overleaf
(https://www.overleaf.com/latex/templates/association-for-computing-machinery-acm-sig-proceedings-template/bmvfhcdnxfty)
and replace `main.tex` with the provided source.

## Before submission to SIGCSE

1. **De-anonymize** only for the final (camera-ready) version — keep
   `anonymous` class option for the blind submission. The file already
   has author block placeholders (`Author 1`, etc.) as recommended by
   the SIGCSE instructions.

2. **Check page count**: 6 body pages max (references may spill to page 7
   as a references-only page). Appendices are NOT permitted on the
   references page per SIGCSE rules.

3. **ORCiD IDs**: Each author must have an ORCiD ID entered in EasyChair
   at submission time.

4. **AI disclosure** is already in the Acknowledgements block — review
   and edit to match your actual tool usage.

5. **Abstract ≤ 250 words** — current abstract is within limit. Ensure
   the same text is pasted into EasyChair.

## Key dates (AoE, UTC-12h)
- **Fri 1 May 2026** — abstract due
- **Fri 8 May 2026** — full paper submission
- **Mon 22 Jun 2026** — decisions
