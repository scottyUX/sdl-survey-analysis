#!/usr/bin/env python3
"""
Inferential tests for stage-wise AU and AUM (paper Section 4.4 / 5.2).

- Friedman test: within-subject differences across SDLC stages (complete-case)
- Wilcoxon signed-rank post-hocs with Bonferroni correction (AUM only)

Loads analysis_dataset.csv and writes:
  data/friedman_results.csv
  data/wilcoxon_aum_posthoc.csv

Usage:
  python3 stats_inference.py
  python3 stats_inference.py --input ./data/analysis_dataset.csv
"""

from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path

import pandas as pd
from scipy import stats

from survey_constants import STAGES

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "data"
DEFAULT_INPUT = DATA_DIR / "analysis_dataset.csv"

STAGE_LABELS = {
    "plan": "Planning",
    "design": "Design",
    "implementation": "Implementation",
    "testing": "Testing",
    "deployment": "Deployment",
    "maintenance": "Maintenance",
}


def complete_case_frame(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    return df[cols].dropna(how="any")


def friedman_test(df: pd.DataFrame, cols: list[str]) -> dict:
    cc = complete_case_frame(df, cols)
    arrays = [cc[c].to_numpy(dtype=float) for c in cols]
    if len(cc) < 2:
        return {
            "N": len(cc),
            "chi2": float("nan"),
            "df": len(cols) - 1,
            "p_value": float("nan"),
        }
    chi2, p = stats.friedmanchisquare(*arrays)
    return {
        "N": len(cc),
        "chi2": float(chi2),
        "df": len(cols) - 1,
        "p_value": float(p),
    }


def significance_label(p_bonf: float) -> str:
    if pd.isna(p_bonf):
        return "n.s."
    if p_bonf < 0.01:
        return "**"
    if p_bonf < 0.05:
        return "*"
    return "n.s."


def wilcoxon_posthoc_aum(df: pd.DataFrame, aum_cols: list[str]) -> pd.DataFrame:
    cc = complete_case_frame(df, aum_cols)
    pairs = list(itertools.combinations(aum_cols, 2))
    n_comparisons = len(pairs)
    alpha = 0.05 / n_comparisons

    rows: list[dict] = []
    for a, b in pairs:
        stage_a = a.removeprefix("AUM_")
        stage_b = b.removeprefix("AUM_")
        x = cc[a].to_numpy(dtype=float)
        y = cc[b].to_numpy(dtype=float)
        if len(cc) < 1:
            stat, p_raw = float("nan"), float("nan")
        else:
            try:
                res = stats.wilcoxon(x, y, zero_method="wilcox")
                stat, p_raw = float(res.statistic), float(res.pvalue)
            except ValueError:
                stat, p_raw = float("nan"), float("nan")

        p_bonf = min(p_raw * n_comparisons, 1.0) if pd.notna(p_raw) else float("nan")
        rows.append(
            {
                "Stage_A": STAGE_LABELS.get(stage_a, stage_a),
                "Stage_B": STAGE_LABELS.get(stage_b, stage_b),
                "N": len(cc),
                "statistic": stat,
                "p_raw": p_raw,
                "p_bonferroni": p_bonf,
                "significant": significance_label(p_bonf),
            }
        )

    out = pd.DataFrame(rows)
    return out.round({"statistic": 4, "p_raw": 4, "p_bonferroni": 4})


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Friedman and Wilcoxon inferential tests for AU/AUM by stage."
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
        default=DATA_DIR,
        help=f"Directory for CSV outputs (default: {DATA_DIR})",
    )
    args = parser.parse_args()
    inp = args.input.expanduser()
    out_dir = args.output_dir.expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    if not inp.is_file():
        print(f"Error: input not found: {inp}", file=sys.stderr)
        return 1

    df = pd.read_csv(inp, low_memory=False)
    au_cols = [f"AU_{s}" for s in STAGES]
    aum_cols = [f"AUM_{s}" for s in STAGES]

    missing = [c for c in au_cols + aum_cols if c not in df.columns]
    if missing:
        print(f"Error: missing columns: {missing}", file=sys.stderr)
        return 1

    print("=== Friedman tests (complete-case subsample) ===")
    friedman_rows = []
    for construct, cols in [("AUM", aum_cols), ("AU", au_cols)]:
        result = friedman_test(df, cols)
        friedman_rows.append({"Construct": construct, **result})
        print(
            f"{construct}: N={result['N']}, "
            f"chi2({result['df']})={result['chi2']:.4f}, p={result['p_value']:.6f}"
        )

    friedman_df = pd.DataFrame(friedman_rows).round(
        {"chi2": 4, "p_value": 6}
    )
    friedman_path = out_dir / "friedman_results.csv"
    friedman_df.to_csv(friedman_path, index=False)

    print("\n=== Wilcoxon signed-rank post-hoc (AUM, Bonferroni) ===")
    wilcoxon_df = wilcoxon_posthoc_aum(df, aum_cols)
    print(wilcoxon_df.to_string(index=False))

    wilcoxon_path = out_dir / "wilcoxon_aum_posthoc.csv"
    wilcoxon_df.to_csv(wilcoxon_path, index=False)

    print(f"\nSaved: {friedman_path}")
    print(f"Saved: {wilcoxon_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
