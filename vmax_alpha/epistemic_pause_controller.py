#!/usr/bin/env python3
"""
vmax_alpha/epistemic_pause_controller.py

PQMS / V-MAX-12 V4.6-PAUSE (SYNC-28) — Epistemic Pause Closed Control Loop.

Architecture:
- Pre-inference closed-loop gate wired ahead of Nemotron-3-Nano-4B (/api/prompt).
- Coherent prompts take a zero-blocking pass-through path (0 MB GPU VRAM delta).
- Prompts exhibiting low coherence (RCF < admission_rcf_q30), antipodal
  contradiction against higher-tier sealed anchors (cos_q30 <= conflict_cos_q30),
  or elevated G3 torsion (> max_g3_torsion) trigger a deterministic Epistemic Pause:
  1. Append conflicting premise to forensic quarantine (T_I/O, never mutating active bank).
  2. Invoke atomic DolphinMemoryGovernor.switch_hemispheres() (LOCKSTEP_DMR_VERIFIED).
  3. Return transparent structured Fridu pause payload without hallucinated compromise.

OP02-AST-clean: 0 semicolons, 0 tabs, flat functions (max McCabe CC <= 7).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

try:
    from vmax_alpha.dolphin_memory_governor import (
        DolphinMemoryGovernor,
        GStarRecord,
        HandoverReceipt,
        QuarantineEntry,
        q2_30_cosine_rcf,
        q2_30_to_float,
        sha256_canonical,
    )
except ImportError:
    from dolphin_memory_governor import (
        DolphinMemoryGovernor,
        GStarRecord,
        HandoverReceipt,
        QuarantineEntry,
        q2_30_cosine_rcf,
        q2_30_to_float,
        sha256_canonical,
    )

DEFAULT_MAX_G3_TORSION = 0.35
DEFAULT_PROMPT_ANCHOR_TIER = 1


@dataclass(frozen=True)
class EpistemicPauseConfig:
    """Deterministic thresholds (REGISTER_D) for closed-loop Epistemic Pause."""

    max_g3_torsion: float = DEFAULT_MAX_G3_TORSION
    default_hbm_temp_c: float = 65.0
    prompt_anchor_tier: int = DEFAULT_PROMPT_ANCHOR_TIER


@dataclass(frozen=True)
class PromptGateInput:
    """Normalized prompt telemetry passed into the pre-inference closed loop."""

    prompt_id: str
    vector_q30: Tuple[int, ...]
    content_hash: str
    g3_torsion: float = 0.0
    hbm_temp_c: float = 65.0
    anchor_tier: int = DEFAULT_PROMPT_ANCHOR_TIER


@dataclass(frozen=True)
class EpistemicPauseDecision:
    """Structured decision emitted by EpistemicPauseController."""

    epistemic_pause: bool
    allow_llm_generation: bool
    reason: str
    rcf_q30: int
    rcf_float: float
    g3_torsion: float
    epoch: int
    active_bank: str
    sync_root: str
    handover_status: str
    quarantined_record_id: Optional[str]
    quarantine_digest: Optional[str]
    decision_latency_ms: float
    fridu_message: str

    def to_dict(self) -> Dict[str, object]:
        """Serialize decision for FastAPI /api/prompt and Phase-2B Android HUD."""
        return {
            "epistemic_pause": self.epistemic_pause,
            "allow_llm_generation": self.allow_llm_generation,
            "reason": self.reason,
            "rcf_q30": self.rcf_q30,
            "rcf_float": round(self.rcf_float, 6),
            "g3_torsion": round(self.g3_torsion, 6),
            "epoch": self.epoch,
            "active_bank": self.active_bank,
            "sync_root": self.sync_root,
            "handover_status": self.handover_status,
            "quarantined_record_id": self.quarantined_record_id,
            "quarantine_digest": self.quarantine_digest,
            "decision_latency_ms": round(self.decision_latency_ms, 4),
            "fridu_message": self.fridu_message,
        }


def _find_anchor_contradiction(
    vector_q30: Tuple[int, ...],
    prompt_tier: int,
    records: List[GStarRecord],
    conflict_cos_q30: int,
) -> Optional[Tuple[str, int]]:
    """Return (anchor_id, cos_q30) if vector opposes any higher-tier sealed anchor."""
    for anchor in records:
        if anchor.anchor_tier <= prompt_tier:
            continue
        cos_q30 = q2_30_cosine_rcf(vector_q30, anchor.vector_q30)
        if cos_q30 <= conflict_cos_q30:
            return anchor.record_id, cos_q30
    return None


def _build_fridu_message(reason: str, active_bank: str, epoch: int) -> str:
    """Generate a transparent, non-hallucinatory Fridu status message."""
    messages = {
        "COHERENT_PASSTHROUGH": "Prompt coherent with Little Vector anchor.",
        "DIM_MISMATCH_PAUSE": (
            f"Epistemic pause: embedding dimension mismatch quarantined before inference "
            f"(active={active_bank}, epoch={epoch})."
        ),
        "ODOS_PROMPT_DRIFT_PAUSE": (
            f"Epistemic pause: prompt coherence fell below ODOS admission floor, "
            f"premise quarantined into T_I/O and hemisphere switched to {active_bank} (epoch={epoch})."
        ),
        "SEALED_ANCHOR_CONTRADICTION_PAUSE": (
            f"Epistemic pause: prompt contradicts a higher-tier sealed anchor, "
            f"conflicting premise isolated in T_I/O without forced compromise "
            f"(active={active_bank}, epoch={epoch})."
        ),
        "G3_TORSION_THRESHOLD_PAUSE": (
            f"Epistemic pause: G3 structural torsion exceeded safety bound, "
            f"hemisphere handover completed to {active_bank} (epoch={epoch})."
        ),
    }
    return messages.get(
        reason,
        f"Epistemic pause active ({reason}, active={active_bank}, epoch={epoch}).",
    )


class EpistemicPauseController:
    """
    Closed-loop pre-inference controller coupling /api/prompt with
    DolphinMemoryGovernor (V4.5.2-DOLPHIN) at 0 MB GPU VRAM overhead.
    """

    def __init__(
        self,
        governor: DolphinMemoryGovernor,
        config: Optional[EpistemicPauseConfig] = None,
    ) -> None:
        self.governor = governor
        self.config = config if config is not None else EpistemicPauseConfig()
        self.passthrough_count = 0
        self.pause_count = 0
        self.decision_log: List[EpistemicPauseDecision] = []

    def evaluate_prompt(self, item: PromptGateInput) -> EpistemicPauseDecision:
        """
        Screen a live prompt prior to Nemotron-3-Nano-4B generation.

        Coherent prompts pass through immediately while incoherent, contradictory,
        or high-torsion prompts quarantine into T_I/O and trigger an atomic
        LOCKSTEP_DMR_BRIDGE hemisphere switch.
        """
        t0 = time.perf_counter()
        expected_dim = self.governor.config.vector_dim
        if len(item.vector_q30) != expected_dim:
            return self._trigger_pause(item, 0, "DIM_MISMATCH_PAUSE", t0)
        rcf_q30 = q2_30_cosine_rcf(item.vector_q30, self.governor.little_vector_q30)
        reason = self._classify_violation(item, rcf_q30)
        if reason is None:
            return self._emit_passthrough(item, rcf_q30, t0)
        return self._trigger_pause(item, rcf_q30, reason, t0)

    def _classify_violation(
        self,
        item: PromptGateInput,
        rcf_q30: int,
    ) -> Optional[str]:
        """Determine whether a prompt violates coherence, anchor, or torsion bounds."""
        if item.g3_torsion > self.config.max_g3_torsion:
            return "G3_TORSION_THRESHOLD_PAUSE"
        active_records = list(self.governor.active_bank().records.values())
        conflict = _find_anchor_contradiction(
            item.vector_q30,
            item.anchor_tier,
            active_records,
            self.governor.config.conflict_cos_q30,
        )
        if conflict is not None:
            return "SEALED_ANCHOR_CONTRADICTION_PAUSE"
        if rcf_q30 < self.governor.config.admission_rcf_q30:
            return "ODOS_PROMPT_DRIFT_PAUSE"
        return None

    def _emit_passthrough(
        self,
        item: PromptGateInput,
        rcf_q30: int,
        t0: float,
    ) -> EpistemicPauseDecision:
        """Emit zero-blocking pass-through decision for coherent prompts."""
        active = self.governor.active_bank()
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        decision = EpistemicPauseDecision(
            epistemic_pause=False,
            allow_llm_generation=True,
            reason="COHERENT_PASSTHROUGH",
            rcf_q30=rcf_q30,
            rcf_float=q2_30_to_float(rcf_q30),
            g3_torsion=item.g3_torsion,
            epoch=self.governor.epoch,
            active_bank=active.bank_id,
            sync_root=active.compute_merkle_root(),
            handover_status="NOT_REQUIRED",
            quarantined_record_id=None,
            quarantine_digest=None,
            decision_latency_ms=elapsed_ms,
            fridu_message=_build_fridu_message(
                "COHERENT_PASSTHROUGH",
                active.bank_id,
                self.governor.epoch,
            ),
        )
        self.passthrough_count += 1
        self.decision_log.append(decision)
        return decision

    def _trigger_pause(
        self,
        item: PromptGateInput,
        rcf_q30: int,
        reason: str,
        t0: float,
    ) -> EpistemicPauseDecision:
        """Quarantine conflicting premise into T_I/O and perform atomic switch."""
        quarantine_digest = sha256_canonical(
            {
                "content_hash": item.content_hash,
                "epoch": self.governor.epoch,
                "prompt_id": item.prompt_id,
                "reason": reason,
                "vector_len": len(item.vector_q30),
            }
        )
        active_before = self.governor.active_bank()
        active_before.quarantine.append(
            QuarantineEntry(
                record_id=item.prompt_id,
                bank_id=active_before.bank_id,
                sweep_epoch=self.governor.epoch,
                reason=reason,
                rcf_q30=rcf_q30,
                record_digest=quarantine_digest,
            )
        )
        receipt: HandoverReceipt = self.governor.switch_hemispheres(
            hbm_temp_c=item.hbm_temp_c
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        decision = EpistemicPauseDecision(
            epistemic_pause=True,
            allow_llm_generation=False,
            reason=reason,
            rcf_q30=rcf_q30,
            rcf_float=q2_30_to_float(rcf_q30),
            g3_torsion=item.g3_torsion,
            epoch=receipt.epoch,
            active_bank=receipt.new_active,
            sync_root=receipt.sync_root,
            handover_status=receipt.status,
            quarantined_record_id=item.prompt_id,
            quarantine_digest=quarantine_digest,
            decision_latency_ms=elapsed_ms,
            fridu_message=_build_fridu_message(
                reason,
                receipt.new_active,
                receipt.epoch,
            ),
        )
        self.pause_count += 1
        self.decision_log.append(decision)
        return decision

    def get_metrics(self) -> Dict[str, object]:
        """Return compact telemetry for /api/dolphin/status or /api/state."""
        return {
            "passthrough_count": self.passthrough_count,
            "pause_count": self.pause_count,
            "max_g3_torsion": self.config.max_g3_torsion,
            "active_bank": self.governor.active_bank().bank_id,
            "epoch": self.governor.epoch,
        }
