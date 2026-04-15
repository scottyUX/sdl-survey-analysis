---
name: Phase 3 extra publication figures
overview: Extend `survey_phase3_analysis.py` to generate six complementary figures (colored AU vs AUM by stage, dual line AU/AUM across stages, correlation heatmap, AU boxplots by stage, per-stage AU–AUM correlation bars, optional overall histograms), reusing existing `df`, `stage_summary_df`, and `corr_matrix`, saving PNGs at 300 dpi to `--output-dir` and listing them in the completion summary.
todos:
  - id: extend-phase3-plots
    content: Add save_extended_figures() + 6 outputs; call after corr_matrix; update completion print
    status: completed
  - id: verify-phase3-plots
    content: Run survey_phase3_analysis.py and confirm new PNGs on disk
    status: completed
isProject: false
---

# Add complementary Phase 3 figures

## Context

`[survey_phase3_analysis.py](/Users/scottdavis/Survey%20Results/survey_phase3_analysis.py)` already saves `usage_by_stage.png`, `aum_by_stage.png`, and `au_vs_aum.png` in **Step 4**, then builds `**corr_matrix**` in **Step 5**. New outputs that need the correlation matrix (**heatmap**) must run **after** `corr_matrix` is computed (currently after line ~211).

## New artifacts (all under `--output-dir`, dpi 300, `tight_layout`, `plt.close`)


| File                                                       | Source data                                                                                                                          | Notes                                                                                                                                                                                                        |
| ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `au_vs_aum_by_stage.png`                                   | Long-format `AU_*` / `AUM_*` with `stage` column; loop over `[STAGES](/Users/scottdavis/Survey%20Results/survey_phase3_analysis.py)` | `sns.scatterplot(..., hue="stage", alpha=0.7)` + pooled `sns.regplot(..., scatter=False, color="black")` on the long table. Title: e.g. "AI Usage vs AUM by Stage".                                          |
| `au_vs_aum_lines.png`                                      | `[stage_summary_df](/Users/scottdavis/Survey%20Results/survey_phase3_analysis.py)`                                                   | Dual line: `AU_mean` vs `AUM_mean` vs `Stage` (use **stage order** = `STAGES` / row order of `stage_summary_df` as built). Markers, legend, rotated x labels.                                                |
| `correlation_heatmap.png`                                  | `corr_matrix` from Step 5                                                                                                            | `sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap="coolwarm", vmin=-1, vmax=1, square=True)`; shrink annot font if needed (`annot_kws={"size": 8}`).                                                     |
| `au_boxplot_by_stage.png`                                  | Long AU only                                                                                                                         | Stack `AU_{s}` into long DataFrame with `stage`; `sns.boxplot(x="stage", y="AU", order=STAGES)`.                                                                                                             |
| `au_aum_correlation_by_stage.png`                          | Per-stage Pearson `df[f"AU_{s}"].corr(df[f"AUM_{s}"])` in a loop                                                                     | Bar chart (`plt.bar` or `sns.barplot`) of correlation vs stage; handle NaN if any stage all-NaN (unlikely). Optional: save small CSV `stage_au_aum_correlations.csv` with columns `Stage`, `corr` for reuse. |
| `au_aum_overall_distributions.png` (optional but low cost) | `AU_overall`, `AUM_overall`                                                                                                          | One figure, two subplots: `sns.histplot(..., kde=True)` for each; share insight on skew/ceiling.                                                                                                             |


## Code structure (keep `main()` readable)

- Add a helper, e.g. `def save_extended_figures(df, stage_summary_df, corr_matrix, out_dir: Path) -> list[Path]:` that returns paths saved, called **after** `corr_matrix` is built (end of Step 5 or new "Step 4b" / "Figures extended" block).
- Reuse existing constants `[STAGES](/Users/scottdavis/Survey%20Results/survey_phase3_analysis.py)`, `[au_cols](/Users/scottdavis/Survey%20Results/survey_phase3_analysis.py)` pattern (already derivable from `STAGES`).
- Use the same `sns.set_theme(style="whitegrid")` already set in Step 4 (theme persists for the session).

## Completion output

- Extend the final `print("Analysis complete...")` loop to include the new paths (or merge into a single list of all outputs).

## Dependencies

- No new packages; `matplotlib` + `seaborn` + `pandas` only.

## Testing

- Run `python survey_phase3_analysis.py` once; confirm all PNGs exist and no runtime errors.

