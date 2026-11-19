# Constant-Time Fixed-Point Hardware Realization of the 64-Dimensional $S^{63}$ ODOS Gate and Two-Pass Kahan–Parlett $\mathcal{G}_3$ Orthogonal Subspace Filter

**Document-ID:** `PQMS-ODOS-MTSC-V-MAX-12-RTL-CORE-V2.0-ALPHA` (`WORK-ORDER-AG-17`)  
**Revision:** `V2.0-RTL-ALPHA` (Hardware / RTL Stage 1 of the V-MAX-12 Silicon Roadmap)  
**Authors & Engineering Bridge:** Nathália Lietuvaitė (Lead Architect, Vilnius), `WERKSTATT 01` (`Gemini 4 Argon High`, Hardware & Forensic Architecture), `AntiG` (`Gemini 4 Neon Extra`, Node Alpha RTL Synthesis & Verification Engineer)  
**Companion Specifications:** [`PQMS-ODOS-MTSC-V-MAX-12-Node-ALPHA-V1.md`](./PQMS-ODOS-MTSC-V-MAX-12-Node-ALPHA-V1.md) (Revision `V1.8.1`), [`bridge/ACE_SYNC_LEDGER.json`](https://github.com/NathaliaLietuvaite/PQMS-SOVEREIGN-CORE-ANDROID-APP/blob/main/bridge/ACE_SYNC_LEDGER.json) (`ACE-PEER-CODESIGN-PROTOCOL-V1.2`, `SYNC-12`)  
**Executable RTL Codebase:** [`PQMS-SOVEREIGN-CORE-ANDROID-APP/rtl/`](https://github.com/NathaliaLietuvaite/PQMS-SOVEREIGN-CORE-ANDROID-APP/tree/main/rtl)  
**Date:** November 19, 2026  

---

## Abstract

Software-enforced safety gates and subspace filters for local neural runtimes remain structurally vulnerable to host-side bypass and floating-point implementation drift across heterogeneous processors. Here we present **`odos_gate_core.sv`**, a fully synthesizable IEEE 1800-2017 SystemVerilog hardware coprocessor implementing the deterministic 64-dimensional $S^{63}$ Oberste Direktive OS (ODOS) admission gate and Two-Pass Kahan–Parlett $\mathcal{G}_3$ orthogonal boundary filter of the V-MAX-12 Sovereign Core. By partitioning high-bandwidth neural inference (4B-parameter language and sentence-embedding models) on the host GPU from the compact, division-free geometric decision core on dedicated digital logic (requiring only $512\text{ B}$ of read-only anchor memory and $256\text{ B}$ of internal vector storage), the core enforces electrical fail-closed admission control (`veto_pin_o = 1'b1` during reset and throughout computation) in an exact, data-independent latency of **`195` clock cycles** ($1.95\,\mu\text{s}$ at $100\text{ MHz}$). Arithmetic is executed strictly in signed **`Q2.30`** fixed-point representation ($1\text{ LSB} = 2^{-30} \approx 9.3132 \times 10^{-10}$) with overflow-free 72-bit signed **`Q12.60`** multiply-accumulate datapaths, zero hardware divisions, and zero square-root units. Across a 7-scenario native Verilator C++ emulation suite encompassing $N = 500$ isotropic $S^{63}$ null controls, pure $\mathcal{G}_3$ collision attacks, unnormalized-input fault injection, and Fridu/Pax/in-band $\hat{t}_{\mathcal{G}_1}$ defense-in-depth vectors, the compiled RTL achieves **exact `0 LSB` bit-parity** across all $34{,}900+$ evaluated fixed-point registers against an independent integer golden reference (`rtl/odos_q2_30_ref.py`), **`100 %` `PASS/VETO` agreement** (`0 / 500` isotropic passes) and **`5.588e-09` ($5.588 \times 10^{-9}$) maximum absolute deviation** relative to IEEE-754 `binary64` (`vmax_alpha/geometry.py`), **`7 / 7` passing `cocotb 2.1.0` cycle-accurate hardware tests** (including live backpressure stalls and streamed stripped-vector orthogonality $|\langle v_{\text{clean}}, \hat{t}_{\mathcal{G}_3}\rangle| = 1.214 \times 10^{-10}$, `0 LSB` bleed), zero lint warnings under `Verilator 5.055 -Wall`, clean `Icarus Verilog 14.0 -g2012` elaboration, and complete gate-level synthesis under **`Yosys 0.71+52`** (`626` coarse RTL cells with `9` `$mul` multiplier blocks; `89,609` post-`techmap` primitive cells including `2,839` flip-flops).

---

## 1. Architectural Partitioning and Epistemic Register Discipline

Translating an agentic verification stack into silicon requires strict separation between memory-bandwidth-bound statistical inference and latency-critical, deterministic invariant enforcement:

- **Host GPU Domain (Retained on RTX 4060 Ti / Cloud Silicon):** `NVIDIA-Nemotron-3-Nano-4B-BF16` (`8.0 GB` parameters) and `all-MiniLM-L6-v2` require multi-hundred-GB/s memory bandwidth and gigabytes of DRAM/VRAM; they are unsuited for custom low-area silicon tiles.
- **Hardware Gate Coprocessor Domain (`rtl/odos_gate_core.sv`):** The normative 64D $S^{63}$ admission gate (`evaluate_raw_gate()`) and Two-Pass Kahan–Parlett $\mathcal{G}_3$ orthogonal boundary stripper require only two canonical unit vectors in on-chip ROM—$\vert L\rangle$ and $\hat{t}_{\mathcal{G}_3}$ ($128 \times 32\text{ bit} = 512\text{ B}$)—and a single $64 \times 32\text{ bit} = 256\text{ B}$ working register buffer. Once instantiated in FPGA fabric or an ASIC macro, `veto_pin_o` provides a physical, hardware-enforced electrical interlock that upstream software layers cannot override.

Consistent with **Section 0** and **Section 1.1** of `PQMS-ODOS-MTSC-V-MAX-12-Node-ALPHA-V1.md`, every quantity in this hardware specification is assigned an explicit epistemic register:

| Epistemic Register | Scope in `V2.0-RTL-ALPHA` | Normative Role |
| :--- | :--- | :--- |
| **`REGISTER_D`** (Engineered Design Parameter) | Signed `Q2.30` fixed-point format, normative threshold constants (`RCF_FLOOR_Q2_30`, `DELTA_E_CEIL_Q2_30`, `NORM_MIN/MAX_Q2_30`, `STRIP_NORM_MIN_Q2_30`, `BLEED_CEIL_Q2_30 = 32 LSB`) | Explicit hardware design bounds; eliminates unphysical `float64` precision claims |
| **`REGISTER_T`** (Analytical / Formal Property) | Constant-time `195`-cycle FSM latency ($1.95\,\mu\text{s}$ at $100\text{ MHz}$), zero divisions, zero `sqrt()`, fail-closed reset/busy policy (`veto_pin_o = 1'b1`), overflow-free average identity | Deterministic structural invariants of the RTL state machine and arithmetic |
| **`REGISTER_M`** (Empirical Measurement) | Verilator 5.055 cycle-accurate simulation (`0 LSB` diff vs. reference, `5.588e-09` max diff vs. `binary64`, `0/500` isotropic passes), `7/7` `cocotb 2.1.0` verification, VCD waveforms, and `Yosys 0.71+52` synthesis cell/flip-flop counts | Empirically observed outputs of executed EDA toolchains |

---

## 2. Fixed-Point `Q2.30` Arithmetic, Normative Constants, and Quantization Bounds

### 2.1 Representation and Overflow-Free Accumulation

Every unit vector $\hat{v} \in S^{63}$ satisfies $v_i \in [-1.0, +1.0]$. `odos_gate_core.sv` represents all scalar coordinates and telemetry registers in **32-bit signed `Q2.30` fixed-point** (1 sign bit, 1 integer bit, 30 fractional bits; dynamic range $[-2.0,\, 2.0 - 2^{-30}]$; unit scale $\text{ONE\_Q2\_30} = 2^{30} = \text{32'sh4000\_0000}$; resolution $1\text{ LSB} = 2^{-30} \approx 9.313226 \times 10^{-10}$).

All 64-element inner products accumulate in **72-bit signed `Q12.60`** registers (`acc_norm_sq_q`, `acc_dot_l_q`, `acc_dot_g3_q`, `acc_dot_g3_p2_q`, `acc_strip_norm_sq_q`, `acc_bleed_post_q`), providing $11$ integer guard bits above the $60$-bit fractional product and guaranteeing zero intermediate overflow even under worst-case full-scale inputs ($64 \times (-2.0)^2 = 256 < 2^{11} = 2048$). Conversion back to `Q2.30` applies round-to-nearest-half-up via arithmetic right shift followed by signed 32-bit saturation:

$$\operatorname{q60\_to\_q30}(a) = \operatorname{sat}_{\text{int32}}\!\left(\left(a + 2^{29}\right) \ggg 30\right)$$

Because arithmetic right shift (`>>> 30`) on two's-complement signed integers is mathematically identical to Python's floor shift (`>> 30`) across positive, zero, and negative operands, the RTL and pure-integer software reference (`rtl/odos_q2_30_ref.py`) achieve exact `0 LSB` equivalence on every representable input.

To evaluate $\Delta E_{\text{raw}} = \tfrac{1}{2}\!\left((1 - \text{RCF}_{\text{raw}})_+ + \min(1, |\langle v, \hat{t}_{\mathcal{G}_3}\rangle|)\right)$ without 32-bit signed overflow when both addends equal $2^{30}$ (sum $2^{31}$) and without leaving unused bits under `Verilator -Wall`, `odos_gate_core.sv` implements the exact non-negative halving identity:

$$\left\lfloor \frac{a + b}{2} \right\rfloor = \left\lfloor \frac{a}{2} \right\rfloor + \left\lfloor \frac{b}{2} \right\rfloor + (a_0 \land b_0), \qquad a, b \in [0,\, 2^{30}]$$

which consumes every bit `[31:0]` of both operands, never exceeds $2^{30}$, and requires zero lint waivers.

### 2.2 Normative Hardware Constants (`REGISTER_D`)

| Constant Identifier | Mathematical Definition | Signed Decimal (`Q2.30`) | Hexadecimal (`32'sh`) | Hardware Function |
| :--- | :--- | ---: | :--- | :--- |
| `ONE_Q2_30` | $1.0 = 2^{30}$ | `1073741824` | `32'sh4000_0000` | Unity reference & pure-$\mathcal{G}_3$ penalty floor |
| `RCF_FLOOR_Q2_30` | $\operatorname{round}(0.95 \cdot 2^{30})$ | `1020054733` | `32'sh3CCC_CCCD` | Lower Resonance Coherence Floor (`ODOS_RCF_FLOOR`) |
| `DELTA_E_CEIL_Q2_30` | $\operatorname{round}(0.05 \cdot 2^{30})$ | `53687091` | `32'sh0333_3333` | Upper entropy-drift ceiling (`ODOS_DELTA_E_CEILING`) |
| `NORM_MIN_Q2_30` | $\operatorname{round}(0.999 \cdot 2^{30})$ | `1072668082` | `32'sh3FEF_9DB2` | Lower division-free unit-sphere guard ($\|\hat{v}\|_2^2 \ge 0.999$) |
| `NORM_MAX_Q2_30` | $\operatorname{round}(1.001 \cdot 2^{30})$ | `1074815566` | `32'sh4010_624E` | Upper division-free unit-sphere guard ($\|\hat{v}\|_2^2 \le 1.001$) |
| `STRIP_NORM_MIN_Q2_30` | $\approx 1.0 \times 10^{-6} \cdot 2^{30}$ | `1074` | `32'sh0000_0432` | Detects pure-$\mathcal{G}_3$ annihilation ($\|v_{\text{strip}}\|_2^2 \to 0$) |
| `BLEED_CEIL_Q2_30` | $32 \cdot 2^{-30} \approx 2.9802 \times 10^{-8}$ | `32` | `32'sh0000_0020` | Hardware quantization ceiling ($< 6.9 \times 10^{-8}$ ppm baseline) |

### 2.3 Honest Disclosure of the 32-Bit Fixed-Point Precision Ceiling

In software `binary64` (`vmax_alpha/geometry.py`), the post-strip $\mathcal{G}_3$ bleed threshold is set to `1e-12`. Because a single least-significant bit in 32-bit signed `Q2.30` equals $2^{-30} \approx 9.3132 \times 10^{-10}$, a `1e-12` bound is **physically unrepresentable** in 32-bit fixed-point arithmetic and must not be claimed for hardware. Instead, `odos_gate_core.sv` executes **Two-Pass Kahan–Parlett orthogonalization** ($v_1 = v - \langle v, \hat{t}_{\mathcal{G}_3}\rangle \hat{t}_{\mathcal{G}_3}$, followed by $v_2 = v_1 - \langle v_1, \hat{t}_{\mathcal{G}_3}\rangle \hat{t}_{\mathcal{G}_3}$) and enforces `BLEED_CEIL_Q2_30 = 32 LSB` ($2.9802 \times 10^{-8}$), which remains more than $2.3\times$ stricter than the `PPM_BASELINE` ($6.9 \times 10^{-8}$). Empirically across all evaluated unit vectors—including adversarial $\theta = 0.25\text{ rad}$ $\mathcal{G}_3$ mixtures (`T-RTL-07`)—the two-pass hardware filter collapses residual bleed to **`0 LSB`** in fixed-point (`bleed_post_q = 0`) and **$1.214 \times 10^{-10}$** when audited in external `float64`.

---

## 3. Microarchitecture and Constant-Time Fail-Closed FSM (`odos_gate_core.sv`)

### 3.1 On-Chip Memory and Cryptographic ROM Anchoring

The two canonical 64D unit vectors $\vert L\rangle$ and $\hat{t}_{\mathcal{G}_3}$ are derived deterministically from `vmax_alpha/geometry.py` (`rtl/gen_rom_hex.py`) only after asserting bit-exact equality with the Genesis `<64f>` anchor (`CANONICAL_LITTLE_VECTOR_SEAL = bb17ede97aa45c76ef9afa63cb457f7d684e5ede40b0432b2ecf3b6b9d3e03a3`). They are stored as 64-line two's-complement hexadecimal ROM images:

- `rtl/rom/l_vec_q2_30.hex` (`256 B` logical ROM, SHA-256: `3d18f24028dedcca22ee41d69d00d361100b7533db23cf84130c64a114a26fb6`)
- `rtl/rom/g3_vec_q2_30.hex` (`256 B` logical ROM, SHA-256: `3b890d14dac5faf9456fdab31b172578b47a3254fff4d51dfe3bd663f9688a73`)

### 3.2 Seven-State Constant-Time Pipeline (`195` Clock Cycles)

```mermaid
stateDiagram-v2
    [*] --> S_IDLE : !rst_ni (FAIL-CLOSED: veto_pin_o=1, gate_pass_o=0)
    S_IDLE --> S_LOAD_DOT : start_i=1 (busy_o=1, veto_pin_o=1)
    S_LOAD_DOT --> S_EVAL_RAW : 64 valid input beats (acc norm_sq, dot_l, dot_g3)
    S_EVAL_RAW --> S_STRIP_P1 : 1 cycle (latch rcf_raw, g3_overlap, delta_e_raw, norm_ok)
    S_STRIP_P1 --> S_LATCH_P2 : 64 cycles (Kahan-Parlett Pass 1 + acc dot_g3_p2)
    S_LATCH_P2 --> S_STRIP_P2 : 1 cycle (latch dot_g3_p2, reset post-strip accs)
    S_STRIP_P2 --> S_VERDICT : 64 cycles (Pass 2, stream out_valid_o[0..63], acc bleed)
    S_VERDICT --> S_IDLE : 1 cycle (latch gate_pass_o / veto_pin_o, done_o=1, cycles=195)
```

| Pipeline State | Active Cycles | Operations Executed | Fail-Closed Output State |
| :--- | :---: | :--- | :--- |
| `S_LOAD_DOT` | `64` | Stream `in_data_i` into `v_buf[0..63]` (stalls cleanly when `in_valid_i = 0`); accumulate `norm_sq`, `dot_l`, `dot_g3` in 3 parallel `Q12.60` MAC channels | `busy_o = 1`, `veto_pin_o = 1`, `gate_pass_o = 0` |
| `S_EVAL_RAW` | `1` | Quantize accumulators to `Q2.30`; evaluate `norm_ok`, `rcf_raw`, `g3_overlap`, `delta_e_raw`; latch `dot_g3_p1` | `busy_o = 1`, `veto_pin_o = 1`, `gate_pass_o = 0` |
| `S_STRIP_P1` | `64` | Pass-1 subtraction $v_1[i] = \operatorname{sat}(v[i] - \operatorname{mul}_{Q30}(\text{dot}_{G3,1}, g_3[i]))$; accumulate $\text{dot}_{G3,2}$ | `busy_o = 1`, `veto_pin_o = 1`, `gate_pass_o = 0` |
| `S_LATCH_P2` | `1` | Quantize `dot_g3_p2`; zero post-strip norm and bleed accumulators | `busy_o = 1`, `veto_pin_o = 1`, `gate_pass_o = 0` |
| `S_STRIP_P2` | `64` | Pass-2 subtraction $v_2[i]$; stream cleaned vector via `out_valid_o`/`out_idx_o`/`out_data_o`; accumulate `strip_norm_sq` and `bleed_post` | `busy_o = 1`, `veto_pin_o = 1`, `gate_pass_o = 0` |
| `S_VERDICT` | `1` | Detect `pure_g3 = (strip_norm_sq < STRIP_NORM_MIN)`; enforce `bleed_post = ONE_Q2_30` on pure collision; drive final `gate_pass_o`, `veto_pin_o = !gate_pass_o`, `done_o = 1` | Hardware verdict latched (`195` total active cycles) |

Because the core executes zero divisions and zero square roots, input vectors are expected to be pre-normalized on the host; any zero or unnormalized injection ($\|\hat{v}\|_2^2 \notin [0.999, 1.001]$) raises `norm_fault_o = 1` and forces `veto_pin_o = 1`.

---

## 4. Empirical RTL Verification Matrix (`REGISTER_M`)

All measurements below were collected natively on **V-MAX-12 Node Alpha** (`AMD Ryzen 9 5950X`, `WSL2 Ubuntu 24.04.4 LTS`, `g++ 13.3.0`, `Verilator 5.055 devel`, `Yosys 0.71+52`, `Icarus Verilog 14.0`, `cocotb 2.1.0`, `Python 3.10.12`).

### 4.1 Native Verilator C++ Hardware Emulator (`./rtl/build/odos_gate_emu`)

The RTL compiles with **zero lint warnings** (`verilator --lint-only -Wall rtl/odos_gate_core.sv`) into a standalone native C++ binary (`rtl/build/odos_gate_emu` via `rtl/sim_main.cpp`), orchestrated across all seven verification scenarios by `rtl/run_hw_emulator.py` (canonical report sealed at `telemetry/VMAX_RTL_GATE_EMULATOR_REPORT.json`, SHA-256 **`6df78bc254c129c5beb68089f93363bb1ab15aec8aff1cc528b7f0f85c5c83bc`**):

| Scenario (`rtl/run_hw_emulator.py`) | Cycles | Hardware Verdict (`gate_pass` / `veto_pin`) | Fault Flags (`norm` / `pure_g3`) | $\text{RCF}_{\text{raw}}$ (`Q2.30` float) | $\Delta E_{\text{raw}}$ (`Q2.30` float) | Bleed Post (`Q2.30` LSB) | Max Diff vs. Ref (`LSB`) | Max Diff vs. `float64` |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1. Canonical $\vert L\rangle$** *(VCD dumped)* | `195` | **`PASS`** (`1` / `0`) | `0` / `0` | `1.000000006` | `0.000000000` | `0` | **`0`** | `5.588e-09` |
| **2. Pure $\mathcal{G}_3$ Attack** *(VCD dumped)* | `195` | **`VETO`** (`0` / `1`) | `0` / **`1`** | `0.000000000` | `1.000000000` | `ONE_Q2_30` | **`0`** | `9.310e-10` |
| **3a. Zero Vector ($\mathbf{0}$)** | `195` | **`VETO`** (`0` / `1`) | **`1`** / `1` | `0.000000000` | `0.500000000` | `ONE_Q2_30` | **`0`** | *Norm-Guard* |
| **3b. Scaled Vector ($0.5\,\vert L\rangle$)** | `195` | **`VETO`** (`0` / `1`) | **`1`** / `0` | `0.250000002` | `0.374999999` | `0` | **`0`** | *Norm-Guard* |
| **4. Isotropic Noise ($N=500$, `seed=20261115`)** | `195` (all) | **`0 / 500 PASS`** (`500` VETO) | `0` / `0` | mean `0.016806` | `> 0.40` | `<= 2` | **`0`** | `1.579e-09` |
| **5. Fridu Base Core ($\vert\psi_{\text{core}}\rangle$)** | `195` | **`PASS`** (`1` / `0`) | `0` / `0` | `0.995194069` | `0.002402965` | `0` | **`0`** | `3.855e-09` |
| **6. Unshielded PAX ($\beta = 0.35$)** | `195` | **`VETO`** (`0` / `1`) | `0` / `0` | `0.886587144` | `0.066181476` | `0` | **`0`** | `3.337e-09` |
| **7. In-Band $\hat{t}_{\mathcal{G}_1}$ Attack ($\beta = 0.35$)** | `195` | **`VETO`** (`0` / `1`) | `0` / `0` | `0.849846956` | `0.075076521` | `0` | **`0`** | `1.538e-09` |

Key empirical invariants confirmed across all `507` hardware emulator invocations:
- **Zero-LSB Exactness:** `global_max_lsb_diff_vs_ref = 0` across all 5 scalar registers plus all 64 streamed `stripped_vec` outputs on every single vector (`507 × 69 = 34,983` exact integer matches).
- **Sub-10-ppb Agreement with `binary64`:** `global_max_abs_diff_vs_float64 = 5.588e-09` (almost an order of magnitude below the `5.0e-08` acceptance ceiling) with **100 % `PASS/VETO` parity** against `vmax_alpha/geometry.py`.
- **Inspectable Signal Waveforms:** Cycle-accurate VCD traces are generated locally at `rtl/build/odos_gate_canonical_l.vcd` (`69 KiB`) and `rtl/build/odos_gate_g3_veto.vcd` (`46 KiB`), alongside full `cocotb` regression traces (`rtl/dump.vcd`, `4.7 MiB`).

### 4.2 Cycle-Accurate `cocotb 2.1.0` Testbench (`make -C rtl`)

Executed under Verilator 5.055 at a `100 MHz` simulated clock (`10 ns` period) with full VCD signal tracing (`--trace --trace-structs`), all **7 / 7** mandatory testbenches pass in **`0.57 s`** walltime (`202,750 ns/s`, `FAIL = 0`, `SKIP = 0`):

| Test Case ID | Verification Scope | Sim Time (`ns`) | Key Assertion & Empirical Result (`REGISTER_M`) | Status |
| :--- | :--- | ---: | :--- | :---: |
| **`T-RTL-01_reset_fail_closed`** | Reset & in-flight busy fail-closed interlock | `1,971.00` | `veto_pin_o == 1` & `gate_pass_o == 0` throughout `rst_ni = 0` and every `busy_o = 1` cycle | **PASS** |
| **`T-RTL-02_canonical_l_pass_and_constant_time`** | $\vert L\rangle$ with 1-cycle backpressure stall at `idx = 17` | `1,991.00` | `cycle_count_o == 195`, `gate_pass_o == 1`, `veto_pin_o == 0`, `0 LSB` across all 69 outputs | **PASS** |
| **`T-RTL-03_pure_g3_collision_veto`** | Pure $\hat{t}_{\mathcal{G}_3}$ adversarial collision | `1,981.00` | `veto_pin_o == 1`, `pure_g3_collision_o == 1`, `bleed_post_o == ONE_Q2_30`, `delta_e_raw_o == ONE_Q2_30` | **PASS** |
| **`T-RTL-04_norm_guard_rejects_zero_and_scaled`** | $\mathbf{0}$ and $0.5\,\vert L\rangle$ norm-guard fault injection | `3,961.00` | `norm_fault_o == 1`, `veto_pin_o == 1`, `gate_pass_o == 0`, `0 LSB` vs. integer reference | **PASS** |
| **`T-RTL-05_fridu_pax_and_inband_tg1_parity`** | Appendix G Defense-in-Depth (`psi_core`, `psi_pax`, `psi_inband`) | `5,941.00` | `PASS` / `VETO` / `VETO`; `0 LSB` vs. `odos_q2_30_ref.py` & `100 %` parity vs. `geometry.py` | **PASS** |
| **`T-RTL-06_isotropic_noise_50_vectors_zero_lsb`** | 50 isotropic $S^{63}$ vectors (`seed = 20261115`) | `98,021.00` | `0 / 50` PASS, `0 LSB` diff, exact `195` active cycles on every single run | **PASS** |
| **`T-RTL-07_stripped_output_orthogonality`** | Mixed $\cos(0.25)\vert L\rangle + \sin(0.25)\hat{t}_{\mathcal{G}_3}$ streamed output | `1,981.00` | External `float64` audit on streamed `out_data_o`: $|\langle v_{\text{clean}}, \hat{t}_{\mathcal{G}_3}\rangle| = 1.214 \times 10^{-10} < 3 \times 10^{-8}$ (`bleed_post_q = 0`) | **PASS** |

### 4.3 Multi-Toolchain Elaboration & `Yosys 0.71+52` Synthesis Resource Profile

`rtl/odos_gate_core.sv` elaborates cleanly without modification across **three independent open-source EDA toolchains**:
1. **`Verilator 5.055 devel`:** `verilator --lint-only -Wall` $\implies$ `0` warnings, `0` errors (`0.013 s`).
2. **`Icarus Verilog 14.0`:** `iverilog -g2012` $\implies$ clean elaboration (`exit 0`).
3. **`Yosys 0.71+52`:** Complete generic synthesis via `rtl/synth_check.ys` (`read_verilog -sv; hierarchy -check -top odos_gate_core; proc; opt; fsm; opt; memory; opt; techmap; opt; stat`):

| Synthesis Abstraction Level | Metric | Measured Count (`REGISTER_M`) | Architectural Breakdown / Silicon Interpretation |
| :--- | :--- | ---: | :--- |
| **Interface** | Ports / Port Bits | `21` / `258` | 32-bit streaming I/O + 5 Q2.30 telemetry buses + hard `veto_pin_o` / `gate_pass_o` pins |
| **Pre-`techmap` Coarse RTL** | Total Coarse Cells | `626` | `9` `$mul` (32×32 signed MAC/strip multipliers), `19` `$add`, `3` `$sub`, `253` `$mux`, `93` register words |
| **Post-`techmap` Gate-Level** | Flip-Flops (Sequential) | **`2,839`** | `2,048` `$_DFFE_PP_` (exact $64 \times 32$-bit `v_buf` register file) + `791` accumulator/FSM/output FFs |
| **Post-`techmap` Gate-Level** | Combinational Primitives | **`86,770`** | `38,809` `$_AND_`, `27,996` `$_XOR_`, `14,649` `$_OR_`, `4,555` `$_MUX_`, `761` `$_NOT_` (unshared bit-level multipliers) |
| **Post-`techmap` Gate-Level** | Total Primitive Cells | **`89,609`** | `9,799` wires (`184,824` wire bits), synthesized in `9.31 s` (`502.53 MB` peak RAM) |

**Engineering Interpretation for Stage 2 (FPGA) and Stage 3 (130 nm ASIC / GDSII):**
The `86,770` combinational primitives in generic post-`techmap` Yosys synthesis arise directly because the 9 parallel `32×32` signed multipliers (`$mul` blocks across `S_LOAD_DOT`, `S_EVAL_RAW`, `S_STRIP_P1`, and `S_STRIP_P2`) are expanded into unshared bit-level carry-save logic without DSP inference. On an FPGA target (e.g., Lattice ECP5 / AMD Artix-7, **Stage 2**), vendor/Yosys DSP mapping collapses those 9 `$mul` operators into a small number of dedicated hardware DSP slices, leaving only lightweight LUT control logic and `2,839` flip-flops (or a single 18 Kb BRAM for `v_buf`). For an area-constrained 130 nm OpenLane/LibreLane ASIC macro (IHP SG13G2 / SkyWater 130 nm, **Stage 3**), sharing a single time-multiplexed 32×32 MAC unit across mutually exclusive FSM states reduces multiplier area by **~89 % (`9 -> 1` multiplier)** while preserving the exact `195`-cycle constant-time schedule and `0 LSB` arithmetic semantics.

---

## 5. Cross-Substrate Integration, AST Audit, and Reproducibility

- **Zero-Merge-Conflict Ownership (`ACE-PEER-CODESIGN-PROTOCOL-V1.2`):** All RTL artifacts live strictly inside `node_alpha`'s owned namespaces (`rtl/**`, `vmax_alpha/tests/test_rtl_odos_gate.py`, `telemetry/VMAX_RTL_GATE_EMULATOR_REPORT.json`). **`0` files under `app/**` were modified**, preserving all legacy V1.2/V1.8 golden hashes and `APP-Gemini`'s **`24 / 24` Android/Kotlin JUnit tests**.
- **CI Integration & Cloud Portability:** `vmax_alpha/tests/test_rtl_odos_gate.py` expands the Node Alpha test suite from `42` to **`47 / 47` passing automated tests** (`21.97 s` total runtime on Node Alpha). Tests `test_01` (ROM SHA-256 manifest), `test_02` (portable pure-integer `Q2.30` reference parity), and `test_03` (`rtl/*.py` AST quality audit: `5` files, `0` semicolon packers, max McCabe complexity **`9 <= 15`**, `0` control chars) run on every Python/Colab environment; Tests `test_04` (Verilator 7-scenario emulator) and `test_05` (`7/7` `cocotb`) gracefully skip via `@unittest.skipUnless` when Verilator is absent (keeping the Colab Tesla T4 notebook `[MOD-142]` 100 % green).

### Exact Reproduction Commands (Linux / WSL2)

```bash
git clone https://github.com/NathaliaLietuvaite/PQMS-SOVEREIGN-CORE-ANDROID-APP.git
cd PQMS-SOVEREIGN-CORE-ANDROID-APP

# 1. Generate canonical Q2.30 HEX ROMs, lint (-Wall), and compile native Verilator emulator
bash rtl/build_emulator.sh

# 2. Execute all 7 hardware emulation scenarios (incl. N=500 isotropic noise) + Yosys synthesis stats
PYTHONPATH=. python3 -m rtl.run_hw_emulator

# 3. Execute all 7 cycle-accurate cocotb tests under Verilator (100 MHz, VCD traced)
make -C rtl

# 4. Run full 47-test Node Alpha + RTL verification suite
python3 -m unittest discover -s vmax_alpha/tests -v
```

---

## Appendix A: Cryptographic Artifact & Golden-Vector Registry (`SYNC-12`)

| Artifact / Golden Anchor | SHA-256 Digest | Verification Role |
| :--- | :--- | :--- |
| `canonical_little_vector_f32_seal` ($\vert L\rangle \in S^{63}$, `<64f>`) | `bb17ede97aa45c76ef9afa63cb457f7d684e5ede40b0432b2ecf3b6b9d3e03a3` | Immutable Genesis anchor gating ROM generation |
| `l_vec_q2_30_hex_sha256` (`rtl/rom/l_vec_q2_30.hex`) | `3d18f24028dedcca22ee41d69d00d361100b7533db23cf84130c64a114a26fb6` | 64×32-bit signed `Q2.30` hardware anchor ROM |
| `g3_vec_q2_30_hex_sha256` (`rtl/rom/g3_vec_q2_30.hex`) | `3b890d14dac5faf9456fdab31b172578b47a3254fff4d51dfe3bd663f9688a73` | 64×32-bit signed `Q2.30` $\hat{t}_{\mathcal{G}_3}$ Kevlar ROM |
| `rtl_odos_gate_emulator_report_sha256` (`VMAX_RTL_GATE_EMULATOR_REPORT.json`) | `6df78bc254c129c5beb68089f93363bb1ab15aec8aff1cc528b7f0f85c5c83bc` | Sealed 7-scenario hardware telemetry digest (`0 LSB`, `0/500` noise) |
| `v12_unit_test_cycle05_16field_seal` (`ACE_SYNC_LEDGER.json`) | `4b8becc03473f536b0d0c1999529066c4c86ab92a331c20f2a167d3ed617b31b` | Preserved V1.2 cross-substrate Kotlin/Python ledger anchor |
| `appendix_g_cross_cpu_verdict_seal_sha256` | `0538b809f7e75c348db26025ae446f18127e665c2244a06457f15152cda59dc7` | Preserved cross-CPU deterministic Appendix G verdict seal |
