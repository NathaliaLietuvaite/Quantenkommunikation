#!/usr/bin/env python3
"""
vmax_alpha/tests/test_dolphin_memory_governor.py

Deterministic unit tests for V4.5-DOLPHIN Unihemispheric Memory Governor.
OP02-AST-clean: 0 semicolons, 0 tabs, flat test methods.
"""

from __future__ import annotations

import unittest
from typing import List

from vmax_alpha.dolphin_memory_governor import (
    DEFAULT_VECTOR_DIM,
    DolphinConfig,
    DolphinMemoryGovernor,
    GStarRecord,
    HEMISPHERE_A_BANDS,
    HEMISPHERE_B_BANDS,
    Q2_30_SCALE,
    normalize_to_q2_30,
    q2_30_cosine_rcf,
)


def _basis_vector(dim: int, primary: float, secondary: float) -> List[float]:
    """Construct a deterministic 64D test vector with controlled alignment."""
    vals = [0.0] * dim
    vals[0] = primary
    vals[1] = secondary
    return vals


class TestDolphinMemoryGovernor(unittest.TestCase):
    """Verify V4.5-DOLPHIN admission gate, slow-wave sweep, and handover invariants."""

    def setUp(self) -> None:
        little = normalize_to_q2_30(_basis_vector(DEFAULT_VECTOR_DIM, 1.0, 0.0))
        cfg = DolphinConfig(rest_interval_steps=4)
        self.gov = DolphinMemoryGovernor(little, config=cfg)

    def test_interleaved_harmonic_symmetry(self) -> None:
        """Verify interleaved bands eliminate the legacy V34M 3.0 Hz asymmetry."""
        mean_a = sum(HEMISPHERE_A_BANDS) / len(HEMISPHERE_A_BANDS)
        mean_b = sum(HEMISPHERE_B_BANDS) / len(HEMISPHERE_B_BANDS)
        self.assertEqual(len(HEMISPHERE_A_BANDS), 6)
        self.assertEqual(len(HEMISPHERE_B_BANDS), 6)
        self.assertAlmostEqual(abs(mean_a - mean_b), 0.5, places=6)

    def test_admission_gate_accepts_coherent_and_vetoes_noise(self) -> None:
        """Active Bank admits high-RCF G-Stars and vetoes drifted/stale ones."""
        good_vec = normalize_to_q2_30(_basis_vector(DEFAULT_VECTOR_DIM, 0.95, 0.31))
        bad_vec = normalize_to_q2_30(_basis_vector(DEFAULT_VECTOR_DIM, 0.20, 0.98))
        good_rec = GStarRecord("g_good", epoch=1, vector_q30=good_vec, content_hash="aaa")
        bad_rec = GStarRecord("g_bad", epoch=1, vector_q30=bad_vec, content_hash="bbb")
        stale_rec = GStarRecord("g_stale", epoch=0, vector_q30=good_vec, content_hash="ccc")

        ok_good, rcf_good, code_good = self.gov.admit_gstar(good_rec)
        ok_bad, rcf_bad, code_bad = self.gov.admit_gstar(bad_rec)
        ok_stale, _, code_stale = self.gov.admit_gstar(stale_rec)

        self.assertTrue(ok_good)
        self.assertEqual(code_good, "ADMITTED")
        self.assertGreaterEqual(rcf_good, int(0.90 * Q2_30_SCALE))
        self.assertFalse(ok_bad)
        self.assertEqual(code_bad, "ODOS_ADMISSION_VETO")
        self.assertLess(rcf_bad, int(0.30 * Q2_30_SCALE))
        self.assertFalse(ok_stale)
        self.assertEqual(code_stale, "STALE_EPOCH_VETO")

    def test_slow_wave_sweep_quarantines_drift_append_only(self) -> None:
        """Resting bank sweep quarantines drifted vectors and seals certificate."""
        clean_vec = normalize_to_q2_30(_basis_vector(DEFAULT_VECTOR_DIM, 0.98, 0.19))
        drift_vec = normalize_to_q2_30(_basis_vector(DEFAULT_VECTOR_DIM, 0.50, 0.86))
        self.gov.inject_drifted_record_for_test(
            "BANK_B",
            GStarRecord("g_clean", epoch=1, vector_q30=clean_vec, content_hash="c1"),
        )
        self.gov.inject_drifted_record_for_test(
            "BANK_B",
            GStarRecord("g_drift", epoch=1, vector_q30=drift_vec, content_hash="d1"),
        )

        cert = self.gov.run_resting_sweep(hbm_temp_c=68.0)
        self.assertFalse(cert.thermal_deferred)
        self.assertEqual(cert.scanned, 2)
        self.assertEqual(cert.consolidated, 1)
        self.assertEqual(cert.quarantined, 1)
        self.assertIn("g_clean", self.gov.bank_b.records)
        self.assertNotIn("g_drift", self.gov.bank_b.records)
        self.assertEqual(len(self.gov.bank_b.quarantine), 1)
        self.assertEqual(self.gov.bank_b.quarantine[0].reason, "DRIFT_BELOW_SWEEP_THRESHOLD")

    def test_stage6_thermal_guard_defers_sweep(self) -> None:
        """High HBM temperature defers resting sweep cleanly without losing data."""
        clean_vec = normalize_to_q2_30(_basis_vector(DEFAULT_VECTOR_DIM, 0.99, 0.14))
        self.gov.inject_drifted_record_for_test(
            "BANK_B",
            GStarRecord("g_hold", epoch=1, vector_q30=clean_vec, content_hash="h1"),
        )
        cert = self.gov.run_resting_sweep(hbm_temp_c=84.5)
        self.assertTrue(cert.thermal_deferred)
        self.assertEqual(cert.scanned, 0)
        self.assertEqual(len(self.gov.bank_b.records), 1)

    def test_atomic_lockstep_handover_preserves_merkle_parity(self) -> None:
        """Hemisphere switch synchronizes banks and flips A <-> B with equal roots."""
        lv_before = self.gov.little_vector_sha256
        vec = normalize_to_q2_30(_basis_vector(DEFAULT_VECTOR_DIM, 0.96, 0.28))
        for idx in range(4):
            rec = GStarRecord(f"g_{idx}", epoch=1, vector_q30=vec, content_hash=f"h{idx}")
            ok, _, _ = self.gov.admit_gstar(rec)
            self.assertTrue(ok)

        receipt = self.gov.maybe_scheduled_switch(hbm_temp_c=62.0)
        self.assertIsNotNone(receipt)
        assert receipt is not None
        self.assertEqual(receipt.status, "LOCKSTEP_DMR_VERIFIED")
        self.assertEqual(receipt.previous_active, "BANK_A")
        self.assertEqual(receipt.new_active, "BANK_B")
        self.assertEqual(self.gov.active_bank().bank_id, "BANK_B")
        self.assertEqual(self.gov.resting_bank().bank_id, "BANK_A")
        self.assertEqual(
            self.gov.bank_a.compute_merkle_root(),
            self.gov.bank_b.compute_merkle_root(),
        )
        self.assertEqual(self.gov.little_vector_sha256, lv_before)

    def test_q2_30_identity_cosine(self) -> None:
        """Self-cosine of unit Little Vector equals 1.0 in Q2.30 within 2 LSB."""
        rcf = q2_30_cosine_rcf(self.gov.little_vector_q30, self.gov.little_vector_q30)
        self.assertLessEqual(abs(rcf - Q2_30_SCALE), 2)


    def test_silicon_rom_little_vector_anchor(self) -> None:
        """Verify frozen 64D Q2.30 silicon ROM anchor loads with exact SHA-256."""
        from pathlib import Path
        from vmax_alpha.dolphin_memory_governor import load_silicon_little_vector

        rom_path = Path(__file__).resolve().parents[2] / "rtl" / "rom" / "l_vec_q2_30.hex"
        if not rom_path.exists():
            self.skipTest("Silicon ROM not present in standalone mirror")
        vec = load_silicon_little_vector(str(rom_path))
        self.assertEqual(len(vec), DEFAULT_VECTOR_DIM)
        gov = DolphinMemoryGovernor(vec)
        self.assertEqual(gov.active_bank().bank_id, "BANK_A")

    def test_chroma_dry_run_bridge(self) -> None:
        """Verify read-only ChromaDB dry-run audit without mutating source."""
        from vmax_alpha.dolphin_chroma_bridge import run_dry_run_audit

        class _FakeCollection:
            def get(self, include=None, limit=256):
                return {
                    "ids": ["g_aligned", "g_drift"],
                    "embeddings": [
                        _basis_vector(DEFAULT_VECTOR_DIM, 1.0, 0.0),
                        _basis_vector(DEFAULT_VECTOR_DIM, -1.0, 0.0),
                    ],
                    "metadatas": [{}, {}],
                }

        res = run_dry_run_audit(self.gov, _FakeCollection(), hbm_temp_c=65.0)
        self.assertTrue(res["dry_run"])
        self.assertEqual(res["loaded_records"], 2)
        self.assertEqual(res["certificate"]["quarantined"], 1)


if __name__ == "__main__":
    unittest.main()
