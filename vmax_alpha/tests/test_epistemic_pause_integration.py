#!/usr/bin/env python3
"""
vmax_alpha/tests/test_epistemic_pause_integration.py

Integration tests for SYNC-28 (V4.6-PAUSE):
- WP-1: Ephemeral server_hud.py /api/prompt coherent pass-through & Epistemic Pause
- WP-2: Zero-VRAM 192 KiB W_384_to_64 projector cache save/load & tamper rejection
- WP-3: Read-only opt-in content_hash duplicate audit helper

OP02-AST-clean: 0 semicolons, 0 tabs, flat test methods (max McCabe CC <= 4).
"""

from __future__ import annotations

import json
import tempfile
import threading
import unittest
import urllib.request
from dataclasses import dataclass
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import List

import numpy as np

from vmax_alpha.dolphin_chroma_bridge import audit_content_hash_duplicates
from vmax_alpha.dolphin_memory_governor import (
    DEFAULT_VECTOR_DIM,
    GStarRecord,
    normalize_to_q2_30,
)
from vmax_alpha.projector_cache import (
    DEFAULT_CACHE_DIR,
    MANIFEST_FILENAME,
    W_FILENAME,
    load_projector_cache,
    project_384_to_64_cpu,
    save_projector_cache,
)
from vmax_alpha.server_hud import make_hud_handler


@dataclass
class _StubLedgerEntry:
    cycle: int
    prompt: str
    status: str


class _StubHudService:
    def __init__(self) -> None:
        self.step_calls = 0

    def step_cycle(self, prompt: str = "", inject_g3_torsion: float = 0.0) -> _StubLedgerEntry:
        self.step_calls += 1
        return _StubLedgerEntry(cycle=self.step_calls, prompt=prompt, status="OK")


def _axis_vec(dim: int, c0: float, c1: float, c2: float = 0.0) -> List[float]:
    vals = [0.0] * dim
    vals[0] = c0
    vals[1] = c1
    vals[2] = c2
    return vals


class TestEpistemicPauseIntegration(unittest.TestCase):
    """Verify WP-1 HTTP hooks, WP-2 projector cache, and WP-3 duplicate audit."""

    def test_projector_cache_roundtrip_and_tamper_detection(self) -> None:
        rng = np.random.RandomState(42)
        mean_arr = rng.randn(384).astype(np.float64)
        w_arr = rng.randn(384, 64).astype(np.float64)
        with tempfile.TemporaryDirectory() as tmp:
            cache_dir = Path(tmp)
            manifest = save_projector_cache(cache_dir, mean_arr, w_arr, anchor_count=72)
            self.assertEqual(manifest["w_shape"], [384, 64])
            m2, w2, _ = load_projector_cache(cache_dir)
            self.assertTrue(np.array_equal(mean_arr, m2))
            self.assertTrue(np.array_equal(w_arr, w2))
            vec_out = project_384_to_64_cpu(rng.randn(384), m2, w2)
            self.assertAlmostEqual(float(np.linalg.norm(vec_out)), 1.0, places=9)
            w_path = cache_dir / W_FILENAME
            raw = bytearray(w_path.read_bytes())
            raw[-1] ^= 0xFF
            w_path.write_bytes(bytes(raw))
            with self.assertRaises(ValueError):
                load_projector_cache(cache_dir)

    def test_canonical_projector_cache_verified_if_present(self) -> None:
        if not (DEFAULT_CACHE_DIR / MANIFEST_FILENAME).exists():
            self.skipTest("Canonical projector cache not present")
        mean_arr, w_arr, manifest = load_projector_cache(DEFAULT_CACHE_DIR)
        self.assertEqual(manifest["anchor_count"], 72)
        self.assertEqual(w_arr.shape, (384, 64))
        probe = np.ones(384, dtype=np.float64)
        out = project_384_to_64_cpu(probe, mean_arr, w_arr)
        self.assertEqual(out.shape, (64,))
        self.assertAlmostEqual(float(np.linalg.norm(out)), 1.0, places=9)

    def test_audit_content_hash_duplicates_read_only(self) -> None:
        vec = normalize_to_q2_30(_axis_vec(DEFAULT_VECTOR_DIM, 1.0, 0.0))
        recs = [
            GStarRecord("r1", 0, vec, content_hash="h_alpha"),
            GStarRecord("r2", 0, vec, content_hash="h_beta"),
            GStarRecord("r3", 0, vec, content_hash="h_alpha"),
            GStarRecord("r4", 0, vec, content_hash="h_alpha"),
        ]
        res = audit_content_hash_duplicates(recs)
        self.assertTrue(res["dry_run"])
        self.assertEqual(res["total_records"], 4)
        self.assertEqual(res["unique_hashes"], 2)
        self.assertEqual(res["duplicate_count"], 2)
        self.assertEqual(res["duplicate_ids"], ["r3", "r4"])
        self.assertEqual(len(recs), 4)

    def test_http_prompt_passthrough_and_epistemic_pause(self) -> None:
        svc = _StubHudService()
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_hud_handler(svc))
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{port}"
        try:
            ok_req = urllib.request.Request(
                f"{base}/api/prompt",
                data=json.dumps({"prompt": "coherent physics query"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(ok_req, timeout=5) as resp:
                body_ok = json.loads(resp.read().decode("utf-8"))
            self.assertFalse(body_ok["epistemic_pause"])
            self.assertEqual(svc.step_calls, 1)

            drift_vec = list(normalize_to_q2_30(_axis_vec(DEFAULT_VECTOR_DIM, 0.10, 0.0, 0.99)))
            pause_payload = {
                "prompt": "contradictory premise",
                "prompt_id": "http_drift_01",
                "vector_q30": drift_vec,
                "hbm_temp_c": 65.0,
            }
            pause_req = urllib.request.Request(
                f"{base}/api/prompt",
                data=json.dumps(pause_payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(pause_req, timeout=5) as resp:
                body_pause = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(body_pause["epistemic_pause"])
            self.assertFalse(body_pause["allow_llm_generation"])
            self.assertEqual(body_pause["handover_status"], "LOCKSTEP_DMR_VERIFIED")
            self.assertEqual(body_pause["active_bank"], "BANK_B")
            self.assertEqual(body_pause["quarantined_record_id"], "http_drift_01")
            self.assertEqual(svc.step_calls, 1)

            with urllib.request.urlopen(f"{base}/api/dolphin/status", timeout=5) as resp:
                st = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(st["epistemic_pause_metrics"]["passthrough_count"], 1)
            self.assertEqual(st["epistemic_pause_metrics"]["pause_count"], 1)
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
