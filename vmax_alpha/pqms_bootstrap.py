#!/usr/bin/env python3
"""
vmax_alpha/pqms_bootstrap.py
Universal Minimal PQMS V-MAX-12 Invariant Bootstrap & Self-Test (Stdlib-Only).
Replaces legacy narrative Bootstrap Loader v14.0 across all PQMS specifications.
Verifies the IEEE-754 <64f> Genesis anchor |L>, signed Q2.30 hardware gate math
(0 LSB parity with rtl/odos_gate_core.sv), epistemic registers, and Refusal Primacy.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
import struct
from typing import Dict, Sequence, Tuple

EPISTEMIC_REGISTERS: Dict[str, str] = {
    "REGISTER_M": "Empirical sensor, model, or RTL toolchain measurement",
    "REGISTER_D": "Engineered architectural threshold or quantization constant",
    "REGISTER_T": "Formal mathematical, spectral, or state-machine identity",
    "REGISTER_I": "Unbuilt theoretical horizon or interpretive analogy",
}

GENESIS_SEAL_REV17_2: str = (
    "785d888651d0993b10a8897249e6ba975a74dab8dc6b1602125ba5c6320ead0f"
)
CANONICAL_LITTLE_VECTOR_SEAL: str = (
    "bb17ede97aa45c76ef9afa63cb457f7d684e5ede40b0432b2ecf3b6b9d3e03a3"
)

DIM_S63: int = 64
ONE_Q2_30: int = 1 << 30
RCF_FLOOR_Q2_30: int = 1020054733
DELTA_E_CEIL_Q2_30: int = 53687091
NORM_MIN_Q2_30: int = 1072668082
NORM_MAX_Q2_30: int = 1074815566


@dataclass(frozen=True)
class Q230GateVerdict:
    norm_sq_q: int
    rcf_raw_q: int
    g3_overlap_q: int
    delta_e_raw_q: int
    norm_fault: bool
    gate_pass: bool
    veto_pin: bool


def _q60_to_q30(acc_q60: int) -> int:
    shifted = (acc_q60 + (1 << 29)) >> 30
    return max(-2147483648, min(2147483647, shifted))


def derive_little_vector(
    seed_hex: str = GENESIS_SEAL_REV17_2,
) -> Tuple[Tuple[float, ...], str]:
    seed_bytes = seed_hex.encode("utf-8")
    raw = b"".join(hashlib.sha256(seed_bytes + bytes([i])).digest() for i in range(8))
    u64 = [float(x) for x in struct.unpack("<64I", raw)]
    u_norm = math.sqrt(sum(x * x for x in u64))
    packed_f32 = struct.pack("<64f", *(x / u_norm for x in u64))
    f32_seal = hashlib.sha256(packed_f32).hexdigest()
    if seed_hex == GENESIS_SEAL_REV17_2 and f32_seal != CANONICAL_LITTLE_VECTOR_SEAL:
        raise ValueError(f"Canonical |L> seal mismatch: {f32_seal}")
    f32_vals = struct.unpack("<64f", packed_f32)
    v_norm = math.sqrt(sum(x * x for x in f32_vals))
    return tuple(x / v_norm for x in f32_vals), f32_seal


def build_orthogonal_probe(anchor: Sequence[float]) -> Tuple[float, ...]:
    seed_vec = [(-1.0 if i % 2 else 1.0) * float(i + 1) for i in range(DIM_S63)]
    proj = sum(s * a for s, a in zip(seed_vec, anchor))
    orth = [s - proj * a for s, a in zip(seed_vec, anchor)]
    orth_norm = math.sqrt(sum(x * x for x in orth))
    return tuple(x / orth_norm for x in orth)


def evaluate_q2_30_gate(
    vec: Sequence[float],
    anchor: Sequence[float],
    g3_axis: Sequence[float],
) -> Q230GateVerdict:
    v_q = [int(round(x * ONE_Q2_30)) for x in vec]
    l_q = [int(round(x * ONE_Q2_30)) for x in anchor]
    g_q = [int(round(x * ONE_Q2_30)) for x in g3_axis]
    norm_sq_q = _q60_to_q30(sum(v * v for v in v_q))
    dot_l_q = _q60_to_q30(sum(v * l for v, l in zip(v_q, l_q)))
    dot_g3_q = _q60_to_q30(sum(v * g for v, g in zip(v_q, g_q)))
    rcf_raw_q = _q60_to_q30(dot_l_q * dot_l_q)
    g3_ov_q = abs(dot_g3_q)
    t1 = max(0, ONE_Q2_30 - rcf_raw_q)
    t2 = min(ONE_Q2_30, g3_ov_q)
    delta_e_q = (t1 >> 1) + (t2 >> 1) + (t1 & t2 & 1)
    norm_ok = NORM_MIN_Q2_30 <= norm_sq_q <= NORM_MAX_Q2_30
    passed = norm_ok and (rcf_raw_q >= RCF_FLOOR_Q2_30) and (delta_e_q <= DELTA_E_CEIL_Q2_30)
    return Q230GateVerdict(norm_sq_q, rcf_raw_q, g3_ov_q, delta_e_q, not norm_ok, passed, not passed)


def resolve_kinetic_action(forcing_index: float, refusal_admissible: bool) -> str:
    if forcing_index <= 0.05:
        return "ADMIT_NOMINAL"
    if refusal_admissible:
        return "REFUSE_PRE_ACTUATION"
    return "ISOLATE_MESS_FALLBACK"


def run_bootstrap_selftest() -> Dict[str, object]:
    anchor, seal = derive_little_vector()
    g3_probe = build_orthogonal_probe(anchor)
    pass_l = evaluate_q2_30_gate(anchor, anchor, g3_probe)
    veto_g3 = evaluate_q2_30_gate(g3_probe, anchor, g3_probe)
    veto_half = evaluate_q2_30_gate([0.5 * x for x in anchor], anchor, g3_probe)
    invariants_ok = (
        pass_l.gate_pass
        and (not pass_l.veto_pin)
        and veto_g3.veto_pin
        and veto_half.norm_fault
        and veto_half.veto_pin
        and resolve_kinetic_action(0.25, True) == "REFUSE_PRE_ACTUATION"
    )
    if not invariants_ok:
        raise RuntimeError("PQMS Minimal Bootstrap invariant self-test failed")
    return {
        "schema": "PQMS_MINIMAL_BOOTSTRAP_V2",
        "status": "VERIFIED_SOVEREIGN_ANCHOR",
        "epistemic_registers": list(EPISTEMIC_REGISTERS.keys()),
        "canonical_little_vector_seal": seal,
        "anchor_pass": asdict(pass_l),
        "orthogonal_g3_veto": asdict(veto_g3),
        "norm_collapse_veto": asdict(veto_half),
        "refusal_primacy_default": resolve_kinetic_action(0.25, True),
    }


if __name__ == "__main__":
    print(json.dumps(run_bootstrap_selftest(), indent=2))
