# Individual Contribution Report
**Name:** Aditya Naredla
**Role:** Storage Architect & Evaluation Engineer

---

## Personal Responsibilities & Implemented Components

### 1. Separated Local Storage Engine (`local_store.py`)
- Designed and implemented the **`LocalStore` class** (241 LOC) — a deterministic, namespaced JSON storage engine inspired by HyperGraphRAG's `JsonKVStorage` pattern.
- Separated contract data into **three namespaced JSON files** under `./project_data_store/`:
  - `kv_store_documents.json` — document-level metadata (doc name, first-seen timestamp, associated chunk IDs)
  - `kv_store_chunks.json` — chunk-level data (text, metadata, timestamp keyed by deterministic UUID)
  - `kv_store_clause_index.json` — inverted keyword index mapping legal terms to chunk IDs for fast clause retrieval
- Implemented the **ingestion pipeline** (`LocalStore.ingest()`) that distributes each incoming chunk across all three stores simultaneously, mirroring HyperGraphRAG's `ainsert()` multi-store distribution pattern.
- Built the **clause search engine** (`LocalStore.search_clauses()`) with fuzzy keyword matching against the inverted index, deduplication while preserving insertion order, and configurable `top_k` result limiting.
- Ensured **byte-identical reproducibility** by writing all JSON files with `sort_keys=True` and `ensure_ascii=False`, guaranteeing deterministic serialization across runs.
- Implemented `save_all()` for atomic persistence of all three stores after each ingestion batch, mirroring HyperGraphRAG's `_insert_done` callback pattern.

### 2. HyperGraphRAG Related Work Analysis (`RELATED_WORK_REPRO.md`)
- Conducted the **HyperGraphRAG reproduction attempt**: cloned the repository, resolved dependencies in an isolated `venv_repro/` environment, and attempted to run the n-ary extraction pipeline.
- Performed **root cause analysis** of the pipeline failure, identifying three specific issues:
  1. Undocumented `working_dir` filesystem assumption in `NanoVectorDBStorage`
  2. Implicit LLM coupling that prevents storage-layer evaluation in isolation
  3. `NanoVectorDBStorage` cold-start gap where dimensionality defaults to `None` without pre-computed embeddings
- Documented the full reproduction attempt in `RELATED_WORK_REPRO.md` Section 4, including environment details, pipeline trace, and a concept-mapping table showing exactly which HyperGraphRAG patterns were adapted for LexGuard.

### 3. Keyword Extraction & Legal Domain Logic
- Curated the **legal keyword vocabulary** (`_LEGAL_KEYWORDS` list with 23 terms) used by the inverted clause index, covering key contract concepts: indemnification, termination, breach, liability, damages, force majeure, arbitration, confidentiality, and more.
- Implemented `_extract_keywords()` for case-insensitive keyword detection in chunk text, powering the inverted index construction during ingestion.

### 4. Evaluation Notebooks & Results
- Developed `phase_2.ipynb` covering retrieval evaluation: TF-IDF vectorization, BM25 retrieval, FAISS semantic search, hybrid retrieval strategies, and cross-encoder re-ranking with Groq LLM evaluation.
- Extended `phase_3.ipynb` for multimodal evaluation: processing text + OCR + image modalities, conducting Gemini-powered evaluation, and generating comparative metrics across models.
- Produced the evaluation result artifacts now stored in `artifacts/`:
  - `phase3_eval_results.csv` — baseline evaluation metrics
  - `phase3_eval_results_gemini.csv` — Gemini model evaluation results
  - `phase3_eval_results_ollama.csv` — Ollama local model evaluation results
  - `task1_antigravity_report.md` and `task4_evaluation_report.md` — detailed task reports

---

## Links to Commits
- [Initial commit for Lab 6: LexGuard Agent](https://github.com/Manan151179/BIG_DATA_LAB6/commit/7c4ea6e)
- [Organize artifacts and update smoke tests](https://github.com/Manan151179/BIG_DATA_LAB6/commit/098a9d0)

---

## Technical Reflection

The most valuable insight from the HyperGraphRAG analysis was learning how storage separation improves retrieval determinism. Before this work, LexGuard stored everything in a single Snowflake table — retrieval was tightly coupled to cloud connectivity and SQL query non-determinism. By studying how HyperGraphRAG separates its `full_docs`, `text_chunks`, `entities_vdb`, and `hyperedges_vdb` into distinct namespaced stores, I designed `LocalStore` to mirror this architecture with three JSON files. The key benefit is that the inverted keyword index (`kv_store_clause_index.json`) enables **exact-match clause retrieval** without embedding-model variance — unlike vector similarity search, keyword lookup is perfectly deterministic and produces identical results across any environment. This separation also enabled the team to run the full agent pipeline offline during development, using `retrieve_local_clauses()` as a drop-in replacement for the Snowflake retrieval tool.
