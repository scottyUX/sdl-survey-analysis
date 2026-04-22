#!/usr/bin/env python3
"""
Phase 2: Construct-level variables for stage-aware TAM and AUM.

Loads cleaned_survey.csv, converts Likert items to 1–5, aggregates per-stage
constructs, and writes analysis_dataset.csv with validation statistics.

Requires: pip install pandas numpy
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "data"
DEFAULT_INPUT = DATA_DIR / "cleaned_survey.csv"
DEFAULT_OUTPUT = DATA_DIR / "analysis_dataset.csv"

# SDLC stage keys (output suffixes) -> Qualtrics column prefixes in CSV
STAGE_PREFIX: dict[str, str] = {
    "plan": "Planning",
    "design": "Design",
    "implementation": "Impl",
    "testing": "Testing",
    "deployment": "Deployment",
    "maintenance": "Maintenance",
}

STAGES: list[str] = list(STAGE_PREFIX.keys())

# TAM item index -> construct (from survey question order; Planning has BI as item 3)
TAM_INDEX_MAP_PLANNING: dict[int, str] = {
    1: "PEOU",
    2: "PU",
    3: "BI",
    4: "AU",
}
TAM_INDEX_MAP_DEFAULT: dict[int, str] = {
    1: "PEOU",
    2: "PU",
    3: "AU",
}

TAM_CONSTRUCTS: tuple[str, ...] = ("PEOU", "PU", "BI", "AU")

# Columns that store Likert 1–5 (plain number or Qualtrics label text)
LIKERT_COLUMN_PATTERN = re.compile(
    r"^(?:Literacy_FC_\d+|"
    r"(?:Planning|Design|Impl|Testing|Deployment|Maintenance)_(?:TAM|AUM)_\d+)$"
)

# Leading digit 1–5 for strings like "5 - Strongly Agree"
LIKERT_DIGIT_PATTERN = re.compile(r"^\s*([1-5])\b")


def likert_to_numeric(series: pd.Series) -> pd.Series:
    """Coerce Likert responses to floats in [1, 5]; invalid -> NaN."""

    def one_cell(v) -> float:
        if pd.isna(v):
            return np.nan
        if isinstance(v, (int, float, np.integer, np.floating)):
            x = float(v)
            return x if 1 <= x <= 5 else np.nan
        s = str(v).strip()
        m = LIKERT_DIGIT_PATTERN.match(s)
        if m:
            return float(m.group(1))
        # Fallback: pandas numeric parse
        try:
            x = float(pd.to_numeric(s, errors="coerce"))
            return x if 1 <= x <= 5 else np.nan
        except (TypeError, ValueError):
            return np.nan

    return series.map(one_cell).astype(float)


def apply_likert_to_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Convert all TAM, AUM, and Literacy_FC columns to numeric."""
    out = df.copy()
    for col in out.columns:
        if LIKERT_COLUMN_PATTERN.match(str(col)):
            out[col] = likert_to_numeric(out[col])
    return out


def tam_index_map_for_prefix(prefix: str) -> dict[int, str]:
    return TAM_INDEX_MAP_PLANNING if prefix == "Planning" else TAM_INDEX_MAP_DEFAULT


def compute_stage_tam(
    df: pd.DataFrame, stage_key: str, prefix: str
) -> dict[str, pd.Series]:
    """Return construct_name -> row-wise mean series for this stage."""
    index_map = tam_index_map_for_prefix(prefix)
    pat = re.compile(rf"^{re.escape(prefix)}_TAM_(\d+)$")

    # index -> column name
    idx_to_col: dict[int, str] = {}
    for col in df.columns:
        m = pat.match(str(col))
        if m:
            idx_to_col[int(m.group(1))] = col

    # construct -> list of column names
    by_construct: dict[str, list[str]] = {c: [] for c in TAM_CONSTRUCTS}
    for idx, construct in index_map.items():
        if idx in idx_to_col:
            by_construct[construct].append(idx_to_col[idx])

    out: dict[str, pd.Series] = {}
    for construct in TAM_CONSTRUCTS:
        cols = by_construct[construct]
        name = f"{construct}_{stage_key}"
        if cols:
            out[name] = df[cols].mean(axis=1, skipna=True)
        else:
            # No BI items outside Planning — explicit NaN column
            out[name] = pd.Series(np.nan, index=df.index, dtype=float)
    return out


def compute_stage_aum(df: pd.DataFrame, stage_key: str, prefix: str) -> pd.Series:
    pat = re.compile(rf"^{re.escape(prefix)}_AUM_(\d+)$")
    cols: list[str] = []
    for col in df.columns:
        if pat.match(str(col)):
            cols.append(col)
    cols.sort(key=lambda c: int(pat.match(c).group(1)))  # type: ignore[union-attr]
    if not cols:
        return pd.Series(np.nan, index=df.index, dtype=float)
    return df[cols].mean(axis=1, skipna=True)


def build_analysis_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Build output table with ResponseId and all computed constructs."""
    if "ResponseId" not in df.columns:
        raise ValueError("Expected column 'ResponseId' in cleaned survey.")

    pieces: dict[str, pd.Series] = {"ResponseId": df["ResponseId"].copy()}

    for stage_key, prefix in STAGE_PREFIX.items():
        tam_block = compute_stage_tam(df, stage_key, prefix)
        pieces.update(tam_block)
        pieces[f"AUM_{stage_key}"] = compute_stage_aum(df, stage_key, prefix)

    # Global literacy / FC (question order: items 1–3 literacy, 4–5 FC)
    lit_cols = [f"Literacy_FC_{i}" for i in (1, 2, 3)]
    fc_cols = [f"Literacy_FC_{i}" for i in (4, 5)]
    for group, name in [(lit_cols, "AI_Literacy"), (fc_cols, "Facilitating_Conditions")]:
        missing = [c for c in group if c not in df.columns]
        if missing:
            raise ValueError(f"Missing expected columns: {missing}")
        pieces[name] = df[group].mean(axis=1, skipna=True)

    return pd.DataFrame(pieces, index=df.index)


def print_validation(analysis: pd.DataFrame) -> None:
    """Mean, std, non-NaN count, NaN count per computed column."""
    print("\n=== Step 9: Basic validation ===\n")
    computed = [c for c in analysis.columns if c != "ResponseId"]
    rows = []
    for col in computed:
        s = analysis[col]
        valid = s.notna()
        rows.append(
            {
                "variable": col,
                "mean": s.mean(),
                "std": s.std(),
                "n_valid": int(valid.sum()),
                "n_nan": int((~valid).sum()),
            }
        )
    val_df = pd.DataFrame(rows)
    # Format means/stds
    pd.set_option("display.max_rows", 200)
    pd.set_option("display.width", 120)
    print(val_df.to_string(index=False, float_format=lambda x: f"{x:.4f}" if pd.notna(x) else ""))

    print("\n--- describe() on computed variables ---")
    print(analysis[computed].describe().T.to_string())


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build analysis_dataset.csv from cleaned_survey.csv"
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
        help=f"Output path (default: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()
    inp = args.input.expanduser()
    out = args.output.expanduser()

    # --- Step 1: Load ---
    print("=== Step 1: Load data ===")
    if not inp.is_file():
        print(f"Error: file not found: {inp}", file=sys.stderr)
        return 1
    df = pd.read_csv(inp, low_memory=False)
    print(f"Final N (rows): {len(df)}")

    # --- Step 2: Column names ---
    print("\n=== Step 2: Column names (inspection) ===")
    names = df.columns.tolist()
    for i, name in enumerate(names, 1):
        print(f"  {i:3d}. {name}")

    # --- Step 3: Likert conversion ---
    print("\n=== Step 3: Convert Likert to numeric (1–5) ===")
    df_num = apply_likert_to_dataframe(df)

    # --- Steps 4–8: Constructs + output frame ---
    print("\n=== Steps 4–8: Compute constructs and build output ===")
    analysis = build_analysis_frame(df_num)
    out_cols = [c for c in analysis.columns if c != "ResponseId"]
    print(f"Computed columns ({len(out_cols)}): {', '.join(out_cols)}")
    out.parent.mkdir(parents=True, exist_ok=True)
    analysis.to_csv(out, index=False)
    print(f"Saved: {out}")

    print_validation(analysis)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
