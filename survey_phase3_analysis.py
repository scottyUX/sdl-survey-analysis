#!/usr/bin/env python3
"""
Phase 3: Descriptive statistics, stage-level AU/AUM summaries, figures,
correlation matrix, and basic insights from analysis_dataset.csv.

Outputs CSVs to ``data/`` by default; PNG figures go under ``assets/`` (configurable).

Environment note: If you see AttributeError: _ARRAY_API not found or
numpy.core.multiarray failed to import, you have NumPy 2.x with packages
built for NumPy 1.x. Fix: pip install "numpy>=1.26,<2" --force-reinstall
(and upgrade matplotlib: pip install "matplotlib>=3.9").
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "data"
DEFAULT_INPUT = DATA_DIR / "analysis_dataset.csv"
DEFAULT_OUTPUT_DIR = DATA_DIR
DEFAULT_ASSETS_DIR = SCRIPT_DIR / "assets"

STAGES: list[str] = [
    "plan",
    "design",
    "implementation",
    "testing",
    "deployment",
    "maintenance",
]


def stage_column_lists() -> tuple[list[str], list[str], list[str], list[str], list[str]]:
    """Build PEOU, PU, AU, AUM column names via loops; BI is only BI_plan in this instrument."""
    peou = [f"PEOU_{s}" for s in STAGES]
    pu = [f"PU_{s}" for s in STAGES]
    au = [f"AU_{s}" for s in STAGES]
    aum = [f"AUM_{s}" for s in STAGES]
    bi = ["BI_plan"]
    return peou, pu, bi, au, aum


def save_extended_figures(
    df: pd.DataFrame,
    stage_summary_df: pd.DataFrame,
    corr_matrix: pd.DataFrame,
    assets_dir: Path,
    data_dir: Path,
) -> list[Path]:
    """
    Publication-style figures: AU vs AUM by stage, dual line plot, heatmap,
    AU boxplots, per-stage AU–AUM correlation bars, overall distributions.
    """
    saved: list[Path] = []

    # --- Long format: one row per respondent per stage (AU & AUM) ---
    long_rows: list[pd.DataFrame] = []
    long_au_rows: list[pd.DataFrame] = []
    for s in STAGES:
        block = df[[f"AU_{s}", f"AUM_{s}"]].copy()
        block.columns = ["AU", "AUM"]
        block["stage"] = s
        long_rows.append(block)
        au_only = df[[f"AU_{s}"]].copy()
        au_only.columns = ["AU"]
        au_only["stage"] = s
        long_au_rows.append(au_only)
    long_df = pd.concat(long_rows, ignore_index=True)
    long_au_df = pd.concat(long_au_rows, ignore_index=True)

    # 1. AU vs AUM by stage (colored scatter + pooled regression line)
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.scatterplot(
        data=long_df, x="AU", y="AUM", hue="stage", alpha=0.7, ax=ax
    )
    sns.regplot(
        data=long_df,
        x="AU",
        y="AUM",
        scatter=False,
        color="black",
        ax=ax,
    )
    ax.set_title("AI Usage vs AUM by Stage")
    ax.set_xlabel("AU")
    ax.set_ylabel("AUM")
    fig.tight_layout()
    p = assets_dir / "au_vs_aum_by_stage.png"
    fig.savefig(p, dpi=300)
    plt.close(fig)
    saved.append(p)

    # 2. Dual-line: mean AU vs mean AUM across stages
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(
        stage_summary_df["Stage"],
        stage_summary_df["AU_mean"],
        marker="o",
        label="AU",
    )
    ax.plot(
        stage_summary_df["Stage"],
        stage_summary_df["AUM_mean"],
        marker="o",
        label="AUM",
    )
    ax.set_title("AI Usage vs AUM Across SDLC Stages")
    ax.set_xlabel("Stage")
    ax.set_ylabel("Mean value")
    ax.legend()
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    fig.tight_layout()
    p = assets_dir / "au_vs_aum_lines.png"
    fig.savefig(p, dpi=300)
    plt.close(fig)
    saved.append(p)

    # 3. Correlation heatmap (planning / TAM validation)
    fig, ax = plt.subplots(figsize=(9, 7))
    sns.heatmap(
        corr_matrix,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        vmin=-1,
        vmax=1,
        square=True,
        ax=ax,
        annot_kws={"size": 8},
    )
    ax.set_title("Correlation Matrix")
    fig.tight_layout()
    p = assets_dir / "correlation_heatmap.png"
    fig.savefig(p, dpi=300)
    plt.close(fig)
    saved.append(p)

    # 4. Boxplot: AU distribution by stage
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.boxplot(
        data=long_au_df,
        x="stage",
        y="AU",
        order=STAGES,
        ax=ax,
    )
    ax.set_title("Distribution of AI Usage by Stage")
    ax.set_xlabel("Stage")
    ax.set_ylabel("AU")
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    fig.tight_layout()
    p = assets_dir / "au_boxplot_by_stage.png"
    fig.savefig(p, dpi=300)
    plt.close(fig)
    saved.append(p)

    # 5. Per-stage Pearson AU–AUM correlation + CSV
    stage_corrs: list[float] = []
    for s in STAGES:
        r = df[f"AU_{s}"].corr(df[f"AUM_{s}"])
        stage_corrs.append(float(r) if pd.notna(r) else float("nan"))
    stage_corr_df = pd.DataFrame({"Stage": STAGES, "corr": stage_corrs})
    csv_p = data_dir / "stage_au_aum_correlations.csv"
    stage_corr_df.to_csv(csv_p, index=False)
    saved.append(csv_p)

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(data=stage_corr_df, x="Stage", y="corr", order=STAGES, ax=ax)
    ax.set_title("AU–AUM Correlation by Stage")
    ax.set_xlabel("Stage")
    ax.set_ylabel("Pearson r")
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    fig.tight_layout()
    p = assets_dir / "au_aum_correlation_by_stage.png"
    fig.savefig(p, dpi=300)
    plt.close(fig)
    saved.append(p)

    # 6. Overall AU / AUM distributions (skew, ceiling effects)
    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(10, 4))
    sns.histplot(df["AU_overall"], kde=True, ax=ax_a)
    ax_a.set_title("AU_overall")
    ax_a.set_xlabel("AU_overall")
    sns.histplot(df["AUM_overall"], kde=True, ax=ax_b)
    ax_b.set_title("AUM_overall")
    ax_b.set_xlabel("AUM_overall")
    fig.suptitle("Overall AI Usage and AUM Distributions")
    fig.tight_layout()
    p = assets_dir / "au_aum_overall_distributions.png"
    fig.savefig(p, dpi=300)
    plt.close(fig)
    saved.append(p)

    return saved


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Phase 3 descriptive analysis for stage-aware TAM / AUM."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Path to analysis_dataset.csv (default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory for CSV outputs (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--assets-dir",
        type=Path,
        default=DEFAULT_ASSETS_DIR,
        help=f"Directory for PNG figures (default: {DEFAULT_ASSETS_DIR})",
    )
    args = parser.parse_args()
    inp = args.input.expanduser()
    data_dir = args.output_dir.expanduser()
    assets_dir = args.assets_dir.expanduser()
    data_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    if not inp.is_file():
        print(f"Error: input not found: {inp}", file=sys.stderr)
        return 1

    # -------------------------------------------------------------------------
    # Step 1: Load data
    # -------------------------------------------------------------------------
    df = pd.read_csv(inp, low_memory=False)
    print("=== Step 1: Load data ===")
    print(f"Dataset shape: {df.shape}")
    print("\nColumns:")
    print(df.columns.tolist())

    peou_cols, pu_cols, bi_cols, au_cols, aum_cols = stage_column_lists()

    # -------------------------------------------------------------------------
    # Step 6: Derived variables (needed for desc, plots, correlation)
    # -------------------------------------------------------------------------
    df["AU_overall"] = df[au_cols].mean(axis=1, skipna=True)
    df["AUM_overall"] = df[aum_cols].mean(axis=1, skipna=True)

    # -------------------------------------------------------------------------
    # Step 2: Descriptive statistics
    # -------------------------------------------------------------------------
    desc_cols = (
        peou_cols
        + pu_cols
        + bi_cols
        + au_cols
        + aum_cols
        + ["AI_Literacy", "Facilitating_Conditions", "AU_overall", "AUM_overall"]
    )
    missing = [c for c in desc_cols if c not in df.columns]
    if missing:
        print(f"Error: missing columns: {missing}", file=sys.stderr)
        return 1

    summary_table = pd.DataFrame(
        {
            "Variable": desc_cols,
            "Mean": [df[c].mean(skipna=True) for c in desc_cols],
            "SD": [df[c].std(skipna=True) for c in desc_cols],
            "N": [df[c].count() for c in desc_cols],
        }
    ).round(3)

    print("\n=== Step 2: Descriptive statistics ===")
    print(summary_table.to_string(index=False))

    desc_path = data_dir / "descriptive_statistics.csv"
    summary_table.to_csv(desc_path, index=False)

    # -------------------------------------------------------------------------
    # Step 3: Stage-level analysis (RQ2)
    # -------------------------------------------------------------------------
    stage_rows: list[dict] = []
    for stage in STAGES:
        au_col = f"AU_{stage}"
        aum_col = f"AUM_{stage}"
        stage_rows.append(
            {
                "Stage": stage,
                "AU_mean": df[au_col].mean(skipna=True),
                "AU_sd": df[au_col].std(skipna=True),
                "AUM_mean": df[aum_col].mean(skipna=True),
                "AUM_sd": df[aum_col].std(skipna=True),
                "N_AU": df[au_col].count(),
                "N_AUM": df[aum_col].count(),
            }
        )
    stage_summary_df = pd.DataFrame(stage_rows).round(3)

    print("\n=== Step 3: Stage-level summary ===")
    print(stage_summary_df.to_string(index=False))

    stage_path = data_dir / "stage_level_summary.csv"
    stage_summary_df.to_csv(stage_path, index=False)

    # -------------------------------------------------------------------------
    # Step 4: Visualization
    # -------------------------------------------------------------------------
    sns.set_theme(style="whitegrid")

    fig1, ax1 = plt.subplots(figsize=(8, 5))
    sns.barplot(data=stage_summary_df, x="Stage", y="AU_mean", ax=ax1)
    ax1.set_title("AI Usage Across SDLC Stages")
    ax1.set_xlabel("SDLC Stage")
    ax1.set_ylabel("Mean AU")
    plt.setp(ax1.get_xticklabels(), rotation=30, ha="right")
    fig1.tight_layout()
    p1 = assets_dir / "usage_by_stage.png"
    fig1.savefig(p1, dpi=300)
    plt.close(fig1)

    fig2, ax2 = plt.subplots(figsize=(8, 5))
    sns.barplot(data=stage_summary_df, x="Stage", y="AUM_mean", ax=ax2)
    ax2.set_title("AI Usage Maturity Across SDLC Stages")
    ax2.set_xlabel("SDLC Stage")
    ax2.set_ylabel("Mean AUM")
    plt.setp(ax2.get_xticklabels(), rotation=30, ha="right")
    fig2.tight_layout()
    p2 = assets_dir / "aum_by_stage.png"
    fig2.savefig(p2, dpi=300)
    plt.close(fig2)

    fig3, ax3 = plt.subplots(figsize=(8, 6))
    sns.regplot(
        data=df,
        x="AU_overall",
        y="AUM_overall",
        ax=ax3,
        scatter_kws={"alpha": 0.7},
    )
    ax3.set_title("AI Usage vs AI Usage Maturity")
    ax3.set_xlabel("Overall AU")
    ax3.set_ylabel("Overall AUM")
    fig3.tight_layout()
    p3 = assets_dir / "au_vs_aum.png"
    fig3.savefig(p3, dpi=300)
    plt.close(fig3)

    # -------------------------------------------------------------------------
    # Step 5: TAM relationships (correlation matrix)
    # -------------------------------------------------------------------------
    corr_cols = [
        "PEOU_plan",
        "PU_plan",
        "BI_plan",
        "AU_plan",
        "AI_Literacy",
        "Facilitating_Conditions",
        "AU_overall",
        "AUM_overall",
    ]
    corr_missing = [c for c in corr_cols if c not in df.columns]
    if corr_missing:
        print(f"Error: missing columns for correlation: {corr_missing}", file=sys.stderr)
        return 1

    corr_matrix = df[corr_cols].corr().round(3)
    print("\n=== Step 5: Correlation matrix ===")
    print(corr_matrix.to_string())

    corr_path = data_dir / "correlation_matrix.csv"
    corr_matrix.to_csv(corr_path)

    # -------------------------------------------------------------------------
    # Extended figures (after correlation matrix for heatmap)
    # -------------------------------------------------------------------------
    extended_paths = save_extended_figures(
        df, stage_summary_df, corr_matrix, assets_dir, data_dir
    )
    print("\n=== Extended figures ===")
    for ep in extended_paths:
        print(f"  Saved: {ep}")

    # -------------------------------------------------------------------------
    # Step 7: Basic insights
    # -------------------------------------------------------------------------
    au_rank = stage_summary_df.sort_values("AU_mean", ascending=False)[
        ["Stage", "AU_mean"]
    ]
    aum_rank = stage_summary_df.sort_values("AUM_mean", ascending=False)[
        ["Stage", "AUM_mean"]
    ]

    highest_au_stage = au_rank.iloc[0]["Stage"]
    lowest_au_stage = au_rank.iloc[-1]["Stage"]
    highest_aum_stage = aum_rank.iloc[0]["Stage"]
    lowest_aum_stage = aum_rank.iloc[-1]["Stage"]
    au_aum_corr = df["AU_overall"].corr(df["AUM_overall"])

    print("\n=== Step 7: Basic insights ===")
    print(f"Highest AI usage stage: {highest_au_stage}")
    print(f"Lowest AI usage stage: {lowest_au_stage}")
    print(f"Highest AUM stage: {highest_aum_stage}")
    print(f"Lowest AUM stage: {lowest_aum_stage}")
    print(
        f"Correlation between AU_overall and AUM_overall: {au_aum_corr:.3f}"
    )

    print("\nAU stage ranking:")
    print(au_rank.to_string(index=False))
    print("\nAUM stage ranking:")
    print(aum_rank.to_string(index=False))

    enriched_path = data_dir / "analysis_dataset_enriched.csv"
    df.to_csv(enriched_path, index=False)

    print("\nAnalysis complete. Outputs saved:")
    all_outputs: list[Path] = [
        desc_path,
        stage_path,
        p1,
        p2,
        p3,
        corr_path,
        *extended_paths,
        enriched_path,
    ]
    for p in all_outputs:
        print(f"  {p}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
