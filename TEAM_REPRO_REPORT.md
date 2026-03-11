# LexGuard — Team Reproducibility Report

**Team Members:** Manan Koradiya, Joe Doan, Ruixuan Hou, Aditya Naredla
**Project:** LexGuard — Neuro-Symbolic Compliance Auditor
**Date:** March 10, 2026
**Repository:** [github.com/Manan151179/BIG_DATA_LAB6](https://github.com/Manan151179/BIG_DATA_LAB6)

---

## 1. Reproducibility Objective

LexGuard is an AI-powered contract auditor that combines Snowflake data retrieval, rule-based risk classification, and Gemini LLM reasoning. Our reproducibility goal is to ensure that **any reviewer can clone the repository and verify core pipeline behavior in under 5 minutes**, without requiring Snowflake credentials, API keys, or proprietary data.

## 2. Dependency Management

All 18 Python dependencies are **pinned to exact versions** using `==` specifiers in `requirements.txt` — no floating ranges (`>=`, `~=`, `*`). Key dependencies include:

| Category | Packages | Versions |
|----------|----------|----------|
| Data & ML | `pandas`, `numpy`, `scikit-learn` | `2.3.3`, `2.4.2`, `1.8.0` |
| Document Processing | `pymupdf`, `pytesseract`, `pdf2image` | `1.27.1`, `0.3.13`, `1.17.0` |
| Retrieval & Vectors | `sentence-transformers`, `faiss-cpu`, `chromadb` | `5.2.3`, `1.13.2`, `1.5.1` |
| Cloud & GenAI | `snowflake-connector-python`, `google-genai` | `3.12.3`, `1.65.0` |
| Testing | `pytest` | `8.4.0` |

The `reproduce.sh` script creates an **isolated virtual environment** (`venv_repro/`) to prevent system-level package interference. Python ≥ 3.11 is enforced with an explicit version check.

## 3. Randomness & Determinism Controls

All sources of randomness are seeded via `config.py`, which is imported at the top of every module:

| Source | Seeding Mechanism | Verified By |
|--------|-------------------|-------------|
| Python `random` | `random.seed(42)` | `test_deterministic_uuids` |
| NumPy | `np.random.seed(42)` | `test_deterministic_uuids` |
| PyTorch (if installed) | `torch.manual_seed(42)` + cuDNN flags | `config.py` import |
| `PYTHONHASHSEED` | `os.environ["PYTHONHASHSEED"] = "42"` | `reproduce.sh` |
| UUID generation | `config.get_seeded_uuid()` (seeded `random.Random`) | `test_deterministic_uuids` |
| LLM temperature | Fixed at `0.1` via `AGENT_TEMPERATURE` | `config.HYPERPARAMS` |
| JSON serialization | `sort_keys=True` for byte-identical output | `test_local_store_determinism` |

**Deterministic UUID Generation:** Standard `uuid.uuid4()` was replaced with a custom `get_seeded_uuid()` that generates UUID-4-formatted strings from a seeded RNG. This ensures identical chunk IDs across runs when the same data is processed in the same order.

## 4. Configuration-Driven Execution

All hyperparameters are centralized in `config.py → HYPERPARAMS` and overridable via environment variables:

```python
HYPERPARAMS = {
    "global_seed": 42,            # GLOBAL_SEED env var
    "min_text_chars": 50,         # MIN_TEXT_CHARS env var
    "agent_temperature": 0.1,     # AGENT_TEMPERATURE env var
    "agent_max_steps": 5,         # AGENT_MAX_STEPS env var
    "retrieval_top_k": 5,         # RETRIEVAL_TOP_K env var
    "working_dir": "./project_data_store",  # LEXGUARD_WORKING_DIR env var
}
```

No magic numbers exist in the codebase — every tunable parameter traces back to this dictionary.

## 5. Automated Verification Results

Our smoke test suite (`tests/test_smoke.py`) contains **11 tests** that run against the real contract PDFs in `./data/` without any external service dependencies:

```
$ pytest tests/test_smoke.py -v
tests/test_smoke.py::test_pdf_discovery            PASSED   [  9%]
tests/test_smoke.py::test_chunk_extraction          PASSED   [ 18%]
tests/test_smoke.py::test_build_dataframe           PASSED   [ 27%]
tests/test_smoke.py::test_risk_calculator_high      PASSED   [ 36%]
tests/test_smoke.py::test_risk_calculator_medium    PASSED   [ 45%]
tests/test_smoke.py::test_risk_calculator_low       PASSED   [ 54%]
tests/test_smoke.py::test_clean_text                PASSED   [ 63%]
tests/test_smoke.py::test_deterministic_uuids       PASSED   [ 72%]
tests/test_smoke.py::test_local_store_separation    PASSED   [ 81%]
tests/test_smoke.py::test_local_store_search        PASSED   [ 90%]
tests/test_smoke.py::test_local_store_determinism   PASSED   [100%]

11 passed in 9.81s
```

Tests cover: PDF discovery, chunk extraction schema validation, DataFrame construction, risk classification (high/medium/low), text cleaning edge cases, deterministic UUID generation, local store file separation, keyword search retrieval, and cross-run storage determinism.

## 6. One-Command Reproduction

The entire verification pipeline is automated in `reproduce.sh`:

```bash
chmod +x reproduce.sh && ./reproduce.sh
```

**Execution steps:**
1. Verifies Python ≥ 3.11
2. Creates isolated `venv_repro/` virtual environment
3. Installs all pinned dependencies from `requirements.txt`
4. Sets `GLOBAL_SEED=42` and `PYTHONHASHSEED=42`
5. Runs all 11 smoke tests against real contract data
6. Generates `artifacts/run_manifest.json` (hyperparameters + execution metrics)
7. Prints summary with exit code 0 on success

**Expected wall-clock time:** ~12 seconds for test execution (after dependency installation).

## 7. Artifacts & Logging

Every pipeline run produces structured outputs in tracked directories:

| Directory | Contents | Purpose |
|-----------|----------|---------|
| `artifacts/` | `run_manifest.json` | Hyperparameters, timestamps, and metrics for each run |
| `artifacts/` | `phase3_eval_results*.csv` | Model evaluation metrics (baseline, Gemini, Ollama) |
| `logs/` | `pipeline_run.log` | Timestamped structured log of all pipeline events |
| `logs/` | `query_metrics.csv` | Retrieval latency and precision per query |
| `project_data_store/` | `kv_store_*.json` | Three separated JSON stores for offline retrieval |

## 8. Known Limitations

1. **LLM Non-Determinism:** Gemini API responses may vary between runs even at `temperature=0.1`. This affects `agent.py` outputs but not the retrieval or risk classification pipeline.
2. **OCR Variance:** Tesseract OCR output differs between major versions (4.x vs 5.x). We document the tested version in `RUN.md`.
3. **Cloud Dependency:** Snowflake ingestion and live agent queries require an active account with MFA. The full smoke test suite bypasses this entirely, using the local store for offline verification.
4. **Notebook Cell Ordering:** Jupyter notebooks (`phase_2.ipynb`, `phase_3.ipynb`) must be executed top-to-bottom; out-of-order execution may produce different results.

## 9. Credential Security

| Control | Status |
|---------|--------|
| `.env` excluded via `.gitignore` | ✅ |
| `.env.example` template committed | ✅ |
| No hardcoded keys in source code | ✅ |
| All credentials via `os.getenv()` | ✅ |
| MFA codes entered at runtime only | ✅ |
