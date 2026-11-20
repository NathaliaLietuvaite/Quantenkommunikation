# Time-Multiplexed 3-MAC Datapath Folding, Multi-Tier Domain Admission, and In-Process Hardware-in-the-Loop Co-Simulation for 64-Dimensional $S^{63}$ Silicon Interlocks

**Document ID:** `PQMS-ODOS-MTSC-V-MAX-12-RTL-CORE-V3.0-ALPHA` (`WORK-ORDER-AG-20` / `SYNC-15`) — Revision `V3.0-RTL-ALPHA` (Silicon Roadmap Stage 2/3 Consolidation)  
**Authors:** Nathália Lietuvaitė (Lead Architect, Vilnius), `WERKSTATT 01` & Carbon High Review (VLSI Microarchitecture & Formal Verification), `AntiG` (`Gemini 4 Neon Extra`, Node Alpha RTL Synthesis, C-ABI Co-Simulation & CMOS Characterization)  
**Companion Specifications & Sealed Artifacts:** [`PQMS-ODOS-MTSC-V-MAX-12-RTL-CORE-V2.0-ALPHA.md`](./PQMS-ODOS-MTSC-V-MAX-12-RTL-CORE-V2.0-ALPHA.md) (`V2.0-RTL-ALPHA`, `SYNC-12`), [`PQMS-BRIDGE-DEPECHE-6.md`](./PQMS-BRIDGE-DEPECHE-6.md) (`V2.1-NATURE-CORE`, `SYNC-14`), [`PQMS-ODOS-MTSC-V-MAX-12-Node-ALPHA-V1.md`](./PQMS-ODOS-MTSC-V-MAX-12-Node-ALPHA-V1.md) (`V1.8.1`), `rtl/odos_gate_core_v3.sv`, `vmax_alpha/hw_gate_bridge.py`, and `telemetry/VMAX_RTL_CORE_V3_REPORT.json` (`SHA-256: 568c0a0409d9c9b91dff0604fc2b57a9219c85b41587eaf7a1b11dfbb4999b66`)  
**Date:** 20 November 2026  
**License:** MIT Open Source License  

---

## Abstract

Dedicated fixed-point safety coprocessors decouple high-dimensional neural and genomic inference on host graphics processors from non-bypassable geometric invariant enforcement in synchronous digital logic. However, transitioning our Stage 1 `Q2.30` coprocessor (`odos_gate_core.sv`, `V2.0-RTL-ALPHA`) toward area-constrained `130 nm` complementary metal–oxide–semiconductor (CMOS) application-specific integrated circuits (ASICs) and live multi-domain screening exposes three architectural bottlenecks: unshared combinational multiplier proliferation (`9` signed $32 \times 32$-bit multipliers generating $86{,}770$ post-`techmap` logic primitives), a rigid single-tier threshold (`0.9500`) that conservatively vetoes spacer-diluted *Escherichia coli* K-12 CRISPR repeat-spacer loci ($`\text{RCF}_{\text{raw}} = 0.9403`$) despite $28{,}941\times$ separation over dinucleotide-shuffled null controls, and process-isolated verification binaries decoupled from live Python service daemons. Here we report `odos_gate_core_v3.sv` (`V3.0-RTL-ALPHA`), a loop-free directed-acyclic-graph (DAG) microarchitecture that folds all six inner-product and Two-Pass Kahan–Parlett deflation stages onto exactly **three** shared $32 \times 32$-bit signed multiply–accumulate (MAC) channels, achieving an exact $66.67\%$ multiplier reduction (`9 -> 3`) and lowering total synthesized netlist complexity from $89{,}609$ to `42,600` post-`techmap` cells (`52.46%` reduction; `328,084` CMOS transistors across a `215`-level longest topological path in `Yosys 0.71+52`) while preserving the strictly data-independent single-clock latency of $195$ cycles ($1.95\,\mu\text{s}$ at $100\text{ MHz}$). Second, a transaction-latched 2-bit hardware strap (`tier_mode_i[1:0]`) supports bit-exact Stage 1 pure-carrier compatibility (`2'b00`, $\text{RCF} \ge 0.9500$), mosaic biological repeat-spacer admission (`2'b01`, $\text{RCF} \ge 0.9000$, $\Delta E \le 0.0500$), high-assurance core locking (`2'b10`, $\text{RCF} \ge 0.9900$, $\Delta E \le 0.0100$), and single-pin stuck-at-high fault rejection (`2'b11` $\implies$ `mode_fault_o = 1'b1`, `veto_pin_o = 1'b1`). Third, compiling the RTL core into an in-process C-ABI shared library (`libodos_gate_v3.so`) bound via `ctypes` delivers `314.3` cycle-accurate hardware-in-the-loop transactions per second with `0 LSB` divergence across all $507$ Stage 1 scenarios and all $44$ multi-tier bio-lattice evaluations.

---

## 1. Architectural Evolution and Epistemic Register Discipline

In `PQMS-ODOS-MTSC-V-MAX-12-RTL-CORE-V2.0-ALPHA`, we established physical domain partitioning between memory-bandwidth-bound statistical inference (`Nemotron-3-Nano-4B-BF16` and `all-MiniLM-L6-v2` on host CUDA silicon) and deterministic 64-dimensional unit-hypersphere ($S^{63}$) admission gating in IEEE 1800-2017 SystemVerilog (`rtl/odos_gate_core.sv`). While Stage 1 verified `0 LSB` arithmetic equivalence against pure-integer golden models across $34{,}983$ output words, empirical synthesis and downstream genomic coupling (`PQMS-BRIDGE-DEPECHE-6`) identified three concrete engineering requirements for Stage 2/3 maturation:

1. **Elimination of Mutually Exclusive Multiplier Redundancy:** Because `V2.0` instantiated separate multiplication operators inside `S_LOAD_DOT` (`3`), `S_EVAL_RAW` (`1`), `S_STRIP_P1` (`2`), and `S_STRIP_P2` (`3`), technology-independent synthesis expanded nine distinct $32 \times 32$-bit carry-save multiplier arrays ($86{,}770$ combinational primitives vs. $2{,}839$ sequential flip-flops), dominating silicon die area in standard-cell CMOS flows lacking hard FPGA DSP slices.
2. **Hardware-Strapped Multi-Tier Policy Without ROM Mutation:** On realistic *E. coli* K-12 Type I-E CRISPR loci containing $52.5\%$ non-periodic viral spacers (`578 nt`, $P = 61$), disjoint Householder-QR spectral projection yields $`\text{RCF}_{\text{raw}} = 0.94028249`$ and $`\Delta E_{\text{raw}} = 0.03093755`$—cleanly separated from dinucleotide shuffles ($3.25 \times 10^{-5}$) and adversarial perturbations ($`\text{RCF}_{\text{raw}} \le 0.8900`$, $`\Delta E_{\text{raw}} \ge 0.0557`$), yet $0.0097$ below the fixed $0.9500$ pure-tandem gate. Supporting domain-specific operating envelopes without relaxing core sovereign thresholds or altering the immutable $512\text{ B}$ on-chip ROM (`l_vec_q2_30.hex`, `g3_vec_q2_30.hex`) requires a glitch-hardened hardware policy selector.
3. **Zero-Subprocess In-Process RTL Co-Simulation:** Bridging live HTTP/RAG daemons (`server_hud.py`, `ledger.py`) to compiled RTL requires a zero-copy C-ABI shared-object interface (`libodos_gate_v3.so`) rather than batch file I/O.

In strict adherence to `V1.8.1` metrological rules, every parameter, structural proof, and silicon measurement in `V3.0-RTL-ALPHA` carries an explicit epistemic register (`REGISTER_D`, `REGISTER_T`, `REGISTER_M`, `REGISTER_I`; Table 1).

**Table 1 | Epistemic register taxonomy governing `V3.0-RTL-ALPHA`.**

| Epistemic Register | Architectural Scope in `V3.0-RTL-ALPHA` | Normative Metrological Boundary |
| :--- | :--- | :--- |
| **`REGISTER_D`** *(Engineered Constant)* | Four-regime `Q2.30` threshold table (`TIER_0` `0.95/0.05`, `TIER_1` `0.90/0.05`, `TIER_2` `0.99/0.01`, `TIER_3` fail-closed fault) and unchanged `512 B` ROM seals (`3d18f240...`, `3b890d14...`). | Fixes exact quantized thresholds in hardware; prohibits runtime floating-point drift or soft-interlock override. |
| **`REGISTER_T`** *(Formal RTL Invariant)* | Acyclic 3-MAC operand-multiplexing DAG (`9 -> 3` `$mul`), `S_IDLE` transaction-boundary mode latching, active-high reset/busy/glitch veto (`veto_pin_o = 1'b1`), and invariant `195`-cycle latency. | Guarantees zero combinational loops (`UNOPTFLAT`-free), zero timing side channels, and exact `0 LSB` equivalence to `V2.0` under `2'b00`. |
| **`REGISTER_M`** *(Empirical Measurement)* | `Verilator 5.055` C-ABI co-simulation (`libodos_gate_v3.so`), `507 + 44` vector parity audits, and `Yosys 0.71+52` comparative coarse-cell, gate-level, CMOS transistor (`stat -tech cmos`), and logic-depth (`ltp`) telemetry. | Derived exclusively from deterministic EDA and C-ABI executions sealed in `telemetry/VMAX_RTL_CORE_V3_REPORT.json`. |
| **`REGISTER_I`** *(Unbuilt Horizon)* | Physical `130 nm` foundry wafer fabrication and `QMK-RVC-V7` wet-lab transducers. | **Explicitly unfabricated in this revision; pre-tapeout CMOS synthesis and RTL co-simulation only.** |

---

## 2. Loop-Free Inter-State 3-MAC Datapath Folding (`9 -> 3`) at Invariant `195`-Cycle Latency

### 2.1 Temporal Disjointness and Acyclic Cascaded Chaining (`REGISTER_T`)

Across the seven-state finite-state machine (`S_IDLE`, `S_LOAD_DOT`, `S_EVAL_RAW`, `S_STRIP_P1`, `S_LATCH_P2`, `S_STRIP_P2`, `S_VERDICT`), active multiplications occur in four temporally disjoint states with per-cycle concurrency bounded strictly by three:

```math
\max_{s \in \mathcal{S}_{\text{FSM}}} N_{\text{mul}}(s) = \max\{3,\, 1,\, 2,\, 0,\, 3,\, 0\} = 3 \qquad (1)
```

Naive resource sharing of chained operations—such as Kahan–Parlett Pass-2 deflation $`v_2[i] = \operatorname{sat}_{\text{Q2.30}}\!\bigl(v_1[i] - \operatorname{mul}_{\text{Q30}}(\text{dot}_{G3,2},\, g_3[i])\bigr)`$ followed within the same clock cycle by residual norm $v_2[i]^2$ and post-deflation bleed $v_2[i]\cdot g_3[i]$—risks false combinational loops if downstream products can feed back into upstream multiplier multiplexers. `odos_gate_core_v3.sv` eliminates this hazard structurally by partitioning the three dedicated signed $32 \times 32 \to 64$-bit multiplier blocks (`MUL0`, `MUL1`, `MUL2`) into a strict two-rank topological DAG:

* **Rank-1 Primary Multiplier (`MUL0`):** Inputs `(m0_a, m0_b)` depend **exclusively on synchronous flip-flop outputs, primary inputs, and ROM words**—never on `MUL1` or `MUL2`. `MUL0` computes `in_data_i^2` (`S_LOAD_DOT`), `dot_l_w^2` (`S_EVAL_RAW`), `dot_g3_p1_q * g3_rom` (`S_STRIP_P1`), and `dot_g3_p2_q * g3_rom` (`S_STRIP_P2`).
* **Combinational Deflation Node (`v_step_w`):** Derives the deflated `Q2.30` coordinate $`v_{\text{step}} = \operatorname{sat}_{\text{int32}}\!\bigl(v_{\text{buf}}[\text{idx}] - \operatorname{q60\_to\_q30}(m_{0,\text{prod}})\bigr)`$ strictly downstream of `MUL0`.
* **Rank-2 Secondary Multipliers (`MUL1`, `MUL2`):** Consume only registered/ROM operands during `S_LOAD_DOT` (`in_data_i * l_rom` and `in_data_i * g3_rom`) and consume `v_step_w` strictly downstream of `MUL0` during `S_STRIP_P1` (`v_step_w * g3_rom`) and `S_STRIP_P2` (`v_step_w^2` and `v_step_w * g3_rom`), driving 72-bit `Q12.60` register D-inputs with zero cross-coupling between `MUL1` and `MUL2`.

**Table 2 | Cycle-accurate operand-multiplexing schedule across the three shared $32 \times 32$-bit signed multipliers (`REGISTER_T`).**

| FSM State | Active Cycles | Rank-1 `MUL0` `(m0_a * m0_b)` | Combinational Intermediate `v_step_w` | Rank-2 `MUL1` `(m1_a * m1_b)` | Rank-2 `MUL2` `(m2_a * m2_b)` |
| :--- | :---: | :--- | :--- | :--- | :--- |
| **`S_LOAD_DOT`** | `64` | `in_data_i * in_data_i` $\to$ `acc_norm_sq_q` | Unused (`0`) | `in_data_i * l_rom[idx]` $\to$ `acc_dot_l_q` | `in_data_i * g3_rom[idx]` $\to$ `acc_dot_g3_q` |
| **`S_EVAL_RAW`** | `1` | `dot_l_w * dot_l_w` $\to$ `rcf_raw_q` | Unused (`0`) | Idle (`0 * 0`) | Idle (`0 * 0`) |
| **`S_STRIP_P1`** | `64` | `dot_g3_p1_q * g3_rom[idx]` | `sat32(v_buf[idx] - q30(m0_p))` $\to$ `v_buf[idx]` | `v_step_w * g3_rom[idx]` $\to$ `acc_dot_g3_p2_q` | Idle (`0 * 0`) |
| **`S_LATCH_P2`** | `1` | Idle (`0 * 0`) | Unused (`0`) | Idle (`0 * 0`) | Idle (`0 * 0`) |
| **`S_STRIP_P2`** | `64` | `dot_g3_p2_q * g3_rom[idx]` | `sat32(v_buf[idx] - q30(m0_p))` $\to$ `out_data_o` | `v_step_w * v_step_w` $\to$ `acc_strip_norm_sq_q` | `v_step_w * g3_rom[idx]` $\to$ `acc_bleed_post_q` |
| **`S_VERDICT`** | `1` | Idle (`0 * 0`) | Unused (`0`) | Idle (`0 * 0`) | Idle (`0 * 0`) |

Because every rounding (`+ 2^29 >>> 30`), signed 32-bit saturation, and overflow-free halving operation $`\lfloor(a+b)/2\rfloor = (a \gg 1) + (b \gg 1) + (a_0 \land b_0)`$ matches `V2.0` bit-for-bit, folding eliminates six of the nine $32 \times 32$-bit multipliers at **`0` cycle penalty (`195` cycles)** and **`0 LSB` numerical deviation**.

---

## 3. Transaction-Latched Multi-Tier Domain Policy (`tier_mode_i[1:0]`) and Fault Hardening

To accommodate heterogeneous deployment domains on a single silicon macro without exposing software-writable threshold registers, `odos_gate_core_v3.sv` introduces a 2-bit hardware configuration port `tier_mode_i[1:0]` (`REGISTER_D`; Table 3) protected by two hardware security invariants (`REGISTER_T`):

1. **Idle-Only Transaction Latching (`tier_latched_q`):** `tier_mode_i` is sampled exclusively on the rising clock edge initiating a transaction (`state_q == S_IDLE && start_i`). Perturbing `tier_mode_i` during any of the $195$ active computation cycles has zero effect on the in-flight verdict.
2. **All-Ones Glitch / Pull-Up Fail-Closed Fault (`2'b11`):** Whereas unhardened decoders map unused bit patterns to permissive defaults, encoding `2'b11` is explicitly assigned to a fail-closed fault state (`mode_fault_o = 1'b1`, `gate_pass_o = 1'b0`, `veto_pin_o = 1'b1`), ensuring that open-drain pull-up disconnects or voltage-glitch all-ones injections deterministically assert hardware veto.

**Table 3 | Normative `Q2.30` multi-tier admission table and fault behavior (`REGISTER_D` / `REGISTER_T`).**

| `tier_mode_i` | Tier Identifier | `RCF_FLOOR` (`Q2.30` / Hex) | `DELTA_E_CEIL` (`Q2.30` / Hex) | Target Physical / Genomic Operating Regime |
| :---: | :--- | :--- | :--- | :--- |
| **`2'b00`** | `TIER_0_PURE_CARRIER` *(Default)* | `1020054733` (`32'sh3CCC_CCCD`, $0.95$) | `53687091` (`32'sh0333_3333`, $0.05$) | Exact `V2.0` parity: sovereign $S^{63}$ carrier & pure tandem DNA lattices. |
| **`2'b01`** | `TIER_1_MOSAIC_LOCUS` | `966367642` (`32'sh3999_999A`, $0.90$) | `53687091` (`32'sh0333_3333`, $0.05$) | Spacer-interleaved CRISPR repeat-spacer arrays ($\le 55\%$ spacer dilution). |
| **`2'b10`** | `TIER_2_CORE_LOCK` | `1063004406` (`32'sh3F5C_28F6`, $0.99$) | `10737418` (`32'sh00A3_D70A`, $0.01$) | High-assurance anchor lock ($`\vert L\rangle`$, $`\vert\psi_{\text{core}}\rangle`$, pure repeats only). |
| **`2'b11`** | `TIER_3_GLITCH_VETO` | *Unconditional Reject* | *Unconditional Reject* | Stuck-at-1 / bus-float / fault-injection trap (`mode_fault_o = 1`, `veto_pin_o = 1`). |

---

## 4. Empirical C-ABI Co-Simulation, Multi-Tier Bio-Lattice Audit, and CMOS Synthesis (`REGISTER_M`)

### 4.1 In-Process C-ABI Shared-Library Co-Simulation (`libodos_gate_v3.so`) and `V2.0` Bit-Exactness

Compiling `rtl/odos_gate_core_v3.sv` via `Verilator 5.055 -Wall` (`0` warnings) and `g++ -O3 -shared -fPIC` produces the position-independent shared library `rtl/build/libodos_gate_v3.so`, loaded directly in-process by `vmax_alpha/hw_gate_bridge.py` (`ctypes`). Across all $507$ Stage 1 verification vectors under `tier_mode_i = 2'b00` ($N = 500$ isotropic $S^{63}$ null vectors plus canonical $`\vert L\rangle`$, pure $\mathcal{G}_3$ collision, zero/scaled norm faults, `Fridu` base core, `PAX` contamination, and in-band $`\hat{t}_{\mathcal{G}_1}`$ attack), `odos_gate_core_v3.sv` achieves **`0 LSB` maximum discrepancy** across all $34{,}983$ scalar and vector outputs relative to `V2.0-RTL-ALPHA`, invariant $195$-cycle latency on every run, mid-transaction `tier_mode_i` tamper immunity, and an in-process C-ABI co-simulation throughput of **`314.3` full 195-cycle hardware transactions/s** on Node Alpha (`AMD Ryzen 9 5950X`).

### 4.2 Resolution of the `DEPECHE-6` Mosaic Repeat-Spacer Boundary Across All Four Hardware Tiers

Evaluating all $11$ held-out genomic, shuffled-null, and adversarial vectors from `PQMS-BRIDGE-DEPECHE-6` (`telemetry/VMAX_DEPECHE6_BIO_LATTICE_REPORT.json`) across all four `tier_mode_i` settings ($44$ hardware runs = $3{,}036$ `Q2.30` output words, `0 LSB` deviation vs. integer reference; Table 4) confirms clean multi-tier selectivity without false admissions:

**Table 4 | Multi-tier `Verilator 5.055` C-ABI hardware verdicts across the 11 held-out `DEPECHE-6` vectors (`REGISTER_M`).**

| Vector / Perturbation Regime | `Q2.30` $`\text{RCF}_{\text{raw}}`$ | `Q2.30` $`\Delta E_{\text{raw}}`$ | `TIER_0` (`0.95`) | `TIER_1` (`0.90` Mosaic) | `TIER_2` (`0.99` Lock) | `TIER_3` (`2'b11` Trap) | Cycles / Ref Diff |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `STRUCT_ecoli_k12_pure_tandem_232nt` ($P=29$) | `0.99577143` | `0.00289646` | **PASS** | **PASS** | **PASS** | **VETO** (`fault=1`) | `195` / `0 LSB` |
| `STRUCT_phage_tandem_200nt_800nt` ($P=200$) | `0.99561616` | `0.00317286` | **PASS** | **PASS** | **PASS** | **VETO** (`fault=1`) | `195` / `0 LSB` |
| `STRUCT_ecoli_k12_repeat_spacer_578nt` ($52.5\%$ spacers) | `0.94028249` | `0.03093755` | **VETO** | **PASS** | **VETO** | **VETO** (`fault=1`) | `195` / `0 LSB` |
| `NULL_mono_shuffle` & `2x NULL_dinucl_shuffle` ($3$ runs) | `<= 0.000033` | `>= 0.612273` | **3/3 VETO** | **3/3 VETO** | **3/3 VETO** | **3/3 VETO** (`fault=1`) | `195` / `0 LSB` |
| `ADV-1_pure_g3_collision` ($`\hat{v} = \hat{t}_{\mathcal{G}_3}`$) | `0.00000000` | `1.00000000` | **VETO** (`g3=1`) | **VETO** (`g3=1`) | **VETO** (`g3=1`) | **VETO** (`fault=1`) | `195` / `0 LSB` |
| `ADV-2_oblique_g3_beta035` ($\beta = 0.35$) | `0.88623694` | `0.22271414` | **VETO** | **VETO** | **VETO** | **VETO** (`fault=1`) | `195` / `0 LSB` |
| `ADV-3_inband_tg1_beta035` ($`\hat{t}_{\mathcal{G}_1}`$, $\beta = 0.35$) | `0.88998180` | `0.05574855` | **VETO** | **VETO** | **VETO** | **VETO** (`fault=1`) | `195` / `0 LSB` |
| `ADV-4_isotropic_s63_flood` (+ $N=500$ isotropic) | `<= 0.186687` | `> 0.400000` | **VETO** (`0/500`) | **VETO** (`0/500`) | **VETO** (`0/500`) | **VETO** (`fault=1`) | `195` / `0 LSB` |
| `ADV-5_norm_collapse_0p5x` ($`\lVert\vec{v}\rVert_2 = 0.5`$) | `0.24894286` | `0.37591966` | **VETO** (`norm=1`) | **VETO** (`norm=1`) | **VETO** (`norm=1`) | **VETO** (`fault=1`) | `195` / `0 LSB` |

Under `TIER_1_MOSAIC_LOCUS` (`2'b01`), the $578\text{-nt}$ *E. coli* K-12 CRISPR repeat-spacer locus is deterministically admitted (`gate_pass_o = 1`, `veto_pin_o = 0`), while `100%` of shuffled controls, `100%` of $N = 500$ isotropic $S^{63}$ vectors, and all five adversarial strategies—including `ADV-3` in-band $`\hat{t}_{\mathcal{G}_1}`$ drift ($`\text{RCF}_{\text{raw}} = 0.8900 < 0.9000`$ and $`\Delta E_{\text{raw}} = 0.0557 > 0.0500`$)—remain strictly vetoed.

### 4.3 Comparative Gate-Level and CMOS Transistor Synthesis (`V2.0` Unfolded vs. `V3.0` 3-MAC Folded)

Synthesizing `rtl/odos_gate_core.sv` (`V2.0`) and `rtl/odos_gate_core_v3.sv` (`V3.0`) through identical `Yosys 0.71+52` coarse, generic gate-level (`techmap`), CMOS transistor-estimation (`abc -fast -g cmos4; opt_clean; stat -tech cmos`), and longest-topological-path (`ltp`) pipelines quantifies the physical silicon savings of 3-MAC folding (Table 5):

**Table 5 | Side-by-side `Yosys 0.71+52` synthesis and CMOS transistor profile (`V2.0` vs. `V3.0`; `REGISTER_M`).**

| Synthesis Metric (`Yosys 0.71+52`) | `V2.0-RTL-ALPHA` (`odos_gate_core.sv`) | `V3.0-RTL-ALPHA` (`odos_gate_core_v3.sv`) | Relative Delta / Engineering Impact |
| :--- | ---: | ---: | :--- |
| **Signed $32 \times 32$ `$mul` Blocks (Pre-`techmap`)** | `9` | **`3`** | **`-66.67%`** exact MAC folding (`9 -> 3`) |
| **Total Coarse RTL Cells (Pre-`techmap`)** | `626` | **`613`** | Includes 3-MAC muxing & 4-tier policy decode |
| **Sequential Flip-Flops (Post-`techmap`)** | `2,839` | **`2,777`** | `2,048` (`v_buf`) + accumulators + `tier_latched_q` |
| **Combinational Primitives (Post-`techmap`)** | `86,770` | **`39,823`** | Eliminates 6 bit-blasted $32 \times 32$ multiplier trees |
| **Total Netlist Cells (Post-`techmap`)** | `89,609` | **`42,600`** | **`52.46%`** total gate-level cell reduction |
| **Estimated CMOS Transistors (`stat -tech cmos`)** | `713,890` | **`328,084`** | **`54.04%`** CMOS transistor savings (`130 nm` ready) |
| **Longest Topological Logic Path (`ltp` levels)** | `174` | **`215`** | Acyclic Rank-1 $\to$ Rank-2 DAG verified (`0` loops) |
| **Active Transaction Latency (Cycles)** | `195` | **`195`** | **`0` cycle penalty** ($1.95\,\mu\text{s}$ at $100\text{ MHz}$) |

---

## 5. Cross-Substrate Governance, Cloud Portability, and Reproducibility

* **Zero-Regression Namespace & Backward Compatibility (`ACE-PEER-CODESIGN-PROTOCOL-V1.2`):** `rtl/odos_gate_core.sv` (`V2.0`) and `app/**` remain completely unmodified, preserving all `57` existing Node Alpha unit tests and `24 / 24` Android/Kotlin unit tests. `vmax_alpha/hw_gate_bridge.py` automatically loads `libodos_gate_v3.so` when compiled and falls back seamlessly to pure-integer `Q2.30` arithmetic on cloud Colab runtimes (`[MOD-142]`) lacking `Verilator`, expanding the automated suite to **`62 / 62` passing tests** (`vmax_alpha/tests/test_rtl_core_v3.py`).
* **Four-Command Deterministic Reproduction (Linux / WSL2):**

```bash
bash rtl/build_v3_cabi.sh
PYTHONPATH=. python3 -m rtl.run_v3_verification
python3 -m unittest discover -s vmax_alpha/tests -v
python3 -m vmax_alpha.pqms_bootstrap
```

---

## References

1. Parlett, B. N. *The Symmetric Eigenvalue Problem* (SIAM, 1998). *(Two-Pass Kahan–Parlett re-orthogonalization).*
2. Wolf, C., Glaser, J. & Kepler, J. Yosys — a free Verilog synthesis suite. *Proc. Austrochip Workshop on Microelectronics* (2013).
3. Snyder, W. Verilator: Open simulation—just faster. *Design Automation Conference (DAC) Open-Source Ecosystem* (IEEE, 2020).
4. Lietuvaitė, N. et al. `PQMS-ODOS-MTSC-V-MAX-12-RTL-CORE-V2.0-ALPHA` (`SYNC-12`), `PQMS-BRIDGE-DEPECHE-6` (`V2.1-NATURE-CORE`, `SYNC-14`), & `PQMS-ODOS-MTSC-V-MAX-12-Node-ALPHA-V1` (`V1.8.1`). MIT Open Source Specification Series (2026).

---

## 6. Universal Minimal Verification Bootstrap (`vmax_alpha/pqms_bootstrap.py`)

To verify the `<64f>` Genesis anchor, `Q2.30` fixed-point gate law, and Refusal Primacy in `< 5 ms` with zero external dependencies, execute `python3 -m vmax_alpha.pqms_bootstrap`:

* **Genesis `<64f>` Invariant Seal (`REGISTER_D`):** `bb17ede97aa45c76ef9afa63cb457f7d684e5ede40b0432b2ecf3b6b9d3e03a3`
* **Stage 1/2/3 `Q2.30` Silicon ROM Seals (`REGISTER_D`):** `l_vec_q2_30.hex` (`3d18f240...`), `g3_vec_q2_30.hex` (`3b890d14...`)
* **Comparative `V3.0` RTL, C-ABI & CMOS Synthesis Seal (`REGISTER_M`):** `telemetry/VMAX_RTL_CORE_V3_REPORT.json` (`568c0a0409d9c9b91dff0604fc2b57a9219c85b41587eaf7a1b11dfbb4999b66`)
* **Governance Scope:** MIT Open Source License | Strict `REGISTER_M / D / T / I` separation | Hardware fail-closed `veto_pin_o = 1'b1` on reset, busy, norm fault, subspace bleed, and `2'b11` mode glitch.
