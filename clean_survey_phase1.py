#!/usr/bin/env python3
"""
Phase 1: Qualtrics survey export — data cleaning and validation.

Usage:
  python clean_survey_phase1.py
  python clean_survey_phase1.py --input /path/to/survey_results.csv --output ./cleaned_survey.csv

Requires: pip install pandas
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

import pandas as pd

# Default input: survey export on Desktop (override with --input)
DEFAULT_INPUT = (
    Path.home()
    / "Desktop"
    / "AI Driven SDL Research"
    / "survey_results.csv"
)

DURATION_COL = "Duration (in seconds)"
DATE_START_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}")


def normalize_finished(series: pd.Series) -> pd.Series:
    """Map common Qualtrics / string truthy values to boolean; NaN stays False for filtering."""
    s = series.astype(str).str.strip().str.lower()
    true_vals = {"true", "1", "yes", "t"}
    return s.isin(true_vals)


def coerce_duration(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def coerce_progress(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def load_qualtrics_csv(path: Path, encoding: str = "utf-8") -> pd.DataFrame:
    """
    Load a Qualtrics CSV where row 1 is the variable-name header and following
    rows may contain question text / labels (including multiline quoted fields).

    Keeps only rows whose first column looks like a StartDate (YYYY-MM-DD...).
    """
    rows: list[list[str]] = []
    header: list[str] | None = None

    def try_open(enc: str):
        return open(path, "r", encoding=enc, newline="")

    try:
        f = try_open(encoding)
    except UnicodeDecodeError:
        f = try_open("utf-8-sig")
        encoding = "utf-8-sig"

    with f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return pd.DataFrame()

        started = False
        for row in reader:
            if not row:
                continue
            first = row[0].strip()
            if not started:
                if DATE_START_PATTERN.match(first):
                    started = True
                    rows.append(row)
                continue
            rows.append(row)

    if not header:
        return pd.DataFrame()

    df = pd.DataFrame(rows, columns=header)
    return df


def print_step_stats(step_name: str, n_before: int, n_after: int) -> None:
    removed = n_before - n_after
    pct = (100.0 * n_after / n_before) if n_before else 0.0
    print(f"\n--- {step_name} ---")
    print(f"  Before: {n_before}")
    print(f"  After:  {n_after}")
    print(f"  Removed: {removed}")
    print(f"  Retained: {pct:.1f}% of rows at start of this step")


def print_duration_noise_report(
    df: pd.DataFrame,
    duration_col: str,
    label: str,
    preview_cols: list[str] | None = None,
    preview_n: int = 10,
) -> None:
    """Report counts of very short / very long durations (no rows dropped)."""
    if duration_col not in df.columns:
        print(f"\n[{label}] Column {duration_col!r} missing; skipping noise report.")
        return

    d = df[duration_col]
    short = d.notna() & (d < 60)
    long_ = d.notna() & (d > 3600)
    print(f"\n--- Potential test / outlier durations ({label}) ---")
    print(f"  Duration < 60 s:   {int(short.sum())} rows")
    print(f"  Duration > 3600 s: {int(long_.sum())} rows")

    cols = preview_cols or []
    base = [c for c in ["ResponseId", "StartDate", duration_col] if c in df.columns]
    show = base + [c for c in cols if c in df.columns and c not in base]

    if short.any() and show:
        print(f"\n  Preview: duration < 60 s (up to {preview_n} rows)")
        print(df.loc[short, show].head(preview_n).to_string(index=False))
    if long_.any() and show:
        print(f"\n  Preview: duration > 3600 s (up to {preview_n} rows)")
        print(df.loc[long_, show].head(preview_n).to_string(index=False))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Qualtrics survey Phase 1: clean and validate responses."
    )
    p.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Path to survey_results.csv (default: {DEFAULT_INPUT})",
    )
    p.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output CSV path (default: cleaned_survey.csv next to this script)",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    out_path = args.output or (script_dir / "cleaned_survey.csv")
    input_path = args.input.expanduser()

    if not input_path.is_file():
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        return 1

    # -------------------------------------------------------------------------
    # Step 1: Load data
    # -------------------------------------------------------------------------
    print("=== Step 1: Load data ===")
    df = load_qualtrics_csv(input_path)
    n_initial = len(df)
    print(f"Initial number of response rows (after skipping Qualtrics preamble): {n_initial}")

    if n_initial == 0:
        print("No data rows loaded; exiting.")
        return 1

    # Numeric duration for all downstream logic
    if DURATION_COL not in df.columns:
        print(f"Error: expected column {DURATION_COL!r} not found.", file=sys.stderr)
        print(f"Columns: {list(df.columns)[:20]}...", file=sys.stderr)
        return 1

    df[DURATION_COL] = coerce_duration(df[DURATION_COL])

    # -------------------------------------------------------------------------
    # Step 3 (part): Diagnostics on raw loaded data — potential test entries
    # -------------------------------------------------------------------------
    print_duration_noise_report(
        df,
        DURATION_COL,
        label="raw loaded data (before main filters)",
    )

    # -------------------------------------------------------------------------
    # Step 2: Filter valid responses
    # -------------------------------------------------------------------------
    print("\n=== Step 2: Filter valid responses ===")
    n_before_filter = len(df)

    finished_ok = normalize_finished(df["Finished"]) if "Finished" in df.columns else pd.Series(False, index=df.index)
    if "Finished" not in df.columns:
        print("Warning: no 'Finished' column; treating all as not finished.")

    progress = coerce_progress(df["Progress"]) if "Progress" in df.columns else pd.Series(float("nan"), index=df.index)
    if "Progress" not in df.columns:
        print("Warning: no 'Progress' column; filter may remove all rows.")

    duration_ok = df[DURATION_COL].notna() & (df[DURATION_COL] > 120)
    n_invalid_duration = int((df[DURATION_COL].isna() | (df[DURATION_COL] <= 120)).sum())

    mask = finished_ok & (progress == 100) & duration_ok
    df_filt = df.loc[mask].copy()

    print(f"Rows with invalid or non-numeric duration (excluded by Duration > 120): {n_invalid_duration}")
    print_step_stats("Filter (Finished & Progress==100 & Duration > 120)", n_before_filter, len(df_filt))

    # -------------------------------------------------------------------------
    # Step 3: Remove noise — duplicates; post-filter long-duration preview
    # -------------------------------------------------------------------------
    print("\n=== Step 3: Remove noise ===")

    n_before_dedupe = len(df_filt)
    if "ResponseId" in df_filt.columns:
        df_clean = df_filt.drop_duplicates(subset=["ResponseId"], keep="first").copy()
        removed_dup = n_before_dedupe - len(df_clean)
        print(f"Duplicate removal (by ResponseId): removed {removed_dup} rows")
    else:
        df_clean = df_filt.drop_duplicates(keep="first").copy()
        removed_dup = n_before_dedupe - len(df_clean)
        print(f"No ResponseId column; full-row deduplication removed {removed_dup} rows")

    print_step_stats("After deduplication", n_before_dedupe, len(df_clean))

    print_duration_noise_report(
        df_clean,
        DURATION_COL,
        label="cleaned sample (after filters; inspect long durations)",
    )

    # -------------------------------------------------------------------------
    # Step 4: Final dataset
    # -------------------------------------------------------------------------
    print("\n=== Step 4: Final dataset ===")
    final_n = len(df_clean)
    print(f"Final N (valid responses): {final_n}")

    dur = df_clean[DURATION_COL]
    print("\nDuration (seconds) summary:")
    print(f"  Mean: {dur.mean():.2f}")
    print(f"  Min:  {dur.min():.2f}")
    print(f"  Max:  {dur.max():.2f}")

    overall_retained = (100.0 * final_n / n_initial) if n_initial else 0.0
    print(f"\nOverall: retained {final_n} of {n_initial} loaded rows ({overall_retained:.1f}%).")

    df_clean.to_csv(out_path, index=False)
    print(f"\nSaved: {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
