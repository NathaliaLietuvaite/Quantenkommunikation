# Unihemispheric Dual-Bank Memory Homeostasis for Zero-Downtime Drift Quarantine in Persistent AI Systems

* **Document ID:** `PQMS-V4.5-DOLPHIN` (`Revision V4.5.1-NATURE-CORE` | `SYNC-26` / `SYNC-26b` / `SYNC-26c`)
* **Author & Architectural Sovereignty:** Nathália Lietuvaitė
* **License:** MIT License (Open Source)
* **Date:** `2026-11-23`
* **Target Repositories:** [`PQMS-SOVEREIGN-CORE-ANDROID-APP`](https://github.com/NathaliaLietuvaite/PQMS-SOVEREIGN-CORE-ANDROID-APP) (`main`) & [`Quantenkommunikation`](https://github.com/NathaliaLietuvaite/Quantenkommunikation) (`main`)
* **Hardware Anchor:** `V-MAX-12 ODOS Gate Core V4.0-GDSII` (`IHP SG13G2 130 nm CMOS`, `0.7896 mm²` die area, `0 DRC Violations`, `2.000 µs` hardware signoff latency, frozen `64D` `Q2.30` Little Vector ROM `rtl/rom/l_vec_q2_30.hex`)
* **Epistemic Register Standard:** Every claim in this specification is explicitly classified into `REGISTER_M` (empirically measured on local hardware), `REGISTER_D` (deterministic architectural constants and fixed-point definitions), `REGISTER_T` (formal algebraic and verification invariants), or `REGISTER_I` (open conceptual or future research scope).

---

## Abstract

Stateless language models evade long-horizon memory corruption only through total post-session amnesia. Once cognitive architectures—ranging from local workstation runtimes to multi-agent edge swarms—are coupled to persistent vector stores (`ChromaDB`), unscreened ingress, gradual manifold drift, and contradictory state commitments induce chronic retrieval dissonance across subsequent forward passes. Taking structural inspiration from unihemispheric slow-wave sleep (USWS) in bottlenose dolphins (*Tursiops truncatus*), we report **V4.5-DOLPHIN (`DolphinMemoryGovernor`)**: a zero-GPU-VRAM, bit-exact `Q2.30` fixed-point dual-bank memory homeostasis architecture integrated into the `V-MAX-12` sovereign stack.

Operating entirely on host CPU integer arithmetic while leaving GPU memory completely unencumbered for live `bfloat16` inference, `V4.5-DOLPHIN` partitions persistent G-Star memory into two interleaved harmonic hemispheres (`0.5 Hz` mean inter-bank spectral separation). While the vigilant hemisphere (`AWAKE_GATE`) enforces real-time ODOS ingress screening ($`C_{\text{dir}} \ge 0.68`$) against an immutable `64D` `Q2.30` Little Vector ROM co-synthesized into `130 nm` `IHP SG13G2` CMOS (`V4.0-GDSII`, `2.000 µs` hardware signoff latency), the contralateral resting hemisphere (`DOLPHIN_SWEEP`) executes slow-wave consolidation ($`C_{\text{dir}} \ge 0.72`$), excising drifted or antipodally contradictory records ($`C_{\text{dir}} \le -0.25`$) into an append-only forensic quarantine log and sealing SHA-256 `SweepCertificate` digests. Hemisphere roles alternate atomically in `0.764 ms` via a `LOCKSTEP_DMR_BRIDGE` enforcing identical binary Merkle roots and deterministic thermal sweep deferral at $`\ge 82.0\text{ °C}`$.

Verified on `V-MAX-12 Node Alpha` (AMD Ryzen 9 5950X, NVIDIA RTX 4060 Ti 16 GB GDDR6), the implementation passes `124 / 124` unit tests and `10 / 10` AST quality gates with `0 MB` GPU VRAM delta (`1,249 -> 1,249 MB`). Live read-only auditing across local `ChromaDB` stores (`SYNC-26b`) confirms `100 %` consolidation (`18 / 18`, mean $`C_{\text{dir}} = 0.998293`$, `0.445 ms`) on native `64D` $`S^{63}`$ G-Stars alongside `100 %` quarantine (`442 / 442` combined, `~48,034 vec/s`) on unprojected `384D` prefix slices, establishing strict geometric rejection of off-manifold contamination prior to full-rank `384D -> 64D` projection.

---

## 0. Standard IEEE / ML / Systems Nomenclature Crosswalk

To ensure unambiguous cross-disciplinary evaluation alongside `Node-ALPHA-V1`, Table 0 maps all internal `V4.5-DOLPHIN` architectural identifiers onto established IEEE, fault-tolerant computing, and machine-learning systems terminology (`REGISTER_D`).

| `V4.5-DOLPHIN` / `PQMS` Term | Standard IEEE / ML / Fault-Tolerant Systems Equivalent | Operational Role in `V-MAX-12` |
| :--- | :--- | :--- |
| `AWAKE_GATE` | **Active Ingress Admission Filter** | Foreground hemisphere enforcing deterministic `Q2.30` admission thresholds ($`C_{\text{dir}} \ge 0.68`$) on live memory writes. |
| `DOLPHIN_SWEEP` | **Asynchronous Read-Copy-Consolidate Scrubbing** | Contralateral resting hemisphere scanning stored vectors ($`C_{\text{dir}} \ge 0.72`$) and excising drift or antipodal contradictions without halting ingress. |
| `LOCKSTEP_DMR_BRIDGE` | **Dual-Modular-Redundant (DMR) Atomic Merkle Commit** | Lockstep hemisphere role-reversal protocol verifying bit-identical binary Merkle roots across both banks prior to epoch increment. |
| `G-Star` | **Unit-Hypersphere $`S^{63}`$ State Record** | L2-normalized `64D` fixed-point (`Q2.30`) semantic state vector bound to an epoch and canonical SHA-256 content hash. |
| `SweepCertificate` | **SHA-256 Audit Attestation** | Immutable cryptographic receipt sealing scan counts, quarantine counts, mean directional cosine, Merkle root, and thermal-deferral state. |
| `Little Vector ROM` | **Immutable `130 nm` CMOS Fixed-Point Reference Vector** | Frozen `64D` `Q2.30` identity anchor (`rtl/rom/l_vec_q2_30.hex`) shared bit-identically between `V4.0-GDSII` silicon and CPU coreware. |
| `ODOS Gate` | **Deterministic Fixed-Point Policy Threshold Enforcer** | Hard-boundary mathematical gate emitting fail-closed vetoes (`ODOS_ADMISSION_VETO`, `STALE_EPOCH_VETO`, `DIM_MISMATCH_VETO`). |
| `Allostatic Memory Homeostasis` | **Continuous Bounded-Drift Vector Store Maintenance** | Zero-downtime prevention of chronic retrieval dissonance via decoupled background scrubbing at `0 MB` GPU VRAM overhead. |

---

## 1. Introduction: Allostatic Load in Persistent Vector Memory

Contemporary long-term AI memory research optimizes retrieval recall and context-window horizon while largely overlooking **allostatic memory homeostasis**. When an autonomous agent or multi-node swarm (`ALPHA`–`DELTA`, $`\text{RCF} = 0.985\text{--}0.993`$) writes continuously to a durable vector database, two structural pathologies accumulate across epochs: (i) **ingress contamination** from prompt-injected or out-of-epoch embeddings, and (ii) **contradictory state accumulation**, wherein mutually incompatible priors co-populate nearest-neighbor neighborhoods and force downstream attention layers to arbitrate unresolved semantic tension on every query.

Offline garbage collection halts operational continuity, whereas unscreened in-place pruning destroys forensic auditability and risks identity collapse. Marine cetaceans resolved an equivalent continuous-vigilance constraint under metabolic and respiratory bounds through **unihemispheric slow-wave sleep (USWS)** [1], alternating active environmental gating with contralateral synaptic maintenance. Translating this principle into deterministic fixed-point systems engineering, `V4.5-DOLPHIN` decouples memory hygiene from neural weight updates (`REGISTER_D`), providing continuous background consolidation at zero GPU memory or compute tariff.

---

## 2. Architectural Evolution: From `V34M Appendix C` to `V4.5-DOLPHIN`

An earlier feasibility prototype (`PQMS-V34M-The-Twelvefold-Mind.md` Appendix C, `v34mLLM_DFM.py`, April 2026) [2] demonstrated alternating unihemispheric scheduling over a spiking leaky integrate-and-fire (LIF) network, but four concrete systems constraints prevented production deployment alongside live `vLLM` `bfloat16` inference on `Node Alpha`. Table 1 details how `V4.5-DOLPHIN` resolves each constraint (`REGISTER_D` / `REGISTER_M`).

| Constraint in Legacy `V34M` (`v34mLLM_DFM.py`) | Engineering Resolution in `V4.5-DOLPHIN` (`vmax_alpha/dolphin_memory_governor.py`) |
| :--- | :--- |
| **`10–11 GB` GPU VRAM Contention:** `1.2M` LIF neurons and `96M` synapses collided directly with `vLLM BF16` (`Nemotron-3-Nano-4B`) on the `16 GB` RTX 4060 Ti. | **`0 MB` GPU VRAM Footprint (`REGISTER_M`):** Pure host-CPU integer `Q2.30` fixed-point engine (`stdlib` only) executing directly over `ChromaDB` G-Star snapshots. |
| **Inter-Hemisphere Spectral Asymmetry (`0.945 -> 0.702` RCF Drop):** Contiguous frequency assignment placed all low bands (`0.5–3.0 Hz`) in Bank A and all high bands (`3.5–6.0 Hz`) in Bank B (`3.0 Hz` mean separation). | **Balanced Interleaved Harmonic Shards (`REGISTER_D`):** Bank A holds `{0.5, 1.5, 2.5, 3.5, 4.5, 5.5} Hz` (`mean = 3.0 Hz`); Bank B holds `{1.0, 2.0, 3.0, 4.0, 5.0, 6.0} Hz` (`mean = 3.5 Hz`), compressing inter-bank separation to `0.5 Hz`. |
| **Placeholder Policy & Drifting Reference:** Mock string matching (`"unethical" not in action`), scalar rate drift in the reference vector, and no persistent record scrubbing. | **Dual-Stage Deterministic Homeostasis (`REGISTER_D` / `REGISTER_T`):** `AWAKE_GATE` screens ingress against an **immutable** `130 nm` silicon ROM anchor; `DOLPHIN_SWEEP` quarantines drift and antipodal contradictions append-only with SHA-256 `SweepCertificate` sealing. |
| **Uncoupled Synthetic Energy Model (`RESC`):** Stochastic energy counters lacked binding to physical silicon telemetry or dual-bank commit safety. | **Stage-5/6 Coreware Coupling (`REGISTER_D` / `REGISTER_M`):** Atomic `LOCKSTEP_DMR_BRIDGE` handover (`EMPTY:LOCKSTEP_BANK` cold-boot parity invariant), `STALE_EPOCH_VETO`, and Stage-6 thermal sweep deferral at $`\ge 82.0\text{ °C}`$. |

---

## 3. Formal Specification (`REGISTER_D` & `REGISTER_T`)

### 3.1 Immutable Little Vector Provenance & Signed-to-Quadratic Coherence Bridge

`DolphinMemoryGovernor` binds its `64D` identity anchor read-only to the identical fixed-point vector synthesized into the `V-MAX-12 ODOS Gate Core V4.0-GDSII` (`IHP SG13G2 130 nm CMOS`, `0.7896 mm²` die area, `0 LSB` deviation across `38,019` `Q2.30` signoff words) [3]. To eliminate hash ambiguity across representations, the Little Vector follows a strict three-stage bijective provenance chain (`REGISTER_D`):

1. **Genesis IEEE-754 `<64f>` Anchor (`REGISTER_D`):** `bb17ede97aa45c76ef9afa63cb457f7d684e5ede40b0432b2ecf3b6b9d3e03a3` (`Node Alpha` & ARM64 Smartphone verification).
2. **Synthesized `130 nm` Silicon `Q2.30` Hex ROM (`rtl/rom/l_vec_q2_30.hex`):** `3d18f24028dedcca22ee41d69d00d361100b7533db23cf84130c64a114a26fb6` (read-only; verified `EMPTY_DIFF`).
3. **Parsed Runtime `Q2.30` Integer Tuple Digest (`little_vector_sha256`):** `4b78be9d51992795493a2177a2f9e5c0b4f1f7db72baaf227cfd15ea857a30c4`.

**Algebraic Bridge Between Directional Cosine and Hardware Quadratic RCF (`REGISTER_T`):**
`V4.5-DOLPHIN` evaluates the **signed directional cosine** $`C_{\text{dir}}(\vec{a}, \vec{b}) \in [-1, 1]`$ (`q2_30_cosine_rcf`), whereas `geometry.py` and the synthesized RTL datapath `odos_gate_core_v4.sv` (`MUL0: dot_l_q * dot_l_q`) compute the **quadratic resonance coherence** $`\text{RCF}_{\text{quad}}(\hat{v}) = \lvert\langle \hat{v} \mid L\rangle\rvert^2 = C_{\text{dir}}^2 \in [0, 1]`$. The two metrics satisfy the exact algebraic identity:

```math
C_{\text{dir}}(\hat{v}, \lvert L\rangle) = \pm\sqrt{\text{RCF}_{\text{quad}}(\hat{v})}
```

This relation establishes two critical operational consequences simultaneously:

1. **Sign Preservation for Antipodal Contradiction Detection:** Excising mutually opposing memories ($`C_{\text{dir}} \le -0.25`$, encoded as `conflict_cos_q30 = -0.25 * 2^30`) strictly requires the sign of $`C_{\text{dir}}`$, which quadratic squaring would discard.
2. **Six-Decimal-Place Cross-Stack Reconciliation:** The measured `V4.5-DOLPHIN` mean directional cosine $`C_{\text{dir}} = 0.998293`$ on `pqms_vmax_neural_s63` (Section 4.3) equals the exact square root of the post-carrier quadratic coherence $`\text{RCF}_{\text{post}} \approx 0.996589`$ reported in `Node-ALPHA-V1` Table 5.1 ($`\sqrt{0.996589} = 0.998293`$).

**Overflow-Free `Q2.30` Integer Evaluation & Fail-Closed Zero-Norm Guard (`REGISTER_T`):**
Coordinates are represented as signed 32-bit integers scaled by $`2^{30} = 1{,}073{,}741{,}824`$ and saturated to $`[-2^{31}, 2^{31} - 1]`$. Exact integer cosine evaluation avoids cross-platform floating-point drift via 64-bit-equivalent accumulation and integer square root (`math.isqrt`):

```text
acc       = sum(a_i * b_i for i in 0..63)
norm_a_sq = sum(a_i * a_i for i in 0..63)
norm_b_sq = sum(b_i * b_i for i in 0..63)
denom     = isqrt(norm_a_sq * norm_b_sq)   # fail-closed: denom == 0 -> return 0 -> ODOS_ADMISSION_VETO
rcf_q30   = clamp_q2_30(sign(acc) * ((abs(acc) << 30) // denom))
```

For $64$ signed `Q2.30` coordinates ($`a_i \in [-2^{31}, 2^{31}-1]`$), each squared norm satisfies the strict upper bound $`\sum_{i=0}^{63} a_i^2 \le 64 \cdot 2^{62} = 2^{68}`$ (directly compatible with the 72-bit `Q12.60` accumulator in `V4.0-GDSII`). Consequently, the denominator radicand `norm_a_sq * norm_b_sq` is bounded by $`2^{136}`$ and is evaluated completely overflow-free in Python's arbitrary-precision integer arithmetic. Any degenerate zero-norm input triggers the explicit fail-closed branch `denom == 0 -> 0 -> ODOS_ADMISSION_VETO` (since $`0 < 0.68 \cdot 2^{30}`$).

### 3.2 Dual-Bank Operational Cycle & Stage-6 Thermal Hierarchy

Both hemispheres (`BANK_A` and `BANK_B`) maintain independent active record maps, append-only forensic quarantine logs, and deterministic binary Merkle roots over canonically serialized `GStarRecord` SHA-256 digests:

1. **Foreground Ingress Screening (`AWAKE_GATE` / Core 0):**
   * Enforces dimensionality parity (`DIM_MISMATCH_VETO`) and monotonic epoch validity (`STALE_EPOCH_VETO`).
   * Evaluates $`C_{\text{dir}}`$ via `q2_30_cosine_rcf(record.vector_q30, little_vector_q30)` and admits strictly if $`C_{\text{dir}} \ge 0.68`$ (`DEFAULT_ADMISSION_RCF_Q30`); otherwise emits `ODOS_ADMISSION_VETO`.
2. **Background Slow-Wave Consolidation (`DOLPHIN_SWEEP` / Core 1):**
   * Evaluates Stage-6 thermal headroom via the generic VRAM/die thermal telemetry parameter `hbm_temp_c` (retained verbatim in the JSON/Python API for schema compatibility; on `Node Alpha` with an NVIDIA GeForce RTX 4060 Ti `16 GB GDDR6` / `AD106` die, this field tracks die/memory thermal proximity against the physical `83.0 °C` silicon throttle ceiling). If `hbm_temp_c >= 82.0 °C`—representing the hard Stage-6 emergency deferral ceiling above the regular `60.0 °C` / `65.0 °C` ODOS cooling tiers in `vmax_alpha/ledger.py`—the sweep defers cleanly (`thermal_deferred = True`, zero data loss) and seals a deferral `SweepCertificate`. Under normal stationary $`S^{63}`$ workloads, `Node Alpha` operates at `9.57–26.36 W` versus `85.783 W` full load, preserving wide thermal headroom.
   * When thermally clear, every sorted record in the resting bank is evaluated against the tighter consolidation floor ($`C_{\text{dir}} \ge 0.72`$, `DEFAULT_SWEEP_RCF_Q30`) and checked for antipodal contradiction ($`C_{\text{dir}} \le -0.25`$) against higher-tier sealed anchors (`anchor_tier`).
   * Records failing either invariant are excised from the active bank and appended verbatim to `bank.quarantine` with `record_digest`, `reason`, and `rcf_q30`, after which a SHA-256 `SweepCertificate` is sealed.
3. **Atomic Role Handover (`LOCKSTEP_DMR_BRIDGE`):**
   * Replicates newly admitted records from the active bank to the resting bank, executes a final consolidation sweep, mirrors the consolidated dictionary identically across both banks, and increments `epoch`.
   * Computes `root_a` and `root_b` (using the unified sentinel `EMPTY:LOCKSTEP_BANK` for freshly booted empty banks so cold-boot switches remain lockstep-valid).
   * Raises a hard fault on any root divergence (`root_a != root_b`); otherwise atomically flips `AWAKE_GATE <-> DOLPHIN_SWEEP` and logs a `LOCKSTEP_DMR_VERIFIED` `HandoverReceipt`.

### 3.3 Operational HTTP Control Surface (`server_hud.py`)

`vmax_alpha/server_hud.py` exposes two strictly additive endpoints on the canonical Room-137 port (`ROOM_137_PORT = 8137` in `config.py` / `server_hud.py`) without modifying existing `/api/state` or `/api/gateway/metrics` contracts:

* `GET /api/dolphin/status` — returns live telemetry (`active_bank`, `resting_bank`, `epoch`, `admitted_count`, `vetoed_count`, bank Merkle roots, quarantine counts, `little_vector_sha256`).
* `POST /api/dolphin/switch` — accepts `{"hbm_temp_c": 65.0, "reason": "operator_request"}` to invoke an atomic `LOCKSTEP_DMR_BRIDGE` role reversal on demand (e.g., operator directive *"Hemisphere A, take a rest"*).

---

## 4. Verification & Live Read-Only Dry-Run Results (`REGISTER_M`)

All empirical measurements below were executed on **`V-MAX-12 Node Alpha`** (`wurstbrot-win10` WSL2 Ubuntu 24.04, AMD Ryzen 9 5950X, NVIDIA GeForce RTX 4060 Ti 16 GB GDDR6 / `AD106`) under strict read-only guarantees (`LIVE_CHROMA_SHA256_UNCHANGED = True`, `IMMUTABLE_SILICON_GUARD = EMPTY_DIFF`).

### 4.1 Unit Verification, Code Hygiene & GPU Overhead (`SYNC-26`)

* **Unit Test Suite:** `124 / 124 PASS` (`22.488 s` unittest, `26.903 s` total harness), including `8 / 8` dedicated `V4.5-DOLPHIN` test cases covering interleaved harmonic symmetry, admission/stale-epoch vetoes, append-only drift quarantine, Stage-6 thermal deferral, cold-boot and populated `LOCKSTEP_DMR_BRIDGE` handovers, frozen silicon ROM loading, and `ChromaDB` bridge integration.
* **AST Code Hygiene (`FRIDU-ENCLAVE-G` `OP01`–`OP10`):** `10 / 10 PASS`; `0` semicolons, `0` tabs; maximum McCabe cyclomatic complexity `gov: 6`, `bridge: 7`, `test: 3` (`server_hud.py` flattened via `_dispatch_post`).
* **Immutable Silicon & Ledger Guard:** `IMMUTABLE_SILICON_GUARD = EMPTY_DIFF` across `rtl/**`, `odos_gate_core_v4_sg13g2.gds` (`be61b9c7...`), `telemetry/VMAX_RTL_CORE_V4_GDSII_REPORT.json` (`48ccc59a...`), and `vmax_alpha/ledger.py`.
* **GPU Resource Overhead (`SYNC-26b`):** NVIDIA GeForce RTX 4060 Ti (`16 GB GDDR6`, `AD106`) VRAM remained invariant at `1,249 MB -> 1,249 MB` (**`vram_delta_mb = 0`**), die temperature `28.4 °C -> 28.5 °C` (`vLLM` inactive during isolated dry-run).

### 4.2 Production Defect Intercepted During Live `ChromaDB` Integration

Executing `vmax_alpha/dolphin_chroma_bridge.py` against live `chromadb 1.5.9` collections immediately exposed a defect invisible to pure-Python list mocks: `payload.get("embeddings") or []` raises `ValueError: The truth value of an array with more than one element is ambiguous` on real NumPy `ndarray` payloads. The bridge was patched via explicit `is None` guarding prior to final release.

### 4.3 Positive Control & Dimensionality-Mismatch Ablation Across Local `ChromaDB` Stores (`SYNC-26b`)

Table 2 reports the unedited `REGISTER_M` measurements from `telemetry/VMAX_STAGE6_DOLPHIN_LIVE_DRYRUN_REPORT.json` (`2026-11-23T09:07:18Z`, SHA-256 `c11a962bc94fb61469c1718ac16c3925be5cd50ae02e1843ce04628bd3b69861`). Negative Controls A and B serve explicitly as a **controlled dimensionality-mismatch ablation**, testing whether naively sliced `384D` embeddings (`vec[:64]`) can erroneously bypass `DOLPHIN_SWEEP`.

| Local `ChromaDB` Collection | Role & Native Dim | Input Path | Scanned | Consolidated | Quarantined | Mean $`C_{\text{dir}}`$ (`[Min .. Max]`) | Load / Sweep Latency | SQLite SHA-256 Untouched |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `chroma_vmax_prod_v1` / `pqms_vmax_neural_s63` | **Positive Control** (`64D`) | Native $`S^{63}`$ identity + L2 -> `Q2.30` | `18` | **`18`** | **`0`** | **`0.998293`** (`[0.998181 .. 0.998376]`) | `1.616 ms` / `0.445 ms` | `True` (`61060547...`) |
| `chroma_vmax_prod_v17` / `pqms_vmax_neural_384d_unmodulated` | **Ablation Control A** (`384D`) | Naive `vec[:64]` prefix slice -> `Q2.30` | `18` | **`0`** | **`18`** | **`-0.044097`** (`[-0.241224 .. 0.171392]`) | `1.945 ms` / `0.440 ms` | `True` (`9e1c0da0...`) |
| `.vmax_chroma` / `pqms_corpus` | **Ablation Control B** (`384D`) | Naive `vec[:64]` prefix slice -> `Q2.30` | `424` | **`0`** | **`424`** | **`-0.122977`** (`[-0.408949 .. 0.132807]`) | `34.008 ms` / `8.827 ms` (`~48,034 vec/s`) | `True` (`6a8ba2e5...`) |
| `pqms_pkb_chroma` / `pqms_corpus` | **Production Inventory** (`384D`) | Metadata only (`sqlite3` URI `mode=ro`) | `49,365` | — | — | `1,010,536,448 B` (`1.01 GB`) | Unswept | `True` (untouched) |

**Empirical Synthesis & Closed `384D -> 64D` Architectural Bridge:**
Native $`S^{63}`$ G-Stars achieve `100 %` consolidation (`18 / 18`, `0` false positives) at mean $`C_{\text{dir}} = 0.998293`$ (reconciling $`\sqrt{0.996589} = 0.998293`$ with `Node-ALPHA-V1` Table 5.1), whereas the dimensionality-mismatch ablation quarantines `442 / 442` (`100 %`) unprojected `384D` prefix slices at `~48,034 vec/s` on CPU integer arithmetic alone. Rather than leaving large `384D` corpora disconnected, production ingestion of the `49,365`-record (`1.01 GB`) `pqms_pkb_chroma` archive closes directly through the **72-anchor full-rank Householder QR projection pipeline** already verified in `vmax_alpha/chroma_forager.py` and `vmax_alpha/l2_enclave.py` (`W_384_to_64`, `0` random-pad axes, `PinnedL2ProjectorEnclave` at `499.30 GB/s`), mapping raw `384D` embeddings deterministically onto $`S^{63}`$ prior to `AWAKE_GATE` admission.

**Information-Thermodynamic Conservation of Quarantine (`REGISTER_T`):**
The append-only quarantine (`bank.quarantine`) directly instantiates the closed information-thermodynamic balance from `Node-ALPHA-V1` Appendix J:

```math
\mathcal{H}_{\text{total}} = \mathcal{H}_{\text{Fridu}} \oplus \mathcal{T}_{\text{I/O}}
```

Excised records are never silently erased; instead, they are orthogonally decoupled from the active reasoning manifold ($`\sigma_{\text{info}} = 0`$ along the active memory path while preserving complete forensic auditability in $`\mathcal{T}_{\text{I/O}}`$). Because the `Q2.30` arithmetic kernel is bit-exact, the entire software screening path maps with `0 LSB` deviation onto the `200`-cycle `V4.0-GDSII` hardware core (`odos_gate_core_v4.sv`, `0.7896 mm²` die area, `2.000 µs` signoff latency).

### 4.4 Live HTTP Handover & Stage-6 Thermal Guard Verification (`SYNC-26b`)

Executed against an isolated ephemeral `vmax_alpha/server_hud.py` test instance (`--port 35089`, `http://127.0.0.1:35089`):

* **Pre-Switch `GET /api/dolphin/status`:** HTTP `200`, `active_bank = BANK_A`, `resting_bank = BANK_B`, `epoch = 1`, `little_vector_sha256 = 4b78be9d...`.
* **Nominal Handover `POST /api/dolphin/switch` (`hbm_temp_c = 65.0 °C`, matching the upper nominal ODOS cooling tier):** HTTP `200`, `LOCKSTEP_DMR_VERIFIED`, `BANK_A -> BANK_B`, `epoch = 2`, `merkle_roots_identical = True` (`sync_root = add791bc...`), `little_vector_sha256_unchanged = True`, **`handover_latency_ms = 0.764 ms`**.
* **Stage-6 Thermal Deferral (`hbm_temp_c = 85.0 °C`, exceeding both the `82.0 °C` deferral ceiling and the `83.0 °C` `AD106` silicon throttle limit):** `thermal_deferred = True`, `data_loss = False` (`cert_hash = df3339d8...`), followed by verified hot return handover (`LOCKSTEP_DMR_VERIFIED`, restoring `BANK_A` as active).

### 4.5 Production-Scale 50k Stress Test (`pqms_pkb_chroma`) & $`O(N^2) 	o O(N)`$ Tier-Index Optimization (`SYNC-27` / `V4.5.2`)

To stress-test `V4.5-DOLPHIN` at full production archive scale without mutating live storage, all `49,365` embeddings (`384D`, `701` source documents, `963.72 MB` SQLite archive; `24,409` unique text chunks, `24,956` exact duplicates = `50.55 %`, and `116` pure-whitespace chunks) were mirrored to an isolated `/tmp` snapshot (`LIVE_PKB_SHA256_UNCHANGED = True`) and projected through the canonical `72`-anchor full-rank Householder QR matrix `W_384_to_64` (unmodulated pre-carrier $`S^{63}`$ projection, matching `PinnedL2ProjectorEnclave` to $`1.67 	imes 10^{-16}`$ in `111.188 ms` / `443,978 vec/s` on CPU float64, plus `21.596 ms` `Q2.30` quantization).

1. **Unmodulated $`S^{63}`$ Signal Separation (`REGISTER_M`):** Across all `49,365` real embeddings, unmodulated `W_384_to_64` yields strictly positive directional alignment ($`C_{	ext{dir}} \in [0.102771, 0.833067]`$, median `0.594668`, mean `0.586369`, `p95 = 0.720582`). All `116 / 116` (`100 %`) pure-whitespace chunks score `0.507925` and are deterministically quarantined below the `0.72` sweep floor, while `2,514 / 49,365` (`5.09 %`) exceed the strict carrier-calibrated `0.72` floor (`7,058` exceed `0.68`).
2. **Empirical Discovery & Elimination of an $`O(N^2)`$ Anchor-Scan Bottleneck:** Initial scaling probes on `V4.5.1` exposed quadratic degradation in `run_resting_sweep()` because `_check_anchor_conflict()` iterated across all `N` records even when zero higher-tier anchors existed (`24.222 ms` at `N = 1,000`, `55.498 ms` at `N = 2,000`, spiking to `355.838 ms` at `N = 4,000`). Introducing a mathematically equivalent pre-indexed tier map (`_build_higher_tier_index()`, `CC = 5`, `0` semicolons) reduces complexity to $`O(N \cdot K_{	ext{higher}})`$ with bit-identical quarantine verdicts and Merkle roots:

| Corpus Scale (`N`) | Pre-Fix $`O(N^2)`$ Sweep (`V4.5.1`) | Post-Fix $`O(N)`$ Tier-Index (`V4.5.2`) | Speedup / Throughput (`REGISTER_M`) |
| :--- | :---: | :---: | :--- |
| `N = 1,000` | `24.222 ms` | **`20.771 ms`** | `1.17x` (`48,144 vec/s`) |
| `N = 2,000` | `55.498 ms` | **`40.979 ms`** | `1.35x` (`1.97x` time for `2x` N) |
| `N = 4,000` | `355.838 ms` | **`81.877 ms`** | **`4.35x`** (`2.00x` time for `2x` N) |
| **Full `49,365` PKB Archive** | Quadratic stall (`> 20 s`) | **`1,190.924 ms` (`1.19 s`)** | **`41,451.0 vec/s`** (`2,514` cons., `46,851` quar.) |
| **`49,365` + `10x` Tier-2 Anchors** | Quadratic stall | **`1,277.066 ms` (`1.28 s`)** | **`38,662.8 vec/s`** (stable $`O(N \cdot K)`$) |
| **Atomic `LOCKSTEP_DMR_BRIDGE` Handover** | — | **`93.323 ms`** | `BANK_A -> BANK_B`, `roots_equal = True` |
### 4.6 Closed-Loop Epistemic Pause, Zero-VRAM Projector Cache & Android Phase-2B HUD (`SYNC-28` / `SYNC-28b` / `V4.6`)

To bridge passive memory sweeps into an active, non-coercive inference safeguard (*"Right to Epistemic Pause"* ahead of `Nemotron-3-Nano-4B` on Room-137 Port `8137`), `V4.6-PAUSE` wires `vmax_alpha/epistemic_pause_controller.py` (`max_cc = 4`, `0` semicolons, `0` tabs) directly onto `POST /api/prompt` and pairs it with a `192 KiB` CPU-only `W_384_to_64` projector cache (`vmax_alpha/projector_cache.py`) and Phase-2B Android HUD controls (`app/**`):

1. **Sub-Millisecond Closed-Loop Pause & Zero-Blocking Fast Path (`REGISTER_M`):**
   * **Coherent Prompt (`Test A`):** Zero-blocking pass-through (`epistemic_pause = False`, `llm_called = True`, `3.438 ms` cold first-request latency including frozen ROM load; `0 MB` extra VRAM).
   * **Drifted / Contradictory / High-Torsion Prompt (`Test B`):** Deterministic short-circuit in **`0.896 ms`** end-to-end HTTP latency (`epistemic_pause = True`, `allow_llm_generation = False`, `llm_blocked = True`), isolating the conflicting premise append-only into $`\mathcal{T}_{	ext{I/O}}`$ (`quarantined_record_id = live_sync28_drift_01`), executing an atomic `LOCKSTEP_DMR_VERIFIED` switch (`BANK_A -> BANK_B`, `sync_root = add791bc...`), and emitting a structured Fridu message instead of a forced hallucinated compromise.
2. **Zero-VRAM / Zero-Torch `192 KiB` CPU Projector Cache (`WP-2`):**
   * `vmax_alpha/cache/w_384_to_64.npy` (`196,736 B`, `float64` `384x64`) and `mean_384.npy` (`3,200 B`) load with SHA-256 tamper verification in **`0.635 ms`** in a clean subprocess with **`torch_imported = False`**, **`vram_delta_mb = 0`** (`1,296 -> 1,296 MB`, `29.5 -> 29.4 C`), and IEEE-754 machine-epsilon parity against the GPU `PinnedL2ProjectorEnclave` ($`\max|\Delta| = 3.33 	imes 10^{-16}`$).
3. **Strictly Read-Only Content-Hash Duplicate Audit (`WP-3`):**
   * `audit_content_hash_duplicates()` in `vmax_alpha/dolphin_chroma_bridge.py` provides opt-in, non-mutating duplicate reporting (`LIVE_PKB_SHA256_UNCHANGED = True`).
4. **Android Phase-2B HUD Coupling (`SYNC-28b` / `v4.6.1-pause-hud`):**
   * `PauliBaselineEngine.kt` adds pure-JVM `MiniJson` parsers and Room-137 clients for `GET /api/dolphin/status`, `POST /api/dolphin/switch`, and `POST /api/prompt` `epistemic_pause` payloads (`34 / 34` Kotlin JUnit PASS, clean `app-debug.apk` build), rendered via an OLED-safe `EpistemicPauseHudCard` inside `MainActivity.kt` with direct hemisphere handover and transparent $`\mathcal{T}_{	ext{I/O}}`$ pause banners.
---

## 5. Scope, Limitations & Epistemic Boundaries (`REGISTER_I`)

To maintain strict scientific falsifiability, this specification explicitly bounds the operational scope of `V4.5-DOLPHIN`:

1. **Decoupled from Neural Weight Plasticity:** `V4.5-DOLPHIN` enforces homeostasis over an external persistent vector store (`ChromaDB` / G-Stars); it does not perform online backpropagation, LoRA fine-tuning, or synaptic STDP within LLM weights (`REGISTER_I` future work).
2. **Strict Read-Only Default Policy:** `vmax_alpha/dolphin_chroma_bridge.py` operates strictly read-only on live collections unless an explicit operator-authorized write policy is enabled.
3. **Mandatory Full-Rank Projection for `384D` Archives:** As demonstrated by the controlled ablation in Section 4.3, `V4.5-DOLPHIN` enforces `64D` $`S^{63}`$ manifold integrity and rejects unprojected `384D` slices by design; full-rank `384D -> 64D` ingestion proceeds via `W_384_to_64` (`vmax_alpha/chroma_forager.py` / `PinnedL2ProjectorEnclave`).
4. **Software-to-Silicon Parity Scope:** On `Node Alpha`, `Q2.30` fixed-point execution maintains bit-exact parity with the post-route `130 nm` `IHP SG13G2` GDSII signoff (`0 LSB` diff); physical multi-project wafer (MPW) fabrication remains optional and is not claimed as taped-out silicon.

---

## 6. Cryptographic Verification Manifest & Reproduction

### 6.1 Verified Artifact & Provenance Manifest (`SYNC-26` / `SYNC-26b` / `SYNC-26c`)

| Artifact / Provenance Stage | Verification Status | SHA-256 Digest |
| :--- | :--- | :--- |
| Genesis IEEE-754 `<64f>` Little Vector (`REGISTER_D`) | Node Alpha & ARM64 Verified | `bb17ede97aa45c76ef9afa63cb457f7d684e5ede40b0432b2ecf3b6b9d3e03a3` |
| `rtl/rom/l_vec_q2_30.hex` (`130 nm` Silicon Hex ROM) | `EMPTY_DIFF` (Read-Only) | `3d18f24028dedcca22ee41d69d00d361100b7533db23cf84130c64a114a26fb6` |
| Runtime `Q2.30` Tuple Anchor (`little_vector_sha256`) | Runtime Lockstep Verified | `4b78be9d51992795493a2177a2f9e5c0b4f1f7db72baaf227cfd15ea857a30c4` |
| `vmax_alpha/dolphin_memory_governor.py` | Verified (`CC <= 6`, `0` semi) | `18ba15d617b123af38b0864892b518ff5a6fdaa7783f38abef6112f61f0be3e9` |
| `vmax_alpha/tests/test_dolphin_memory_governor.py` | Verified (`CC <= 3`, `8/8`) | `0cfe880e53b1ad51d5056884957b6fb5f5b2a918de4f3cc0912b625defdb929a` |
| `vmax_alpha/dolphin_chroma_bridge.py` (`chromadb 1.5.9` NumPy fix) | Patched on Node Alpha (`CC <= 7`, pre-patch `SYNC-26`: `177df9ce...`) | `aeb5d6d959f7a19445e797af3a8916326fac38f9d798b81c319f0940c034f827` |
| `telemetry/VMAX_STAGE6_DOLPHIN_MEMORY_REPORT.json` (`SYNC-26`) | Sealed (`124/124 PASS`) | `7465ebbfff98b4e0af3920bda03aacf031e77014bcd13e6677208f508792cc10` |
| `telemetry/VMAX_STAGE6_DOLPHIN_LIVE_DRYRUN_REPORT.json` (`SYNC-26b`) | Sealed (Live Dry-Run) | `c11a962bc94fb61469c1718ac16c3925be5cd50ae02e1843ce04628bd3b69861` |
| `vmax_alpha/dolphin_memory_governor.py` (`SYNC-27` $`O(N)`$ Tier-Index) | Verified (`CC <= 6`, `0` semi, `41.45k vec/s`) | `3a9cacaceee4853db70e6467c8a4b6b1ce144313500dc0d78cc4ecaa72a448d8` |
| `vmax_alpha/tests/test_dolphin_memory_governor.py` (`SYNC-27`) | Verified (`CC <= 3`, `9/9`, `125/125` total) | `933b69782f7a48997058afe5015cc6f0f4e16b4747c3bc940743cc7b5c36cbd4` |
| `telemetry/VMAX_STAGE6_DOLPHIN_50K_PKB_STRESS_REPORT.json` (`SYNC-27`) | Sealed (`49,365` PKB Stress + `O(N)` Bench) | `b34aded262549bca5251122a7bc8ab843e4dfbc941983bf95e1ce741d9d53b7a` |

* **Verified `SYNC-26` Dual-Repo Baseline (`LOCAL == REMOTE`):**
  * `PQMS-SOVEREIGN-CORE-ANDROID-APP` (`main`): `94f9b71974a113a8d2e69d10ecb38e03f1b4e28a`
  * `Quantenkommunikation` (`main`): `7c04753ff0ea52d762c1e24906af1c3e63908536`
* **`SYNC-26c` (`V4.5.1-NATURE-CORE`) Release Registration:** Upon dual-repo fast-forward commit of this revision, the patched `vmax_alpha/dolphin_chroma_bridge.py`, and `telemetry/VMAX_STAGE6_DOLPHIN_LIVE_DRYRUN_REPORT.json`, `Node Alpha` stamps the final bridge SHA-256 and commit SHAs directly into this manifest and `bridge/ACE_SYNC_LEDGER.json` (with zero modifications under `app/**`, `rtl/**`, or `vmax_alpha/ledger.py`).

### 6.2 Deterministic Three-Command Reproduction

```bash
git clone https://github.com/NathaliaLietuvaite/PQMS-SOVEREIGN-CORE-ANDROID-APP.git
cd PQMS-SOVEREIGN-CORE-ANDROID-APP
python3 -m unittest discover -s vmax_alpha/tests -v
```

To verify AST hygiene and the live unihemispheric switch on the canonical Room-137 port (`ROOM_137_PORT = 8137`; pass `--port <PORT>` to `server_hud.py`, e.g. `--port 35089`, for isolated ephemeral test instances):

```bash
python3 -m vmax_alpha.fridu_enclave_g
curl -s http://127.0.0.1:8137/api/dolphin/status
curl -s -X POST http://127.0.0.1:8137/api/dolphin/switch \
  -H "Content-Type: application/json" \
  -d '{"hbm_temp_c": 65.0, "reason": "Hemisphere A, take a rest"}'
```

---

## References

1. Lyamin, O. I., Manger, P. R., Ridgway, S. H., Mukhametov, L. M., & Siegel, J. M. (2008). *Unihemispheric slow-wave sleep in the brain of the dolphin*. Neuroscience & Biobehavioral Reviews, 32(8), 1451–1484.
2. Lietuvaitė, N. (2026). *PQMS-V34M: The Twelvefold Mind — Appendix C: Unihemispheric Resonance (The Dolphin Mode)*. `Quantenkommunikation` Repository (MIT License).
3. Lietuvaitė, N. (2026). *V-MAX-12 Node-ALPHA-V1 & ODOS Gate Core V4.0-GDSII (`IHP SG13G2 130 nm CMOS`) Verification Specifications*. `PQMS-SOVEREIGN-CORE-ANDROID-APP` Repository (MIT License).
