#!/usr/bin/env python3
"""
vmax_alpha/projector_cache.py

Zero-VRAM CPU cache for the canonical 72-anchor Householder QR projection
matrix W_384_to_64 (192 KiB float64) and background mean vector mean_384.

OP02-AST-clean: 0 semicolons, 0 tabs, flat functions (max McCabe CC <= 5).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, Tuple

import numpy as np

DEFAULT_CACHE_DIR = Path(__file__).resolve().parent / "cache"
W_FILENAME = "w_384_to_64.npy"
MEAN_FILENAME = "mean_384.npy"
MANIFEST_FILENAME = "projector_manifest.json"


def _sha256_bytes(data: bytes) -> str:
    """Return hex SHA-256 digest of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def save_projector_cache(
    cache_dir: Path,
    mean_384: np.ndarray,
    w_384_to_64: np.ndarray,
    anchor_count: int = 72,
) -> Dict[str, object]:
    """Persist mean_384 and W_384_to_64 as float64 .npy files with SHA-256 manifest."""
    target = Path(cache_dir)
    target.mkdir(parents=True, exist_ok=True)
    mean_arr = np.ascontiguousarray(mean_384, dtype=np.float64)
    w_arr = np.ascontiguousarray(w_384_to_64, dtype=np.float64)
    if mean_arr.shape != (384,) or w_arr.shape != (384, 64):
        raise ValueError(f"Unexpected projector shapes: {mean_arr.shape}, {w_arr.shape}")
    mean_p = target / MEAN_FILENAME
    w_p = target / W_FILENAME
    np.save(mean_p, mean_arr)
    np.save(w_p, w_arr)
    manifest: Dict[str, object] = {
        "schema": "VMAX_PROJECTOR_CACHE_V1",
        "anchor_count": anchor_count,
        "dtype": "float64",
        "mean_file": MEAN_FILENAME,
        "mean_shape": list(mean_arr.shape),
        "mean_bytes": mean_p.stat().st_size,
        "mean_sha256": _sha256_bytes(mean_p.read_bytes()),
        "w_file": W_FILENAME,
        "w_shape": list(w_arr.shape),
        "w_bytes": w_p.stat().st_size,
        "w_sha256": _sha256_bytes(w_p.read_bytes()),
    }
    (target / MANIFEST_FILENAME).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def load_projector_cache(
    cache_dir: Path = DEFAULT_CACHE_DIR,
) -> Tuple[np.ndarray, np.ndarray, Dict[str, object]]:
    """Load cached mean_384 and W_384_to_64 on CPU after SHA-256 verification."""
    target = Path(cache_dir)
    manifest = json.loads((target / MANIFEST_FILENAME).read_text(encoding="utf-8"))
    mean_p = target / str(manifest["mean_file"])
    w_p = target / str(manifest["w_file"])
    if _sha256_bytes(mean_p.read_bytes()) != manifest["mean_sha256"]:
        raise ValueError("mean_384.npy SHA-256 verification failed")
    if _sha256_bytes(w_p.read_bytes()) != manifest["w_sha256"]:
        raise ValueError("w_384_to_64.npy SHA-256 verification failed")
    mean_arr = np.load(mean_p, allow_pickle=False).astype(np.float64, copy=False)
    w_arr = np.load(w_p, allow_pickle=False).astype(np.float64, copy=False)
    return mean_arr, w_arr, manifest


def project_384_to_64_cpu(
    vec_384: np.ndarray,
    mean_384: np.ndarray,
    w_384_to_64: np.ndarray,
) -> np.ndarray:
    """Deterministically project 1D or 2D float64 384D embeddings onto unit S^63 on CPU."""
    arr = np.asarray(vec_384, dtype=np.float64)
    if arr.ndim == 1:
        proj = (arr - mean_384) @ w_384_to_64
        norm = float(np.linalg.norm(proj))
        return proj / max(norm, 1e-12)
    proj = (arr - mean_384[None, :]) @ w_384_to_64
    norms = np.clip(np.linalg.norm(proj, axis=1, keepdims=True), 1e-12, None)
    return proj / norms
