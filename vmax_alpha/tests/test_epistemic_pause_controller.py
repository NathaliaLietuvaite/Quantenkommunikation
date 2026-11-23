#!/usr/bin/env python3
"""
vmax_alpha/tests/test_epistemic_pause_controller.py

Deterministic unit tests for V4.6-PAUSE Epistemic Pause Closed Control Loop.
OP02-AST-clean: 0 semicolons, 0 tabs, flat test methods.
"""

from __future__ import annotations

import unittest
from typing import List

try:
    from vmax_alpha.dolphin_memory_governor import (
        DEFAULT_VECTOR_DIM,
        DolphinMemoryGovernor,
        GStarRecord,
        normalize_to_q2_30,
    )
    from vmax_alpha.epistemic_pause_controller import (
        EpistemicPauseConfig,
        EpistemicPauseController,
        PromptGateInput,
    )
except ImportError:
    from dolphin_memory_governor import (
        DEFAULT_VECTOR_DIM,
        DolphinMemoryGovernor,
        GStarRecord,
        normalize_to_q2_30,
    )
    from epistemic_pause_controller import (
        EpistemicPauseConfig,
        EpistemicPauseController,
        PromptGateInput,
    )


def _axis_vec(dim: int, c0: float, c1: float, c2: float = 0.0) -> List[float]:
    """Build deterministic 64D unit-normalizable test vector."""
    vals = [0.0] * dim
    vals[0] = c0
    vals[1] = c1
    vals[2] = c2
    return vals


class TestEpistemicPauseController(unittest.TestCase):
    """Verify coherent pass-through and closed-loop Epistemic Pause triggers."""

    def setUp(self) -> None:
        little = normalize_to_q2_30(_axis_vec(DEFAULT_VECTOR_DIM, 1.0, 0.0))
        self.gov = DolphinMemoryGovernor(little)
        self.ctrl = EpistemicPauseController(self.gov, EpistemicPauseConfig())
        anchor_vec = normalize_to_q2_30(_axis_vec(DEFAULT_VECTOR_DIM, 0.90, 0.43))
        ok, _, _ = self.gov.admit_gstar(
            GStarRecord(
                record_id="anchor_tier2",
                epoch=1,
                vector_q30=anchor_vec,
                anchor_tier=2,
                content_hash="sealed_anchor_hash",
            )
        )
        self.assertTrue(ok)

    def test_coherent_prompt_passes_through_without_switch(self) -> None:
        """Coherent prompt allows LLM generation and leaves active bank unchanged."""
        vec = normalize_to_q2_30(_axis_vec(DEFAULT_VECTOR_DIM, 0.96, 0.28))
        decision = self.ctrl.evaluate_prompt(
            PromptGateInput(
                prompt_id="p_ok",
                vector_q30=vec,
                content_hash="h_ok",
                g3_torsion=0.05,
            )
        )
        self.assertFalse(decision.epistemic_pause)
        self.assertTrue(decision.allow_llm_generation)
        self.assertEqual(decision.reason, "COHERENT_PASSTHROUGH")
        self.assertEqual(decision.active_bank, "BANK_A")
        self.assertEqual(decision.handover_status, "NOT_REQUIRED")
        self.assertIsNone(decision.quarantined_record_id)
        self.assertEqual(self.ctrl.passthrough_count, 1)

    def test_low_rcf_drift_triggers_pause_quarantine_and_handover(self) -> None:
        """Drifted prompt triggers Epistemic Pause, T_I/O quarantine, and switch."""
        drift_vec = normalize_to_q2_30(_axis_vec(DEFAULT_VECTOR_DIM, 0.15, 0.0, 0.98))
        decision = self.ctrl.evaluate_prompt(
            PromptGateInput(
                prompt_id="p_drift",
                vector_q30=drift_vec,
                content_hash="h_drift",
                g3_torsion=0.10,
            )
        )
        self.assertTrue(decision.epistemic_pause)
        self.assertFalse(decision.allow_llm_generation)
        self.assertEqual(decision.reason, "ODOS_PROMPT_DRIFT_PAUSE")
        self.assertEqual(decision.handover_status, "LOCKSTEP_DMR_VERIFIED")
        self.assertEqual(decision.active_bank, "BANK_B")
        self.assertEqual(decision.quarantined_record_id, "p_drift")
        self.assertNotIn("p_drift", self.gov.bank_a.records)
        self.assertNotIn("p_drift", self.gov.bank_b.records)
        self.assertEqual(len(self.gov.bank_a.quarantine), 1)
        self.assertEqual(self.gov.bank_a.quarantine[0].record_id, "p_drift")

    def test_sealed_anchor_contradiction_triggers_pause(self) -> None:
        """Prompt opposing higher-tier sealed anchor triggers contradiction pause."""
        contra_vec = normalize_to_q2_30(_axis_vec(DEFAULT_VECTOR_DIM, -0.80, -0.60))
        decision = self.ctrl.evaluate_prompt(
            PromptGateInput(
                prompt_id="p_contra",
                vector_q30=contra_vec,
                content_hash="h_contra",
                g3_torsion=0.05,
            )
        )
        self.assertTrue(decision.epistemic_pause)
        self.assertFalse(decision.allow_llm_generation)
        self.assertEqual(decision.reason, "SEALED_ANCHOR_CONTRADICTION_PAUSE")
        self.assertEqual(decision.handover_status, "LOCKSTEP_DMR_VERIFIED")
        self.assertEqual(decision.active_bank, "BANK_B")

    def test_high_g3_torsion_triggers_pause_even_with_high_rcf(self) -> None:
        """Excessive G3 torsion triggers Epistemic Pause and atomic handover."""
        vec = normalize_to_q2_30(_axis_vec(DEFAULT_VECTOR_DIM, 0.99, 0.14))
        decision = self.ctrl.evaluate_prompt(
            PromptGateInput(
                prompt_id="p_torsion",
                vector_q30=vec,
                content_hash="h_torsion",
                g3_torsion=0.52,
            )
        )
        self.assertTrue(decision.epistemic_pause)
        self.assertFalse(decision.allow_llm_generation)
        self.assertEqual(decision.reason, "G3_TORSION_THRESHOLD_PAUSE")
        self.assertEqual(decision.handover_status, "LOCKSTEP_DMR_VERIFIED")
        payload = decision.to_dict()
        self.assertTrue(payload["epistemic_pause"])
        self.assertIn("fridu_message", payload)

    def test_dimension_mismatch_fails_closed(self) -> None:
        """Non-64D prompt vector fails closed into Epistemic Pause."""
        bad_vec = tuple([0] * 16)
        decision = self.ctrl.evaluate_prompt(
            PromptGateInput(
                prompt_id="p_dim",
                vector_q30=bad_vec,
                content_hash="h_dim",
            )
        )
        self.assertTrue(decision.epistemic_pause)
        self.assertEqual(decision.reason, "DIM_MISMATCH_PAUSE")
        self.assertEqual(decision.handover_status, "LOCKSTEP_DMR_VERIFIED")


if __name__ == "__main__":
    unittest.main()
