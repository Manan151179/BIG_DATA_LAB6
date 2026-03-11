# RUN.md — Step-by-Step Execution Guide

This document describes how to run each phase of the LexGuard pipeline from scratch.

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | ≥ 3.11 | Tested on 3.13 (macOS Apple Silicon) |
| Tesseract OCR | ≥ 5.0 | `brew install tesseract` on macOS |
| Poppler | ≥ 23.0 | `brew install poppler` (needed by `pdf2image`) |
| Snowflake account | — | With `COMPUTE_WH` warehouse access |
| Gemini API key | — | Google AI Studio |
| Groq API key | — | For Phase 2 notebook (optional) |

## Step 0: Environment Setup

```bash
# Clone the repository
git clone <repo-url>
cd LexGaurd

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install all pinned dependencies
pip install -r requirements.txt

# Configure credentials
cp .env.example .env
# Edit .env with your real keys
```

## Step 1: Data Ingestion (`ingest.py`)

Reads PDF contracts from `./data/`, chunks them page-by-page, and uploads to Snowflake.

```bash
python ingest.py
```

**What happens:**
1. Discovers all `.pdf` / `.PDF` files in `./data/`
2. Extracts text from each page using PyMuPDF
3. Falls back to OCR (Tesseract) for scanned/image-heavy pages
4. Builds a DataFrame and uploads to `LEXGUARD_DB.CONTRACT_DATA.CONTRACT_CHUNKS`
5. Prompts for Snowflake MFA/TOTP code at runtime

**Expected output:**
```
📂 Found 6 PDF(s) in './data/'
🧩 Total chunks extracted: ~50-80
☁️  Connecting to Snowflake …
✅ Upload complete
```

## Step 2: Retrieval & Evaluation (`phase_2.ipynb`)

Open in Jupyter and run all cells:

```bash
jupyter notebook phase_2.ipynb
```

**Covers:** TF-IDF vectorization, BM25 retrieval, FAISS semantic search, hybrid retrieval, cross-encoder re-ranking, and Groq LLM evaluation.

## Step 3: Multimodal Evaluation (`phase_3.ipynb`)

```bash
jupyter notebook phase_3.ipynb
```

**Covers:** Multi-modal document processing (text + OCR + images), Gemini-powered evaluation, and comparative metrics.

## Step 4: Agent Interaction (`app.py`)

Launch the Streamlit chat interface:

```bash
streamlit run app.py
```

**Usage:**
1. Enter your Snowflake MFA code in the sidebar
2. Ask questions like: *"Are there any high-risk indemnification clauses?"*
3. The agent retrieves relevant clauses and synthesizes a compliance verdict

## Smoke Test (Offline)

Run the full smoke-test suite without any external dependencies:

```bash
python tests/generate_fixtures.py    # Generate synthetic test data
pytest tests/test_smoke.py -v        # Run 9 offline tests
```

Or use the all-in-one script:

```bash
./reproduce.sh
```

## Directory Outputs

| Directory | Contents |
|-----------|----------|
| `artifacts/` | `run_manifest.json` — pipeline run summary |
| `artifacts/` | `phase3_eval_results.csv` — Phase 3 evaluation metrics |
| `artifacts/` | `phase3_eval_results_gemini.csv` — Gemini evaluation metrics |
| `artifacts/` | `phase3_eval_results_ollama.csv` — Ollama evaluation metrics |
| `artifacts/` | `task1_antigravity_report.md` — Task 1 report |
| `artifacts/` | `task4_evaluation_report.md` — Task 4 evaluation report |
| `logs/` | `pipeline_run.log` — structured execution logs |
| `logs/` | `query_metrics.csv` — retrieval latency & precision metrics |
| `tests/fixtures/` | `dummy_contract.pdf` — generated test data |
