#!/usr/bin/env python3
"""
Cronbach's alpha for the three-item AUM scale at each SDLC stage.

Loads cleaned_survey.csv, converts Likert items to 1–5, and writes
data/aum_reliability.csv (paper Section 5.1).

Usage:
  python3 stats_reliability.py
  python3 stats_reliability.py --input ./data/cleaned_survey.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from build_analysis_dataset import apply_likert_to_dataframe
from survey_constants import STAGE_PREFIX, STAGES

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "data"
DEFAULT_INPUT = DATA_DIR / "cleaned_survey.csv"
DEFAULT_OUTPUT = DATA_DIR / "aum_reliability.csv"


def aum_item_columns(prefix: str) -> list[str]:
    return [f"{prefix}_AUM_{i}" for i in (1, 2, 3)]


def cronbach_alpha(items: pd.DataFrame) -> tuple[float, int]:
    """
    Cronbach's alpha for k Likert items (rows = respondents).
    Returns (alpha, n_valid); alpha is NaN when undefined.
    """
    df = items.dropna(how="any")
    n, k = df.shape
    if k < 2 or n < 2:
        return float("nan"), n

    item_vars = df.var(axis=0, ddof=1)
    total_var = df.sum(axis=1).var(ddof=1)
    if total_var == 0 or np.isnan(total_var):
        return float("nan"), n

    alpha = (k / (k - 1)) * (1 - item_vars.sum() / total_var)
    return float(alpha), n


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compute Cronbach's alpha for AUM items per SDLC stage."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Path to cleaned_survey.csv (default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output CSV path (default: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()
    inp = args.input.expanduser()
    out = args.output.expanduser()

    if not inp.is_file():
        print(f"Error: input not found: {inp}", file=sys.stderr)
        return 1

    print("=== AUM reliability (Cronbach's alpha) ===")
    df = pd.read_csv(inp, low_memory=False)
    df_num = apply_likert_to_dataframe(df)

    rows: list[dict] = []
    for stage_key, prefix in STAGE_PREFIX.items():
        cols = aum_item_columns(prefix)
        missing = [c for c in cols if c not in df_num.columns]
        if missing:
            print(f"Warning: missing columns for {stage_key}: {missing}", file=sys.stderr)
            continue

        alpha, n = cronbach_alpha(df_num[cols])
        rows.append(
            {
                "Stage": stage_key,
                "Prefix": prefix,
                "Items": 3,
                "N": n,
                "Cronbach_alpha": round(alpha, 3) if pd.notna(alpha) else np.nan,
            }
        )

    result = pd.DataFrame(rows)
    print(result.to_string(index=False))

    out.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(out, index=False)
    print(f"\nSaved: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
