#!/usr/bin/env python3
"""
vmax_alpha/dolphin_chroma_bridge.py

Read-only ChromaDB G-Star snapshot adapter for V4.5-DOLPHIN (SYNC-26).
Snapshots stored embeddings into BANK_B for slow-wave dry-run auditing without
mutating live ChromaDB collections.

OP02-AST-clean: 0 semicolons, 0 tabs, flat functions (max McCabe CC <= 5).
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Optional

from vmax_alpha.dolphin_memory_governor import (
    DEFAULT_VECTOR_DIM,
    DolphinMemoryGovernor,
    GStarRecord,
    normalize_to_q2_30,
)


def _pad_or_slice(vec: List[float], dim: int = DEFAULT_VECTOR_DIM) -> List[float]:
    """Fit an embedding vector deterministically to the 64D Q2.30 manifold."""
    if len(vec) >= dim:
        return [float(x) for x in vec[:dim]]
    padded = [float(x) for x in vec]
    padded.extend([0.0] * (dim - len(padded)))
    return padded


def snapshot_collection_to_resting_bank(
    governor: DolphinMemoryGovernor,
    collection: Any,
    limit: int = 256,
) -> int:
    """
    Copy up to `limit` embeddings read-only from a ChromaDB-like collection
    into the governor's resting bank for dry-run slow-wave auditing.
    """
    payload = collection.get(include=["embeddings", "metadatas"], limit=limit)
    ids = payload.get("ids") or []
    raw_emb = payload.get("embeddings")
    embeddings = [] if raw_emb is None else raw_emb
    resting = governor.resting_bank()
    loaded = 0
    for idx, rec_id in enumerate(ids):
        if idx >= len(embeddings) or embeddings[idx] is None:
            continue
        vec = _pad_or_slice(list(embeddings[idx]))
        if sum(v * v for v in vec) <= 0.0:
            continue
        q_vec = normalize_to_q2_30(vec)
        resting.records[str(rec_id)] = GStarRecord(
            record_id=str(rec_id),
            epoch=governor.epoch,
            vector_q30=q_vec,
        )
        loaded += 1
    return loaded


def run_dry_run_audit(
    governor: DolphinMemoryGovernor,
    collection: Any,
    hbm_temp_c: float = 65.0,
    limit: int = 256,
) -> Dict[str, Optional[object]]:
    """Run a non-mutating slow-wave audit on a read-only ChromaDB snapshot."""
    loaded = snapshot_collection_to_resting_bank(governor, collection, limit=limit)
    cert = governor.run_resting_sweep(hbm_temp_c=hbm_temp_c)
    return {
        "dry_run": True,
        "loaded_records": loaded,
        "certificate": asdict(cert),
    }
def _extract_record_key_and_hash(item: Any, idx: int) -> tuple:
    """Extract (record_id, content_hash) from a GStarRecord, dict, or raw string."""
    if hasattr(item, "record_id") and hasattr(item, "content_hash"):
        return str(item.record_id), str(item.content_hash)
    if isinstance(item, dict):
        rec_id = str(item.get("record_id", item.get("id", f"rec_{idx}")))
        c_hash = str(item.get("content_hash", ""))
        return rec_id, c_hash
    return f"rec_{idx}", str(item)


def audit_content_hash_duplicates(records: Any) -> Dict[str, object]:
    """
    Strictly read-only opt-in audit counting exact duplicate content_hash entries.
    Never mutates input records or live ChromaDB collections.
    """
    seen: Dict[str, str] = {}
    duplicate_ids: List[str] = []
    total = 0
    for idx, item in enumerate(records):
        total += 1
        rec_id, c_hash = _extract_record_key_and_hash(item, idx)
        if not c_hash:
            continue
        if c_hash in seen:
            duplicate_ids.append(rec_id)
        else:
            seen[c_hash] = rec_id
    dup_count = len(duplicate_ids)
    ratio = round(100.0 * dup_count / total, 2) if total > 0 else 0.0
    return {
        "dry_run": True,
        "total_records": total,
        "unique_hashes": len(seen),
        "duplicate_count": dup_count,
        "duplicate_ratio_pct": ratio,
        "duplicate_ids": duplicate_ids,
    }
