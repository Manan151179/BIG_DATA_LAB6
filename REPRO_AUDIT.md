# REPRO_AUDIT.md — Reproducibility Audit

This document certifies the reproducibility controls in the LexGuard project.

---

## Audit Checklist

### 🔒 Dependency Pinning

| Check | Status | Details |
|-------|--------|---------|
| All Python packages pinned with `==` versions | ✅ | See `requirements.txt` |
| No floating version specifiers (`>=`, `~=`, `*`) | ✅ | Every dependency is exact |
| System dependencies documented | ✅ | Tesseract, Poppler in `RUN.md` |
| Virtual environment isolation | ✅ | `reproduce.sh` creates `venv_repro/` |

### 🎲 Randomness Control

| Source | Seeded? | Mechanism |
|--------|---------|-----------|
| Python `random` | ✅ | `random.seed(GLOBAL_SEED)` in `config.py` |
| NumPy | ✅ | `np.random.seed(GLOBAL_SEED)` in `config.py` |
| PyTorch (if installed) | ✅ | `torch.manual_seed()` + CUDA + cuDNN flags |
| `PYTHONHASHSEED` | ✅ | `os.environ["PYTHONHASHSEED"]` set in `config.py` |
| UUID generation | ✅ | `config.get_seeded_uuid()` replaces `uuid.uuid4()` |
| LLM temperature | ✅ | Fixed at `0.1` via `AGENT_TEMPERATURE` env var |

### 🔧 Configuration Management

| Parameter | Source | Default |
|-----------|--------|---------|
| `GLOBAL_SEED` | Environment variable | `42` |
| `MIN_TEXT_CHARS` | Environment variable | `50` |
| `AGENT_TEMPERATURE` | Environment variable | `0.1` |
| `AGENT_MAX_STEPS` | Environment variable | `5` |
| `RETRIEVAL_TOP_K` | Environment variable | `5` |

All hyperparameters are centralized in `config.py` → `HYPERPARAMS` dict.

### 🔐 Credential Security

| Check | Status | Details |
|-------|--------|---------|
| `.env` in `.gitignore` | ✅ | Prevents accidental credential commits |
| `.env.example` provides template | ✅ | All vars listed with placeholder values |
| No hardcoded API keys in source | ✅ | All use `os.getenv()` / `os.environ.get()` |
| No credentials in notebooks | ✅ | Notebooks use `load_dotenv()` + `os.getenv()` |

### 🧪 Automated Verification

| Test | What It Validates |
|------|-------------------|
| `test_pdf_discovery` | PDF file discovery works |
| `test_chunk_extraction` | Text extraction produces valid chunks |
| `test_build_dataframe` | DataFrame schema matches Snowflake table |
| `test_risk_calculator_high` | "indemnify" → High Risk |
| `test_risk_calculator_medium` | "penalty" → Medium Risk |
| `test_risk_calculator_low` | Neutral text → Low Risk |
| `test_clean_text` | Whitespace normalization correctness |
| `test_deterministic_uuids` | Same seed → identical chunk IDs |
| `test_local_store_separation` | Ingestion creates 3 namespaced JSON files |
| `test_local_store_search` | Clause keyword search returns correct results |
| `test_local_store_determinism` | Two ingestion runs → identical output |

### 📊 Logging & Artifacts

| Output | Location | Purpose |
|--------|----------|---------|
| Execution log | `logs/pipeline_run.log` | Timestamped pipeline events |
| Run manifest | `artifacts/run_manifest.json` | Hyperparams + metrics summary |
| Query metrics | `logs/query_metrics.csv` | Retrieval latency & precision |

---

## Reproduction Steps

```bash
# Full offline verification (no API keys needed)
./reproduce.sh

# Expected: all 8 tests pass, exit code 0
```

## Known Limitations

1. **LLM non-determinism**: Gemini API responses may vary slightly between runs even at `temperature=0.1`. This affects `agent.py` and notebook evaluation cells.
2. **OCR variance**: Tesseract OCR output may differ across versions (`5.x` vs `4.x`).
3. **Snowflake dependency**: Ingestion and live agent queries require an active Snowflake account. Smoke tests bypass this entirely.
4. **Notebook cell ordering**: Jupyter notebooks must be run top-to-bottom; out-of-order execution may produce different results.
