# Individual Contribution Report
**Name:** Ruixuan Hou
**Role:** Reproducibility & Testing Lead

---

## Personal Responsibilities & Implemented Components

### 1. Deterministic Configuration System (`config.py`)
- Designed and implemented the **centralized configuration module** that seeds all sources of randomness on import: Python's `random`, NumPy's RNG, PyTorch (with CUDA and cuDNN determinism flags), and `PYTHONHASHSEED`.
- Built the **deterministic UUID generator** (`get_seeded_uuid()`) — a custom implementation that generates UUID-4-formatted strings from a seeded `random.Random` instance, ensuring identical chunk IDs across runs without relying on the non-deterministic `uuid.uuid4()`.
- Centralized all pipeline hyperparameters into the `HYPERPARAMS` dictionary with environment-variable overrides, providing a single source of truth for `GLOBAL_SEED`, `MIN_TEXT_CHARS`, `AGENT_TEMPERATURE`, `AGENT_MAX_STEPS`, `RETRIEVAL_TOP_K`, and `working_dir`.
- Implemented **device auto-detection** (`get_device()`) with priority: Apple Silicon MPS → NVIDIA CUDA → CPU, ensuring the pipeline runs optimally across different hardware.

### 2. Centralized Logging & Metrics (`lexguard_logger.py`)
- Built the **structured logging framework** with dual output (console + rotating log file at `logs/pipeline_run.log`), using ISO-8601 timestamps and severity-level formatting.
- Implemented `log_hyperparams()` for formatted parameter logging at pipeline start, and `log_metrics()` for recording arbitrary key-value execution metrics with UTC timestamps.
- Created `write_run_manifest()` to generate `artifacts/run_manifest.json` — a JSON summary of each pipeline run containing completion timestamp, hyperparameters, and all recorded metrics.
- Set up automatic directory creation for `logs/` and `artifacts/` on module import, ensuring the pipeline never fails due to missing output directories.

### 3. Smoke Test Suite (`tests/test_smoke.py`)
- Authored all **11 smoke tests** covering the full pipeline without requiring external API keys or Snowflake connectivity:
  - `test_pdf_discovery` — verifies `discover_pdfs()` finds all contracts in `./data/`
  - `test_chunk_extraction` — validates chunk schema (`CHUNK_ID`, `DOC_NAME`, `CHUNK_TEXT`, `METADATA`, `UPLOAD_TIMESTAMP`)
  - `test_build_dataframe` — confirms DataFrame column ordering matches the Snowflake table schema
  - `test_risk_calculator_high/medium/low` — unit tests for the rule-based risk classifier
  - `test_clean_text` — edge-case testing for whitespace normalization (empty strings, `None`, newlines/tabs)
  - `test_deterministic_uuids` — proves that resetting the UUID RNG seed produces identical chunk IDs
  - `test_local_store_separation` — validates that `LocalStore.ingest()` creates three separate JSON files
  - `test_local_store_search` — tests the clause keyword search returns correct results and returns empty for absent keywords
  - `test_local_store_determinism` — proves two independent ingestion runs (after seed reset) produce byte-identical JSON stores (after stripping wall-clock timestamps)
- Designed the `data_dir` pytest fixture to point tests at the real contract PDFs in `./data/`, ensuring tests validate against actual production data.

### 4. Reproducibility Infrastructure (`reproduce.sh`, `REPRO_AUDIT.md`)
- Wrote the **one-command reproducibility script** (`reproduce.sh`) that creates an isolated virtual environment, installs pinned dependencies, sets determinism environment variables, runs the full test suite, and generates `run_manifest.json`.
- Authored `REPRO_AUDIT.md` — a comprehensive audit checklist covering dependency pinning, randomness control, configuration management, credential security, automated verification, and logging/artifact outputs.
- Created `.env.example` with placeholder values for all required environment variables.
- Configured `.gitignore` to track result files in `artifacts/` while excluding auto-generated files (`run_manifest.json`) and sensitive credentials (`.env`).

---

## Links to Commits
- [Initial commit: environment setup](https://github.com/Manan151179/BIG_DATA_LAB6/commit/b6abf4a)
- [Organize artifacts and update smoke tests](https://github.com/Manan151179/BIG_DATA_LAB6/commit/098a9d0)

---

## Technical Reflection

The core challenge in reproducibility engineering was handling the tension between determinism and real-world variability. LLM API responses are inherently non-deterministic even at low temperatures, OCR output varies across Tesseract versions, and Snowflake queries depend on mutable cloud state. My approach was to draw a clear boundary: everything *within our control* (seeds, UUIDs, file ordering, JSON serialization with `sort_keys=True`) is made fully deterministic, while external non-determinism (LLM responses, OCR engine versions) is explicitly documented as a known limitation in `REPRO_AUDIT.md`. The most satisfying test to write was `test_local_store_determinism`, which proves that two completely independent pipeline runs — from PDF parsing through chunk extraction to JSON storage — produce mathematically identical outputs when given the same seed, after stripping wall-clock timestamps.
