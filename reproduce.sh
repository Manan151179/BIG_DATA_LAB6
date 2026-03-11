#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# LexGuard — Reproducibility Script
# ════════════════════════════════════════════════════════════════
# Creates a clean virtual environment, installs pinned deps,
# generates test fixtures, and runs the smoke-test suite.
#
# Usage:
#   chmod +x reproduce.sh
#   ./reproduce.sh
# ════════════════════════════════════════════════════════════════
set -euo pipefail

PYTHON="${PYTHON:-python3}"
VENV_DIR="venv_repro"

echo "═══════════════════════════════════════════════════════"
echo "  LexGuard — Reproducibility Runner"
echo "═══════════════════════════════════════════════════════"
echo ""

# ── 1. Check Python version ─────────────────────────────────
echo "🔍 Step 1: Checking Python version …"
PY_VERSION=$("$PYTHON" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$("$PYTHON" -c 'import sys; print(sys.version_info.major)')
PY_MINOR=$("$PYTHON" -c 'import sys; print(sys.version_info.minor)')

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 11 ]; }; then
    echo "❌ Python 3.11+ is required (found $PY_VERSION). Aborting."
    exit 1
fi
echo "   ✅ Python $PY_VERSION detected."

# ── 2. Create virtual environment ───────────────────────────
echo ""
echo "📦 Step 2: Creating virtual environment in ./$VENV_DIR …"
if [ -d "$VENV_DIR" ]; then
    echo "   ⚠  $VENV_DIR already exists — reusing."
else
    "$PYTHON" -m venv "$VENV_DIR"
    echo "   ✅ Virtual environment created."
fi

# Activate
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# ── 3. Install dependencies ─────────────────────────────────
echo ""
echo "📥 Step 3: Installing pinned dependencies …"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo "   ✅ All dependencies installed."

# ── 4. Set reproducibility env vars ─────────────────────────
echo ""
echo "🔧 Step 4: Setting reproducibility environment …"
export GLOBAL_SEED=42
export PYTHONHASHSEED=42
echo "   GLOBAL_SEED=$GLOBAL_SEED"
echo "   PYTHONHASHSEED=$PYTHONHASHSEED"

# ── 5. Run smoke tests against real contracts ───────────────
echo ""
echo "🧪 Step 5: Running smoke tests against ./data/ …"
"$PYTHON" -m pytest tests/test_smoke.py -v --tb=short

# ── 6. Generate run manifest ────────────────────────────────
echo ""
echo "📋 Step 6: Writing run manifest …"
"$PYTHON" -c "
import config
from lexguard_logger import write_run_manifest
path = write_run_manifest(hyperparams=config.HYPERPARAMS)
print(f'   ✅ Manifest written to {path}')
"

# ── 7. Summary ──────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════════"
echo "  ✅  All reproducibility checks PASSED"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "Artifacts dir:  ./artifacts/"
echo "  → run_manifest.json  (auto-generated)"
echo "  → phase3_eval_results*.csv"
echo "  → task1_antigravity_report.md"
echo "  → task4_evaluation_report.md"
echo "Logs dir:       ./logs/"
echo "Test fixtures:  ./tests/fixtures/"
echo ""

deactivate 2>/dev/null || true
