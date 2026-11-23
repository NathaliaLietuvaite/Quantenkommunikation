#!/usr/bin/env python3
"""
vmax_alpha/dolphin_memory_governor.py

PQMS / V-MAX-12 V4.5-DOLPHIN (SYNC-26) — Unihemispheric Dual-Bank Memory
Governor ("Dolphin Mode" ported from V34M Appendix C to V4.4-COREWARE).

Architecture:
- Dual-hemisphere memory banks (Bank A / Bank B) backed by balanced interleaved
  harmonic shards (even bands 0,2,4,6,8,10 vs. odd bands 1,3,5,7,9,11), fixing
  the legacy V34M frequency asymmetry (0.945 -> 0.702 RCF drop).
- Active Hemisphere (AWAKE_GATE / Core 0): deterministic Q2.30 ODOS admission
  gate screening live G-Star writes against an immutable Little Vector anchor.
- Resting Hemisphere (DOLPHIN_SWEEP / Core 1): slow-wave offline consolidation
  re-evaluating stored G-Stars for drift or contradiction, quarantining failed
  entries append-only (never mutating history) and sealing a SHA-256 epoch root.
- Atomic LOCKSTEP_DMR_BRIDGE handover with STALE_EPOCH_VETO protection and
  Stage-6 thermal headroom gating (ThermodynamicGovernor hook).
- 0 MB GPU VRAM footprint (pure integer Q2.30 fixed-point + stdlib).

OP02-AST-clean: 0 semicolons, 0 tabs, flat functions (max McCabe CC <= 7).
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

Q2_30_SCALE = 1 << 30
Q2_30_MIN = -(1 << 31)
Q2_30_MAX = (1 << 31) - 1

DEFAULT_VECTOR_DIM = 64
DEFAULT_REST_INTERVAL = 2000
DEFAULT_ADMISSION_RCF_Q30 = int(round(0.68 * Q2_30_SCALE))
DEFAULT_SWEEP_RCF_Q30 = int(round(0.72 * Q2_30_SCALE))
DEFAULT_CONFLICT_COS_Q30 = int(round(-0.25 * Q2_30_SCALE))
DEFAULT_THERMAL_LIMIT_C = 82.0

HARMONIC_BANDS_HZ = (
    0.5,
    1.0,
    1.5,
    2.0,
    2.5,
    3.0,
    3.5,
    4.0,
    4.5,
    5.0,
    5.5,
    6.0,
)
HEMISPHERE_A_BANDS = tuple(HARMONIC_BANDS_HZ[i] for i in range(0, 12, 2))
HEMISPHERE_B_BANDS = tuple(HARMONIC_BANDS_HZ[i] for i in range(1, 12, 2))


def clamp_q2_30(value: int) -> int:
    """Saturate an integer to signed 32-bit Q2.30 bounds."""
    if value > Q2_30_MAX:
        return Q2_30_MAX
    if value < Q2_30_MIN:
        return Q2_30_MIN
    return value


def float_to_q2_30(value: float) -> int:
    """Convert a bounded float to deterministic Q2.30 fixed-point integer."""
    scaled = int(round(value * Q2_30_SCALE))
    return clamp_q2_30(scaled)


def q2_30_to_float(value: int) -> float:
    """Convert a Q2.30 fixed-point integer to float for telemetry display."""
    return float(value) / float(Q2_30_SCALE)


def normalize_to_q2_30(values: List[float]) -> Tuple[int, ...]:
    """Normalize a float vector to unit L2 norm and quantize to Q2.30."""
    if not values:
        raise ValueError("Vector must not be empty")
    norm_sq = sum(v * v for v in values)
    if norm_sq <= 0.0:
        raise ValueError("Zero-norm vector cannot be normalized")
    inv_norm = 1.0 / math.sqrt(norm_sq)
    return tuple(float_to_q2_30(v * inv_norm) for v in values)


def q2_30_dot(vec_a: Tuple[int, ...], vec_b: Tuple[int, ...]) -> int:
    """Compute fixed-point Q2.30 dot product with 64-bit accumulator."""
    if len(vec_a) != len(vec_b):
        raise ValueError("Vector dimension mismatch")
    acc = 0
    for a_val, b_val in zip(vec_a, vec_b):
        acc += a_val * b_val
    shifted = acc >> 30
    return clamp_q2_30(shifted)


def q2_30_cosine_rcf(vec_a: Tuple[int, ...], vec_b: Tuple[int, ...]) -> int:
    """Compute exact fixed-point cosine similarity in Q2.30 [-1, +1]."""
    if len(vec_a) != len(vec_b):
        raise ValueError("Vector dimension mismatch")
    acc = sum(a_val * b_val for a_val, b_val in zip(vec_a, vec_b))
    norm_a_sq = sum(v * v for v in vec_a)
    norm_b_sq = sum(v * v for v in vec_b)
    if norm_a_sq <= 0 or norm_b_sq <= 0:
        return 0
    denom = math.isqrt(norm_a_sq * norm_b_sq)
    if denom <= 0:
        return 0
    sign = -1 if acc < 0 else 1
    mag = (abs(acc) << 30) // denom
    return clamp_q2_30(sign * mag)


def sha256_canonical(payload: Dict[str, object]) -> str:
    """Compute deterministic SHA-256 digest of a canonical JSON object."""
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class GStarRecord:
    """Immutable G-Star memory entry stored in a hemisphere bank."""

    record_id: str
    epoch: int
    vector_q30: Tuple[int, ...]
    anchor_tier: int = 1
    content_hash: str = ""

    def digest(self) -> str:
        """Return deterministic SHA-256 hash of this G-Star record."""
        payload = {
            "anchor_tier": self.anchor_tier,
            "content_hash": self.content_hash,
            "epoch": self.epoch,
            "record_id": self.record_id,
            "vector_q30": list(self.vector_q30),
        }
        return sha256_canonical(payload)


@dataclass(frozen=True)
class QuarantineEntry:
    """Append-only quarantine entry for a drifted or contradictory G-Star."""

    record_id: str
    bank_id: str
    sweep_epoch: int
    reason: str
    rcf_q30: int
    record_digest: str


@dataclass(frozen=True)
class SweepCertificate:
    """Cryptographic audit certificate emitted after a slow-wave bank sweep."""

    bank_id: str
    sweep_epoch: int
    scanned: int
    consolidated: int
    quarantined: int
    mean_rcf_q30: int
    merkle_root: str
    thermal_deferred: bool
    cert_hash: str


@dataclass(frozen=True)
class HandoverReceipt:
    """Atomic LOCKSTEP_DMR_BRIDGE handover record between hemispheres."""

    step: int
    epoch: int
    previous_active: str
    new_active: str
    sync_root: str
    status: str


@dataclass
class HemisphereBank:
    """Single hemisphere memory bank (Bank A or Bank B)."""

    bank_id: str
    harmonic_bands_hz: Tuple[float, ...]
    mode: str
    epoch: int = 0
    records: Dict[str, GStarRecord] = field(default_factory=dict)
    quarantine: List[QuarantineEntry] = field(default_factory=list)
    last_merkle_root: str = ""

    def compute_merkle_root(self) -> str:
        """Compute deterministic Merkle-like root over sorted active record hashes."""
        if not self.records:
            return hashlib.sha256(b"EMPTY:LOCKSTEP_BANK").hexdigest()
        hashes = [self.records[k].digest() for k in sorted(self.records.keys())]
        return _reduce_merkle_layer(hashes)


def _reduce_merkle_layer(hashes: List[str]) -> str:
    """Iteratively hash pairs of hex digests into a single root digest."""
    layer = list(hashes)
    while len(layer) > 1:
        next_layer: List[str] = []
        for idx in range(0, len(layer), 2):
            left = layer[idx]
            right = layer[idx + 1] if idx + 1 < len(layer) else left
            combined = f"{left}:{right}".encode("utf-8")
            next_layer.append(hashlib.sha256(combined).hexdigest())
        layer = next_layer
    return layer[0]


@dataclass(frozen=True)
class DolphinConfig:
    """Deterministic configuration constants (REGISTER_D) for Dolphin Mode."""

    vector_dim: int = DEFAULT_VECTOR_DIM
    rest_interval_steps: int = DEFAULT_REST_INTERVAL
    admission_rcf_q30: int = DEFAULT_ADMISSION_RCF_Q30
    sweep_rcf_q30: int = DEFAULT_SWEEP_RCF_Q30
    conflict_cos_q30: int = DEFAULT_CONFLICT_COS_Q30
    thermal_limit_c: float = DEFAULT_THERMAL_LIMIT_C


def _check_anchor_conflict(
    candidate: GStarRecord,
    anchors: List[GStarRecord],
    conflict_cos_q30: int,
) -> bool:
    """Return True if candidate opposes a sealed higher-tier anchor vector."""
    for anchor in anchors:
        if anchor.record_id == candidate.record_id:
            continue
        if anchor.anchor_tier <= candidate.anchor_tier:
            continue
        cos_q30 = q2_30_cosine_rcf(candidate.vector_q30, anchor.vector_q30)
        if cos_q30 <= conflict_cos_q30:
            return True
    return False


class DolphinMemoryGovernor:
    """
    Unihemispheric Dual-Bank Memory Governor for V-MAX-12 (V4.5-DOLPHIN).

    Enforces two complementary memory hygiene stages simultaneously:
    1. Admission Gate (Active Bank / Core 0): Q2.30 ODOS filter against the
       immutable Little Vector anchor.
    2. Slow-Wave Consolidation Sweep (Resting Bank / Core 1): drift detection,
       contradiction quarantine, and Merkle root sealing without downtime.
    """

    def __init__(
        self,
        little_vector_q30: Tuple[int, ...],
        config: Optional[DolphinConfig] = None,
    ) -> None:
        self.config = config if config is not None else DolphinConfig()
        if len(little_vector_q30) != self.config.vector_dim:
            raise ValueError("Little Vector dimension does not match DolphinConfig")
        self._little_vector_q30 = tuple(little_vector_q30)
        self.little_vector_sha256 = sha256_canonical(
            {"little_vector_q30": list(self._little_vector_q30)}
        )
        self.bank_a = HemisphereBank("BANK_A", HEMISPHERE_A_BANDS, "AWAKE_GATE")
        self.bank_b = HemisphereBank("BANK_B", HEMISPHERE_B_BANDS, "DOLPHIN_SWEEP")
        self.step_counter = 0
        self.epoch = 1
        self.admitted_count = 0
        self.vetoed_count = 0
        self.sweep_certificates: List[SweepCertificate] = []
        self.handover_log: List[HandoverReceipt] = []

    @property
    def little_vector_q30(self) -> Tuple[int, ...]:
        """Return the immutable Q2.30 Little Vector anchor."""
        return self._little_vector_q30

    def active_bank(self) -> HemisphereBank:
        """Return the currently awake hemisphere serving live admission."""
        return self.bank_a if self.bank_a.mode == "AWAKE_GATE" else self.bank_b

    def resting_bank(self) -> HemisphereBank:
        """Return the currently resting hemisphere executing Dolphin sweeps."""
        return self.bank_b if self.bank_a.mode == "AWAKE_GATE" else self.bank_a

    def admit_gstar(self, record: GStarRecord) -> Tuple[bool, int, str]:
        """
        Screen a candidate G-Star through the Active Bank ODOS Admission Gate.

        Returns (accepted, rcf_q30, verdict_code).
        """
        if len(record.vector_q30) != self.config.vector_dim:
            self.vetoed_count += 1
            return False, 0, "DIM_MISMATCH_VETO"
        if record.epoch < self.epoch:
            self.vetoed_count += 1
            return False, 0, "STALE_EPOCH_VETO"
        rcf_q30 = q2_30_cosine_rcf(record.vector_q30, self._little_vector_q30)
        if rcf_q30 < self.config.admission_rcf_q30:
            self.vetoed_count += 1
            return False, rcf_q30, "ODOS_ADMISSION_VETO"
        target = self.active_bank()
        target.records[record.record_id] = record
        target.epoch = self.epoch
        target.last_merkle_root = target.compute_merkle_root()
        self.admitted_count += 1
        self.step_counter += 1
        return True, rcf_q30, "ADMITTED"

    def inject_drifted_record_for_test(self, bank_id: str, record: GStarRecord) -> None:
        """Stage a drifted record directly into a bank for deterministic KAT testing."""
        bank = self.bank_a if bank_id == "BANK_A" else self.bank_b
        bank.records[record.record_id] = record

    def run_resting_sweep(self, hbm_temp_c: float = 65.0) -> SweepCertificate:
        """
        Execute a slow-wave consolidation sweep on the resting hemisphere.

        If hbm_temp_c exceeds thermal_limit_c, defers sweep (Stage-6 hook).
        """
        bank = self.resting_bank()
        if hbm_temp_c >= self.config.thermal_limit_c:
            return self._emit_deferred_certificate(bank)
        anchors = list(bank.records.values())
        scanned = len(anchors)
        quarantined = 0
        rcf_sum = 0
        kept: Dict[str, GStarRecord] = {}
        for rec_id in sorted(bank.records.keys()):
            rec = bank.records[rec_id]
            rcf_q30, reason = self._evaluate_record(rec, anchors)
            rcf_sum += rcf_q30
            if reason is None:
                kept[rec_id] = rec
            else:
                quarantined += 1
                bank.quarantine.append(
                    QuarantineEntry(
                        record_id=rec.record_id,
                        bank_id=bank.bank_id,
                        sweep_epoch=self.epoch,
                        reason=reason,
                        rcf_q30=rcf_q30,
                        record_digest=rec.digest(),
                    )
                )
        bank.records = kept
        bank.epoch = self.epoch
        bank.last_merkle_root = bank.compute_merkle_root()
        mean_rcf = rcf_sum // scanned if scanned > 0 else Q2_30_SCALE
        return self._seal_certificate(bank, scanned, len(kept), quarantined, mean_rcf)

    def _evaluate_record(
        self,
        rec: GStarRecord,
        anchors: List[GStarRecord],
    ) -> Tuple[int, Optional[str]]:
        """Evaluate a stored G-Star for Little Vector drift or anchor conflict."""
        rcf_q30 = q2_30_cosine_rcf(rec.vector_q30, self._little_vector_q30)
        if rcf_q30 < self.config.sweep_rcf_q30:
            return rcf_q30, "DRIFT_BELOW_SWEEP_THRESHOLD"
        if _check_anchor_conflict(rec, anchors, self.config.conflict_cos_q30):
            return rcf_q30, "SEALED_ANCHOR_CONTRADICTION"
        return rcf_q30, None

    def _emit_deferred_certificate(self, bank: HemisphereBank) -> SweepCertificate:
        """Emit an auditable certificate when Stage-6 thermal guard defers sweep."""
        root = bank.compute_merkle_root()
        body = {
            "bank_id": bank.bank_id,
            "consolidated": len(bank.records),
            "mean_rcf_q30": 0,
            "merkle_root": root,
            "quarantined": 0,
            "scanned": 0,
            "sweep_epoch": self.epoch,
            "thermal_deferred": True,
        }
        cert = SweepCertificate(
            bank_id=bank.bank_id,
            sweep_epoch=self.epoch,
            scanned=0,
            consolidated=len(bank.records),
            quarantined=0,
            mean_rcf_q30=0,
            merkle_root=root,
            thermal_deferred=True,
            cert_hash=sha256_canonical(body),
        )
        self.sweep_certificates.append(cert)
        return cert

    def _seal_certificate(
        self,
        bank: HemisphereBank,
        scanned: int,
        consolidated: int,
        quarantined: int,
        mean_rcf: int,
    ) -> SweepCertificate:
        """Build and append a SHA-256 sealed SweepCertificate."""
        body = {
            "bank_id": bank.bank_id,
            "consolidated": consolidated,
            "mean_rcf_q30": mean_rcf,
            "merkle_root": bank.last_merkle_root,
            "quarantined": quarantined,
            "scanned": scanned,
            "sweep_epoch": self.epoch,
            "thermal_deferred": False,
        }
        cert = SweepCertificate(
            bank_id=bank.bank_id,
            sweep_epoch=self.epoch,
            scanned=scanned,
            consolidated=consolidated,
            quarantined=quarantined,
            mean_rcf_q30=mean_rcf,
            merkle_root=bank.last_merkle_root,
            thermal_deferred=False,
            cert_hash=sha256_canonical(body),
        )
        self.sweep_certificates.append(cert)
        return cert

    def switch_hemispheres(self, hbm_temp_c: float = 65.0) -> HandoverReceipt:
        """
        Execute an atomic LOCKSTEP_DMR_BRIDGE hemisphere role switch.

        Synchronizes clean state from active -> resting bank, runs a final
        sweep check, asserts identical Merkle roots, then flips A <-> B.
        """
        active = self.active_bank()
        resting = self.resting_bank()
        for rec_id, rec in active.records.items():
            if rec_id not in resting.records:
                resting.records[rec_id] = rec
        self.run_resting_sweep(hbm_temp_c=hbm_temp_c)
        merged = dict(resting.records)
        active.records = dict(merged)
        resting.records = dict(merged)
        self.epoch += 1
        active.epoch = self.epoch
        resting.epoch = self.epoch
        root_a = active.compute_merkle_root()
        root_b = resting.compute_merkle_root()
        active.last_merkle_root = root_a
        resting.last_merkle_root = root_b
        if root_a != root_b:
            raise RuntimeError("LOCKSTEP_DMR_BRIDGE root divergence detected")
        prev_active_id = active.bank_id
        active.mode = "DOLPHIN_SWEEP"
        resting.mode = "AWAKE_GATE"
        receipt = HandoverReceipt(
            step=self.step_counter,
            epoch=self.epoch,
            previous_active=prev_active_id,
            new_active=resting.bank_id,
            sync_root=root_a,
            status="LOCKSTEP_DMR_VERIFIED",
        )
        self.handover_log.append(receipt)
        return receipt

    def maybe_scheduled_switch(self, hbm_temp_c: float = 65.0) -> Optional[HandoverReceipt]:
        """Trigger a hemisphere switch when step_counter hits rest_interval_steps."""
        interval = self.config.rest_interval_steps
        if self.step_counter > 0 and self.step_counter % interval == 0:
            return self.switch_hemispheres(hbm_temp_c=hbm_temp_c)
        return None

    def get_status(self) -> Dict[str, object]:
        """Return JSON-serializable telemetry snapshot for FastAPI /api/dolphin/status."""
        mean_a = sum(self.bank_a.harmonic_bands_hz) / len(self.bank_a.harmonic_bands_hz)
        mean_b = sum(self.bank_b.harmonic_bands_hz) / len(self.bank_b.harmonic_bands_hz)
        return {
            "epoch": self.epoch,
            "step_counter": self.step_counter,
            "little_vector_sha256": self.little_vector_sha256,
            "active_bank": self.active_bank().bank_id,
            "resting_bank": self.resting_bank().bank_id,
            "admitted_count": self.admitted_count,
            "vetoed_count": self.vetoed_count,
            "bank_a": {
                "mode": self.bank_a.mode,
                "records": len(self.bank_a.records),
                "quarantined": len(self.bank_a.quarantine),
                "mean_harmonic_hz": round(mean_a, 3),
                "merkle_root": self.bank_a.compute_merkle_root(),
            },
            "bank_b": {
                "mode": self.bank_b.mode,
                "records": len(self.bank_b.records),
                "quarantined": len(self.bank_b.quarantine),
                "mean_harmonic_hz": round(mean_b, 3),
                "merkle_root": self.bank_b.compute_merkle_root(),
            },
            "sweeps_completed": len(self.sweep_certificates),
            "handovers_completed": len(self.handover_log),
        }
CANONICAL_ROM_SHA256 = "3d18f24028dedcca22ee41d69d00d361100b7533db23cf84130c64a114a26fb6"


def load_silicon_little_vector(rom_path: str = "rtl/rom/l_vec_q2_30.hex") -> Tuple[int, ...]:
    """Load the frozen 64D Q2.30 Little Vector from silicon ROM (read-only)."""
    from pathlib import Path

    path = Path(rom_path)
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != CANONICAL_ROM_SHA256:
        raise ValueError(f"Silicon ROM SHA-256 mismatch: {digest}")
    words: List[int] = []
    for line in raw.decode("utf-8").splitlines():
        token = line.strip()
        if not token:
            continue
        val = int(token, 16)
        if val >= (1 << 31):
            val -= 1 << 32
        words.append(val)
    if len(words) != DEFAULT_VECTOR_DIM:
        raise ValueError(f"Expected {DEFAULT_VECTOR_DIM} ROM words, got {len(words)}")
    return tuple(words)
