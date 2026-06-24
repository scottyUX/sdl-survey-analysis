#!/usr/bin/env bash
# Run the full survey analysis pipeline (Phases 1–3 + inferential stats + dashboard).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

INPUT="${1:-}"

run_phase1() {
  if [[ -n "$INPUT" ]]; then
    python3 clean_survey_phase1.py --input "$INPUT"
  else
    python3 clean_survey_phase1.py
  fi
}

echo "=== Phase 1: Clean Qualtrics export ==="
run_phase1

echo ""
echo "=== Phase 2: Build analysis dataset ==="
python3 build_analysis_dataset.py

echo ""
echo "=== Phase 3: Descriptive analysis + figures ==="
python3 survey_phase3_analysis.py

echo ""
echo "=== Phase 4: AUM reliability (Cronbach's alpha) ==="
python3 stats_reliability.py

echo ""
echo "=== Phase 5: Friedman + Wilcoxon inference ==="
python3 stats_inference.py

echo ""
echo "=== Phase 6: Regenerate dashboard ==="
python3 generate_survey_dashboard.py

echo ""
echo "Done. Open index.html via: python3 -m http.server 8765"
