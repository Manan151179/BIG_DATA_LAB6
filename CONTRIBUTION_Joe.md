# Individual Contribution Report
**Name:** Joe Doan
**Role:** Data Pipeline & Ingestion Engineer

---

## Personal Responsibilities & Implemented Components

### 1. PDF Ingestion Pipeline (`ingest.py`)
- Built the complete **end-to-end data ingestion pipeline** that reads PDF contracts from `./data/`, extracts text page-by-page using PyMuPDF (`fitz`), and uploads structured chunks to Snowflake's `CONTRACT_CHUNKS` table.
- Implemented the **OCR fallback pipeline** for scanned or image-heavy pages: when PyMuPDF text extraction yields fewer than `MIN_TEXT_CHARS` (50) characters, the pipeline falls back to `pdf2image` + `pytesseract` at 300 DPI for accurate optical character recognition.
- Designed the **chunk data schema** with five fields (`CHUNK_ID`, `DOC_NAME`, `CHUNK_TEXT`, `METADATA`, `UPLOAD_TIMESTAMP`) that serves as the single source of truth for both Snowflake and the local store.
- Integrated **deterministic UUID generation** via `config.get_seeded_uuid()` to replace `uuid.uuid4()`, ensuring identical chunk IDs across repeated pipeline runs when processing the same documents in the same order.
- Implemented the `discover_pdfs()` utility to recursively discover `.pdf` and `.PDF` files in any directory, with a sorted output for deterministic processing order.
- Wrote the `clean_text()` function used across the entire pipeline for whitespace normalization — collapsing multiple spaces, tabs, and newlines into single spaces.

### 2. Snowflake Upload & Schema Management
- Implemented `get_snowflake_connection()` with full auto-provisioning: automatically creates the database, schema, and table (`CREATE IF NOT EXISTS`) before each upload, eliminating manual DDL setup.
- Integrated Snowflake's `write_pandas()` for efficient bulk upload — the function handles parquet staging and `COPY INTO` commands under the hood.
- Added **runtime MFA prompting** (`input()` for TOTP code) to support Snowflake's Multi-Factor Authentication requirement without storing temporary codes in `.env` files.
- Implemented error handling that catches `ProgrammingError` exceptions and provides actionable diagnostic messages (warehouse existence, role permissions).

### 3. Dual-Write Architecture
- After the HyperGraphRAG analysis, extended the ingestion pipeline to **dual-write**: chunks are persisted to both the `LocalStore` (offline JSON files) and Snowflake (cloud warehouse), ensuring the system works in both online and offline modes.
- Added `LocalStore` initialization and ingestion calls at lines 303–306 of `ingest.py`, triggered after chunk extraction and before Snowflake upload.

### 4. Data Directory & Contracts
- Curated and organized the 6 contract PDFs in `./data/`, sourced from public SEC filings and the CUAD dataset, covering diverse agreement types: co-branding, endorsement, manufacturing, servicing, and supply agreements.
- Verified that all PDFs are parseable by PyMuPDF and produce meaningful text extraction results across all pages.

---

## Links to Commits
- [Initial commit: environment setup](https://github.com/Manan151179/BIG_DATA_LAB6/commit/b6abf4a)
- [Initial commit for Lab 6: LexGuard Agent](https://github.com/Manan151179/BIG_DATA_LAB6/commit/7c4ea6e)

---

## Technical Reflection

The most significant engineering challenge was handling the diversity of PDF formats in real-world legal contracts. Some documents are natively digital with clean text layers, while others are scanned images requiring OCR. The two-tier extraction approach (PyMuPDF native → pytesseract fallback) reliably handles both cases, but I learned that OCR accuracy varies significantly between Tesseract versions (4.x vs 5.x) — a reproducibility concern we documented in `REPRO_AUDIT.md`. The dual-write architecture was inspired by studying HyperGraphRAG's storage separation pattern: writing to both a local JSON store and Snowflake ensures the system degrades gracefully when cloud connectivity is unavailable, which proved essential during development and testing cycles.
