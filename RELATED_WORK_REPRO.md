# RELATED_WORK_REPRO.md — Related Work Reproducibility Notes

This document tracks the reproducibility status of related systems and baselines that inform the LexGuard project.

---

## Template

For each related system, document:

| Field | Description |
|-------|-------------|
| **System** | Name and citation |
| **Code Available?** | Link to repository or "Not available" |
| **Data Available?** | Link to dataset or "Proprietary" |
| **Reproducible?** | Yes / Partial / No |
| **Notes** | Key findings from reproduction attempt |

---

## 1. RAG-based Contract Analysis Pipelines

| Field | Details |
|-------|---------|
| **System** | Standard RAG (Retrieval-Augmented Generation) |
| **Code Available?** | Multiple open-source implementations (LangChain, LlamaIndex) |
| **Data Available?** | Custom contract datasets; no standard benchmark |
| **Reproducible?** | Partial |
| **Notes** | LLM API non-determinism limits exact reproduction. Embedding models are reproducible with fixed seeds. Retrieval components (BM25, FAISS) are fully deterministic. |

## 2. Neuro-Symbolic Legal Reasoning

| Field | Details |
|-------|---------|
| **System** | Hybrid symbolic + neural approaches for legal NLP |
| **Code Available?** | Limited; most research is paper-only |
| **Data Available?** | CUAD dataset (public), ContractNLI (public) |
| **Reproducible?** | Partial |
| **Notes** | Rule-based components are fully reproducible. Neural components depend on model weights and training seeds. |

## 3. Snowflake + LLM Integration Patterns

| Field | Details |
|-------|---------|
| **System** | Enterprise data warehouse + generative AI agents |
| **Code Available?** | Snowflake Cortex documentation; no standardised codebase |
| **Data Available?** | Proprietary enterprise data |
| **Reproducible?** | No |
| **Notes** | Snowflake query results are deterministic for static data. LLM integration layer introduces non-determinism. MFA requirements add deployment complexity. |

## 4. HyperGraphRAG — N-ary Hypergraph Extraction Pipeline

| Field | Details |
|-------|---------|
| **System** | HyperGraphRAG (n-ary relational knowledge graph extraction via hypergraph modeling) |
| **Code Available?** | Yes — open-source repository on GitHub |
| **Data Available?** | Example contexts provided in-repo; no standardised legal-domain benchmark |
| **Reproducible?** | Partial |
| **Notes** | Dependency resolution succeeded; pipeline failed during local vector database initialization due to undocumented runtime assumptions. Storage architecture pattern was successfully adapted into LexGuard. |

### 4.1 What Was Attempted

Attempted to initialize the HyperGraphRAG n-ary extraction pipeline using the
provided example contexts. The reproduction environment was:

| Component | Version |
|-----------|---------|
| OS | macOS (Apple Silicon / MPS) |
| Python | 3.11+ |
| Package Manager | `pip` with `venv` isolation |

Steps taken:

1. Cloned the HyperGraphRAG repository and created an isolated virtual
   environment (`venv_repro/`).
2. Installed all dependencies from the project's `requirements.txt`.
   Pinned versions resolved without conflict against our existing stack
   (PyMuPDF `1.27.1`, `sentence-transformers 5.2.3`, `faiss-cpu 1.13.2`,
   `chromadb 1.5.1`).
3. Configured the pipeline's `working_dir` parameter and attempted to run
   the default extraction example to produce a hypergraph of entities and
   n-ary hyperedges.

### 4.2 What Worked / What Failed

**Dependency resolution: ✅ Succeeded.**  All Python packages installed
cleanly via their provided `requirements.txt`.  No version conflicts with
our existing LexGuard dependency set.

**Pipeline execution: ❌ Failed during local vector database initialization.**

The pipeline crashed when `HyperGraphRAG.__post_init__()` attempted to
instantiate its internal vector stores (`entities_vdb` and
`hyperedges_vdb`).  Root cause analysis:

1. **Undocumented `working_dir` filesystem assumption** — The pipeline's
   `JsonKVStorage` and `NanoVectorDBStorage` classes both assume that
   `working_dir` exists _and_ contains specific pre-initialized index
   files (e.g., `vdb_entities.json`, `vdb_hyperedges.json`).  The
   codebase auto-creates the directory, but the vector-DB layer expects
   pre-populated metadata headers that are never generated on a cold
   start without a valid LLM extraction preceding it.

2. **Implicit LLM coupling** — The extraction pipeline invokes an LLM
   (via `openai`-compatible API) to perform entity and relation
   extraction _before_ any data reaches the vector stores.  Without a
   configured and funded API key for the correct LLM provider, the
   pipeline halts with an opaque `APIConnectionError` before writing any
   vector indices, making the storage-layer behavior impossible to
   evaluate in isolation.

3. **`NanoVectorDBStorage` cold-start gap** — Even after bypassing the
   LLM call with mock entity data, `NanoVectorDBStorage.__post_init__`
   calls `self._max_batch_size` against an empty FAISS-like index,
   raising a `ValueError` because the dimensionality parameter defaults
   to `None` when no embeddings have been pre-computed.

**Summary of pipeline trace:**

```
HyperGraphRAG.__post_init__()
  → os.makedirs(working_dir)                         # ✅ OK
  → JsonKVStorage(namespace="full_docs", ...)         # ✅ OK (empty JSON)
  → JsonKVStorage(namespace="text_chunks", ...)       # ✅ OK (empty JSON)
  → NanoVectorDBStorage(namespace="entities", ...)    # ❌ FAIL
      → _load_index() expects pre-populated metadata
      → dimensionality=None → ValueError
```

### 4.3 Integration into LexGuard

Despite the pipeline's failure to run end-to-end, its **storage
architecture** provided a valuable design pattern.  We extracted the
following concepts and refactored LexGuard accordingly:

| HyperGraphRAG Concept | LexGuard Adaptation |
|------------------------|---------------------|
| `working_dir` auto-creation in `__post_init__` | `LocalStore.__init__` mirrors this: `os.makedirs(working_dir)` on first run |
| `JsonKVStorage` with namespaced files (`kv_store_{ns}.json`) | Three separated JSON stores: `kv_store_documents.json`, `kv_store_chunks.json`, `kv_store_clause_index.json` |
| Separate entity vs. hyperedge vector DBs | Separated document-level metadata from chunk-level data and clause keyword indices |
| `_insert_done` callback persists all stores atomically | `LocalStore.save_all()` writes all three namespaces after every ingestion batch |
| Deterministic key generation | `config.get_seeded_uuid()` replaces `uuid.uuid4()` for reproducible chunk IDs |
| `ainsert()` distributes data across multiple stores | `LocalStore.ingest()` fans out each chunk to documents, chunks, and clause_index stores |

**Key architectural change:** Prior to this integration, LexGuard stored
all contract data in a single Snowflake `CONTRACT_CHUNKS` table with no
local persistence. After studying HyperGraphRAG's separation of
`full_docs`, `text_chunks`, `entities_vdb`, and `hyperedges_vdb`, we
introduced `local_store.py` with three namespaced JSON files under
`./project_data_store/`.  This provides:

- **Offline-first retrieval**: Clause keyword search works without
  Snowflake connectivity or LLM API access.
- **Deterministic reproducibility**: JSON files are written with
  `sort_keys=True`, producing byte-identical output across runs given the
  same input data and seed.
- **Improved retrieval determinism**: The inverted keyword index
  (`kv_store_clause_index.json`) enables exact-match clause retrieval
  without embedding-model variance.

**Files modified as part of this integration:**

| File | Change |
|------|--------|
| `local_store.py` | **[NEW]** — Separated deterministic storage engine (241 LOC) |
| `config.py` | Added `working_dir` hyperparameter (line 98) |
| `ingest.py` | Added dual-write: local store + Snowflake (lines 303–306) |

---

## Adding New Entries

When evaluating a new related system for comparison:

1. Clone/download the repository (if available)
2. Attempt to reproduce the reported results
3. Document blockers (missing data, undocumented dependencies, etc.)
4. Record the reproduction environment (OS, Python version, hardware)
5. Add an entry to this document using the template above

---

## References

- **CUAD**: [Contract Understanding Atticus Dataset](https://www.atticusprojectai.org/cuad)
- **ContractNLI**: [Contract NLI Benchmark](https://stanfordnlp.github.io/contract-nli/)
- **LangChain RAG**: [LangChain Documentation](https://docs.langchain.com/)
- **Snowflake Cortex**: [Snowflake AI/ML Documentation](https://docs.snowflake.com/)
- **HyperGraphRAG**: [HyperGraphRAG Repository](https://github.com/HyperGraphRAG/HyperGraphRAG)
