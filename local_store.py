"""
LexGuard — LocalStore: Separated Deterministic Storage
========================================================
Inspired by HyperGraphRAG's namespaced JsonKVStorage + working_dir pattern.

Instead of mixing all contract data into a single Snowflake table,
this module separates data into three deterministic, namespaced JSON
files under a local working directory:

    working_dir/
    ├── kv_store_documents.json      # doc-level metadata
    ├── kv_store_chunks.json         # chunk_id → text + metadata
    └── kv_store_clause_index.json   # keyword → [chunk_ids]

Design decisions lifted from HyperGraphRAG:
    • working_dir is auto-created if it doesn't exist
    • Each store is a separate file with a `kv_store_{namespace}` naming convention
    • Data is keyed by deterministic IDs (seeded UUIDs from config.py)
    • JSON is written with sorted keys for byte-identical reproducibility

Usage:
    from local_store import LocalStore
    store = LocalStore(working_dir="./project_data_store")
    store.ingest(chunks)                         # persist after extraction
    results = store.search_clauses("indemnify")  # local retrieval
"""

import json
import os
import re
from collections import defaultdict
from pathlib import Path

from lexguard_logger import get_logger

logger = get_logger(__name__)

# ──────────────────────────────────────────────
# Keyword extraction for the clause index
# ──────────────────────────────────────────────
# Legal keywords that are relevant for clause-type indexing.
# Kept deliberately small and domain-specific; extend as needed.
_LEGAL_KEYWORDS = [
    "indemnify", "indemnification", "termination", "penalty", "penalties",
    "breach", "liability", "damages", "security deposit", "rent",
    "notice", "governing law", "arbitration", "confidentiality",
    "insurance", "subletting", "assignment", "default", "waiver",
    "force majeure", "maintenance", "repairs", "eviction",
]


def _extract_keywords(text: str) -> list[str]:
    """Return legal keywords found in the text (case-insensitive)."""
    text_lower = text.lower()
    return [kw for kw in _LEGAL_KEYWORDS if kw in text_lower]


# ──────────────────────────────────────────────
# LocalStore — mirrors HyperGraphRAG's storage separation
# ──────────────────────────────────────────────
class LocalStore:
    """Separated, deterministic local storage for LexGuard contract data.

    Modeled after HyperGraphRAG's initialization pattern where each storage
    concern gets its own namespaced file under a shared working_dir.

    Attributes:
        working_dir:  Root directory for all persisted data.
        documents:    dict  — doc_name → metadata (namespace: "documents")
        chunks:       dict  — chunk_id → {text, metadata} (namespace: "chunks")
        clause_index: dict  — keyword → [chunk_ids] (namespace: "clause_index")
    """

    # Namespace → filename mapping, following HyperGraphRAG's kv_store_{ns}.json convention
    _NAMESPACES = {
        "documents":    "kv_store_documents.json",
        "chunks":       "kv_store_chunks.json",
        "clause_index": "kv_store_clause_index.json",
    }

    def __init__(self, working_dir: str = "./project_data_store"):
        self.working_dir = working_dir

        # Auto-create working_dir (mirrors HyperGraphRAG.__post_init__)
        if not os.path.exists(self.working_dir):
            logger.info(f"Creating working directory: {self.working_dir}")
            os.makedirs(self.working_dir)

        # Load each namespaced store from its own JSON file
        self.documents: dict = self._load("documents")
        self.chunks: dict = self._load("chunks")
        self.clause_index: dict = self._load("clause_index")

        logger.info(
            f"LocalStore initialized — "
            f"{len(self.documents)} docs, "
            f"{len(self.chunks)} chunks, "
            f"{len(self.clause_index)} indexed keywords"
        )

    # ──────────────────────────────────────────
    # Persistence (mirroring JsonKVStorage._load / index_done_callback)
    # ──────────────────────────────────────────
    def _filepath(self, namespace: str) -> str:
        return os.path.join(self.working_dir, self._NAMESPACES[namespace])

    def _load(self, namespace: str) -> dict:
        """Load a namespaced JSON store from disk, or return empty dict."""
        fpath = self._filepath(namespace)
        if os.path.exists(fpath):
            with open(fpath, encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"Loaded {namespace} store with {len(data)} entries")
            return data
        return {}

    def _save(self, namespace: str) -> None:
        """Persist a namespaced store to its JSON file with sorted keys."""
        fpath = self._filepath(namespace)
        data = getattr(self, namespace)
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)
        logger.debug(f"Saved {namespace} store ({len(data)} entries) → {fpath}")

    def save_all(self) -> None:
        """Persist all three stores (mirrors HyperGraphRAG._insert_done)."""
        for ns in self._NAMESPACES:
            self._save(ns)
        logger.info("All local stores saved.")

    # ──────────────────────────────────────────
    # Ingestion
    # ──────────────────────────────────────────
    def ingest(self, chunks: list[dict]) -> None:
        """Ingest extracted chunks into the three separated stores.

        Each chunk dict is expected to have:
            CHUNK_ID, DOC_NAME, CHUNK_TEXT, METADATA, UPLOAD_TIMESTAMP

        This mirrors HyperGraphRAG's ainsert() which distributes data across
        full_docs, text_chunks, entities_vdb, and hyperedges_vdb.
        """
        if not chunks:
            logger.warning("No chunks to ingest.")
            return

        new_docs = 0
        new_chunks = 0

        for chunk in chunks:
            chunk_id = chunk["CHUNK_ID"]
            doc_name = chunk["DOC_NAME"]
            text = chunk["CHUNK_TEXT"]
            metadata = chunk["METADATA"]
            timestamp = chunk["UPLOAD_TIMESTAMP"]

            # ── Documents store (doc-level metadata) ──
            if doc_name not in self.documents:
                self.documents[doc_name] = {
                    "doc_name": doc_name,
                    "first_seen": timestamp,
                    "chunk_ids": [],
                }
                new_docs += 1
            self.documents[doc_name]["chunk_ids"].append(chunk_id)

            # ── Chunks store (chunk-level data) ──
            if chunk_id not in self.chunks:
                self.chunks[chunk_id] = {
                    "doc_name": doc_name,
                    "text": text,
                    "metadata": metadata,
                    "timestamp": timestamp,
                }
                new_chunks += 1

            # ── Clause index (inverted keyword index) ──
            keywords = _extract_keywords(text)
            for kw in keywords:
                if kw not in self.clause_index:
                    self.clause_index[kw] = []
                if chunk_id not in self.clause_index[kw]:
                    self.clause_index[kw].append(chunk_id)

        logger.info(
            f"Ingested {new_chunks} new chunks from {new_docs} new docs "
            f"({len(self.clause_index)} keywords indexed)"
        )

        # Persist all stores after ingestion (mirrors HyperGraphRAG._insert_done)
        self.save_all()

    # ──────────────────────────────────────────
    # Retrieval
    # ──────────────────────────────────────────
    def search_clauses(self, keyword: str, top_k: int = 5) -> list[dict]:
        """Search the clause index for chunks matching a keyword.

        Returns a list of dicts with doc_name + text, similar to how
        HyperGraphRAG queries its entities_vdb then retrieves from the graph.
        """
        keyword_lower = keyword.strip().lower()

        # Gather chunk IDs from all matching index entries
        matching_ids: list[str] = []
        for indexed_kw, chunk_ids in self.clause_index.items():
            if keyword_lower in indexed_kw.lower():
                matching_ids.extend(chunk_ids)

        # Deduplicate while preserving order
        seen = set()
        unique_ids = []
        for cid in matching_ids:
            if cid not in seen:
                seen.add(cid)
                unique_ids.append(cid)

        # Retrieve chunk text (up to top_k)
        results = []
        for cid in unique_ids[:top_k]:
            chunk_data = self.chunks.get(cid)
            if chunk_data:
                results.append({
                    "chunk_id": cid,
                    "doc_name": chunk_data["doc_name"],
                    "text": chunk_data["text"],
                })

        logger.info(
            f"search_clauses('{keyword}') → {len(results)} results "
            f"(from {len(matching_ids)} index hits)"
        )
        return results

    def get_all_chunks(self) -> list[dict]:
        """Return all stored chunks as a list of dicts."""
        return [
            {"chunk_id": cid, **data}
            for cid, data in self.chunks.items()
        ]
