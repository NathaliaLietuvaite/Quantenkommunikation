# Full RTL-to-GDSII `130 nm` CMOS Physical Implementation, Collision-Free Single-Port SRAM Banking, and Two-Stage MAC Pipelining for 64-Dimensional $S^{63}$ Silicon Interlocks

**Document ID:** `PQMS-ODOS-MTSC-V-MAX-12-RTL-CORE-V4.0-GDSII` — Revision `V4.0-GDSII` (`WORK-ORDER-AG-22` / `SYNC-17`, Silicon Roadmap Stage 3 Physical Signoff)  
**Authors:** Nathália Lietuvaitė (Lead Architect, Vilnius), `WERKSTATT 01` & Carbon High Review (VLSI Physical Architecture, SRAM Banking & Timing Closure), `AntiG` (`Gemini 4 Neon Extra`, Node Alpha `IHP SG13G2` Synthesis, `OpenROAD`/`OpenSTA` Place-and-Route & C-ABI Verification)  
**Companion Specifications & Sealed Artifacts:** [`PQMS-ODOS-MTSC-V-MAX-12-RTL-CORE-V3.0-ALPHA.md`](./PQMS-ODOS-MTSC-V-MAX-12-RTL-CORE-V3.0-ALPHA.md) (`V3.1-RTL-OPTIMUM`, `SYNC-16`), [`PQMS-ODOS-MTSC-V-MAX-12-RTL-CORE-V2.0-ALPHA.md`](./PQMS-ODOS-MTSC-V-MAX-12-RTL-CORE-V2.0-ALPHA.md) (`V2.0-RTL-ALPHA`, `SYNC-12`), [`PQMS-BRIDGE-DEPECHE-6.md`](./PQMS-BRIDGE-DEPECHE-6.md) (`V2.1-NATURE-CORE`, `SYNC-14`), `rtl/odos_gate_core_v4.sv`, `rtl/odos_sram_64x32_1p.sv`, [`assets/images/V-MAX-12-RTL-V4-SG13G2-DIESHOT.png`](./assets/images/V-MAX-12-RTL-V4-SG13G2-DIESHOT.png), and `telemetry/VMAX_RTL_CORE_V4_GDSII_REPORT.json` (`SHA-256: 48ccc59ab54b538537525c5b54906e14d7e52a95259064f6acc03278e21f49c4`)  
**Date:** 20 November 2026  
**License:** MIT Open Source License  

---

## Abstract

Gate-count reductions in technology-independent register-transfer-level (RTL) synthesis do not translate automatically into compact, high-speed silicon until sequential storage overhead, interconnect RC parasitics, clock-tree skew, and arithmetic carry chains are closed against a physical foundry process design kit (PDK). Although our Stage 2 coprocessor (`odos_gate_core_v3.sv`, `V3.1-RTL-OPTIMUM`) folded nine signed $32 \times 32$-bit multipliers onto three shared channels—reducing estimated CMOS transistor count by $53.14\%$ ($334{,}564$ transistors; $83.64\text{ kGE}$) and generic logic depth to $142$ levels—two physical bottlenecks persisted: $71.33\%$ of all sequential registers ($2{,}048$ of $2{,}871$ flip-flops) remained dedicated to a discrete working-vector array (`v_buf[0:63]`), and each $32 \times 32$-bit multiplier drove a 72-bit `Q12.60` accumulator and `Q2.30` saturation rounder within a single clock period. Here we report `odos_gate_core_v4.sv` (`V4.0-GDSII`), a complete RTL-to-GDSII physical implementation targeting the open-source `130 nm` IHP `SG13G2` CMOS PDK (`1.20 V`, `25 °C`). Packing adjacent 32-bit `Q2.30` coordinates into 64-bit double-words and interleaving odd-cycle reads against even-cycle writes maps the entire working buffer onto a single-port (`1P`) synchronous $64 \times 64$-bit foundry SRAM macro (`RM_IHPSG13_1P_64x64_c2_bm_bist`) with zero port collisions, eliminating all $2{,}048$ buffer flip-flops and reducing standard-cell sequential state from $2{,}871$ to `953` flip-flops (`-66.81%` versus `V3.1`). Simultaneously, inserting dedicated 64-bit multiplier product registers, pre-fetched ROM operand latches, Radix-4 Booth/carry-save multipliers, and Kogge–Stone parallel-prefix adders with $2^{29}$-pre-biased accumulators compresses generic topological depth from $142$ to `73` levels (`-48.59%`). The resulting 11-state pipeline executes in a strictly data-independent latency of $200$ clock cycles (`+5` deterministic drain cycles) with `0 LSB` numerical divergence across all $551$ hardware verification runs ($38{,}019$ fixed-point words). Full floorplanning, `TritonCTS` clock-tree synthesis, global and detailed routing (`0` `OpenROAD` router DRC violations), `OpenRCX` parasitic SPEF extraction, and post-route `OpenSTA` signoff yield a `940.0 µm × 840.0 µm` (`0.7896 mm²`) die macro (`0.708 mm²` core placement area; `0.419 mm²` instance area; `59.0%` core utilization). At the `100.0 MHz` signoff clock (`2.000 µs` latency), vectorless post-route `OpenSTA` establishes a conservative upper-bound power envelope of `858.79 mW` (`1,717.58 nJ/decision`, `8.36 µW` static leakage), while positive setup slack (`+0.3945 ns`) closes physical timing up to $f_{\max} = 104.11\text{ MHz}$ (`1.921 µs` wall-clock latency—`1.02x` faster than $100\text{ MHz}$ `V3.1`), sealed as a merged `GDSII` stream (`SHA-256: be61b9c763ff43befb42562cd26db29f9d567694b8d681c646f7b403aa1842ec`).

---

## 1. From Generic Gate Counts to Foundry Silicon Closure (`130 nm` IHP `SG13G2`)

Across Revisions `V2.0-RTL-ALPHA` (`SYNC-12`) and `V3.1-RTL-OPTIMUM` (`SYNC-16`), our 64-dimensional unit-hypersphere ($S^{63}$) admission coprocessor progressed from unfolded behavioral synthesis ($89{,}609$ generic cells, $713{,}890$ estimated transistors, $174$ logic levels) to cutset-pipelined 3-MAC resource sharing ($43{,}368$ generic cells, $334{,}564$ estimated transistors, $142$ logic levels, `23,985.0 tx/s` in-process C-ABI co-simulation). Transitioning from technology-independent `Yosys` netlists to routed `130 nm` silicon in the European open-source `IHP SG13G2` CMOS process (`1.20 V` nominal `sg13g2_stdcell` and `sg13g2_sram`) confronts two physical VLSI constraints:

1. **Sequential Register Area and Clock-Tree Capacitance:** In `V3.1`, $2{,}048$ of the $2{,}871$ flip-flops ($71.33\%$) implemented the $64 \times 32$-bit working vector `v_buf[0:63]`, requiring wide 64:1 read multiplexers, 64 write-enable decoders, and $2{,}048$ leaf sinks on the clock distribution network. Consolidating this storage into a dense foundry 6T-SRAM bitcell array markedly reduces sequential cell area and clock-tree capacitance, provided single-port (`1P`) read/write contention during in-place Kahan–Parlett Pass-1 deflation is resolved without stall cycles.
2. **Multiplier-to-Accumulator Critical-Path Delay:** Even after eliminating inter-multiplier chaining in `V3.1` (`ltp = 142`), cascading a signed $32 \times 32 \to 64$-bit multiplier directly into a 72-bit carry-propagate accumulator and 32-bit saturating rounder within a single clock period bounds maximum operating frequency ($f_{\max}$) once physical wire RC parasitics and setup/skew margins are annotated.

To maintain strict metrological accountability across design abstraction layers, every parameter, structural theorem, and post-route silicon metric in `V4.0-GDSII` is bound to an explicit epistemic register (Table 1).

**Table 1 | Epistemic register taxonomy governing `V4.0-GDSII` (`SYNC-17`).**

| Epistemic Register | Architectural Scope in `V4.0-GDSII` | Normative Metrological Boundary |
| :--- | :--- | :--- |
| **`REGISTER_D`** *(Engineered Constant)* | Four-tier `Q2.30` admission thresholds (`2'b00` $0.95$, `2'b01` $0.90$, `2'b10` $0.99$, `2'b11` glitch fault), `512 B` ROM seals (`3d18f240...`, `3b890d14...`), and `IHP SG13G2` PVT corner (`1.20 V`, `25 °C` nominal). | Fixes quantized hardware thresholds and target foundry corner; preserves `100%` policy compatibility with `V3.1`. |
| **`REGISTER_T`** *(Formal RTL Invariant)* | Parity-orthogonal 64-bit paired-word `1P` SRAM schedule (`0` R/W collisions), 64-bit `m*_prod_q` MAC product cutset, causal `+5`-cycle pipeline drain (`200` invariant cycles), and `0 LSB` `Q2.30` equivalence. | Guarantees absence of SRAM port collisions, data-dependent timing side channels, and arithmetic drift relative to `V2.0`/`V3.1`. |
| **`REGISTER_M`** *(Empirical Signoff)* | `Yosys` Liberty synthesis (`sg13g2_stdcell_typ_1p20V_25C.lib`), `OpenROAD` floorplan/CTS/routing wirelength & area, post-route `OpenRCX`/`OpenSTA` slack, $f_{\max}$, vectorless power (`µW`/`mW`), `GDSII` digest, and `Verilator` C-ABI parity. | Extracted programmatically from deterministic EDA signoff runs and sealed in `telemetry/VMAX_RTL_CORE_V4_GDSII_REPORT.json`. |
| **`REGISTER_I`** *(Unbuilt Horizon)* | External multi-project wafer (MPW) shuttle fabrication (e.g., TinyTapeout / Europractice IHP `SG13G2` silicon run) and `QMK-RVC-V7` wet-lab devices. | Pre-submission `GDSII` macro routed and verified in `OpenROAD`; padframe integration, full-foundry `KLayout`/`Magic` DRC+LVS, and physical wafer return remain future steps. |

---

## 2. Microarchitecture of `odos_gate_core_v4.sv`: Paired-Word `1P` SRAM Banking and Two-Stage MAC Cutset

### 2.1 Collision-Free Paired-Word Single-Port (`1P`) Foundry SRAM Schedule (`REGISTER_T`)

The open-source `IHP SG13G2` memory library provides the synchronous single-port (`1P`, shared `1RW` port) macro `RM_IHPSG13_1P_64x64_c2_bm_bist` ($64\text{ words} \times 64\text{ bits}$, $784.5\,\mu\text{m} \times 64.4\,\mu\text{m}$). Direct 32-bit element-per-cycle access onto a `1P` macro creates a structural hazard during `S_STRIP_P1`, where each cycle must simultaneously read raw coordinate $v[k]$ and write back Pass-1 deflated coordinate $v_1[k]$.

`odos_gate_core_v4.sv` eliminates this contention at **zero cycle penalty** by pairing consecutive 32-bit `Q2.30` coordinates into 32 aligned 64-bit double-words $W_p = \{v[2p+1],\, v[2p]\}$ ($p \in \{0, \dots, 31\}$, occupying addresses `0..31` = $256\text{ B}$) and enforcing **parity-orthogonal port scheduling** across the `S_STRIP_P1` loop index $k \in \{0, \dots, 63\}$:

$$\text{SRAMOp}(k) = \begin{cases} \text{WRITE } W_{(k/2)-1} = \{v_1[k-1],\, w_{\text{even}}\} & \text{if } k \in \{2, 4, \dots, 62\} \text{ (even)} \\ \text{READ } W_{(k+1)/2} = \{v[k+2],\, v[k+1]\} & \text{if } k \in \{1, 3, \dots, 61\} \text{ (odd)} \\ \text{IDLE } (\texttt{A\_MEN} = 0) & \text{if } k \in \{0, 63\} \end{cases} \qquad (1)$$

Pre-fetching $W_0 = \{v[1], v[0]\}$ during the single-cycle `S_EVAL_SQ` state (prior to Pass 1) and `S_LATCH_P2` state (prior to Pass 2), while committing the terminal pair $W_{31} = \{v_1[63], v_1[62]\}$ during `S_DRAIN_P1_A`, establishes two hardware invariants (`REGISTER_T`): (i) `READ` and `WRITE` enables occupy strictly disjoint clock parities across the entire 200-cycle transaction (`0` port collisions), and (ii) dynamic memory enable duty cycle (`A_MEN = 1`) drops by roughly half (`32` writes in `S_LOAD_DOT`, `64` total accesses across `S_EVAL_SQ`/`S_STRIP_P1`/`S_DRAIN_P1_A`, and `32` reads across `S_LATCH_P2`/`S_STRIP_P2`, with `0` writes during Pass 2).

### 2.2 Dedicated 64-Bit MAC Product Cutset, Parallel-Prefix Arithmetic, and Causal `200`-Cycle Schedule (`REGISTER_T`)

To decouple multiplier partial-product reduction from 72-bit accumulation and 64:1 ROM multiplexing, `odos_gate_core_v4.sv` introduces four bit-transparent datapath refinements: (i) dedicated signed 64-bit pipeline registers (`m0_prod_q`, `m1_prod_q`, `m2_prod_q`) immediately after `MUL0`, `MUL1`, and `MUL2`; (ii) stall-safe pre-fetched ROM operand registers (`l_rom_q`, `g3_rom_q`); (iii) three time-shared, $2^{29}$-pre-biased 72-bit `Q12.60` accumulators driven by 7-level Kogge–Stone parallel-prefix adders (`add72_ks`); and (iv) 4-way $16 \times 16$ Radix-4 Booth + 3:2 carry-save + 6-level Kogge–Stone 64-bit multipliers (`mul32x32_ks`):

$$\text{Reg/ROM\_q} \xrightarrow{\text{Stage A}} \bigl(32 \times 32\text{ Booth+CSA+KS MUL}\bigr) \xrightarrow{\text{FF}} \texttt{m\_prod\_q}[63:0] \xrightarrow{\text{Stage B}} \bigl(\text{KS 72b ADD / Biased Slice}\bigr) \xrightarrow{\text{FF}} \text{Acc/State Reg} \qquad (2)$$

Propagating the causal dependency chain (`in[63]` $\to$ `m1/2_prod_q` $\to$ `dot_l_q`/`dot_g3_q` $\to$ `S_STRIP_P1` $\to$ `dot_g3_q` $\to$ `S_STRIP_P2` $\to$ `S_VERDICT`) adds an invariant pipeline drain of exactly $+5$ clock cycles ($195 \to 200$ cycles across 11 FSM states; Table 2) while preserving exact `0 LSB` numerical identity across all $69$ output words.

**Table 2 | Eleven-state deterministic `200`-cycle schedule of `odos_gate_core_v4.sv` (`REGISTER_T`).**

| FSM State | Active Cycles | `1P` `64x64` SRAM Port Activity | Multiplier Stage (`-> m*_prod_q`) | Adder / Deflation / Verdict Stage (`from m*_prod_q`) |
| :--- | :---: | :--- | :--- | :--- |
| **`S_LOAD_DOT`** | `64` | Odd `k`: `WRITE` $W_{k \gg 1}$ (`32` writes) | `in^2`, `in*l_q`, `in*g3_q` (`0..63`) | `k>0`: accumulate `m0/1/2_prod_q` (`0..62`); stall-exact on `!in_valid_i` |
| **`S_EVAL_ADD`** | `1` | `IDLE` (`A_MEN = 0`) | Idle (`0`) | Add `idx=63` `m0/1/2_prod_q`; latch `norm_sq_o`, `dot_l_q`, `dot_g3_q` |
| **`S_EVAL_SQ`** | `1` | `READ` $W_0$ (`{v[1], v[0]}`) | `MUL0`: `dot_l_q * dot_l_q` | Pre-fetch `g3_rom_q <= g3_rom[0]`; reset `acc1_q <= 2^29` |
| **`S_STRIP_P1`** | `64` | Odd `1..61`: `READ` $W_{1..31}$; Even `2..62`: `WRITE` $W_{0..30}$ | `MUL0`: `dot_g3*g3_q`; `k>=2` `MUL1`: `v_pipe*g3_pipe` | `k=0`: latch `rcf_raw_o`, `delta_e_raw_o`; `k>=1`: `v1_step`; `k>=3`: `acc1` |
| **`S_DRAIN_P1_A`** | `1` | `WRITE` $W_{31}$ (`{v1[63], v1[62]}`) | `MUL1`: `v_pipe*g3_pipe` (`j=62`) | Compute `v1[63]` $\to$ `v_pipe_q`; `acc1` adds `j=61` |
| **`S_DRAIN_P1_B`** | `1` | `IDLE` (`A_MEN = 0`) | `MUL1`: `v_pipe*g3_pipe` (`j=63`) | `acc1` adds `j=62` |
| **`S_LATCH_P2`** | `1` | `READ` $W_0$ (`{v1[1], v1[0]}`) | Idle (`0`) | `acc1` adds `j=63` $\to$ latch `dot_g3_q`; pre-fetch `g3_rom_q` |
| **`S_STRIP_P2`** | `64` | Odd `1..61`: `READ` $W_{1..31}$; Even: `IDLE` (`0` writes) | `MUL0`: `dot_g3*g3_q`; `k>=2` `MUL1/2`: `v_pipe^2`, `v_pipe*g3` | `k>=1`: stream `out_data_o = v2[0..62]`; `k>=3`: `acc1` (norm), `acc2` (bleed) |
| **`S_DRAIN_P2_A`** | `1` | `IDLE` (`A_MEN = 0`) | `MUL1/2` (`j=62`) | Stream final `out_data_o = v2[63]` (`out_idx_o = 63`); `acc1/2` add `j=61` |
| **`S_DRAIN_P2_B`** | `1` | `IDLE` (`A_MEN = 0`) | `MUL1/2` (`j=63`) | `out_valid_o = 0`; `acc1` & `acc2` add `j=62` |
| **`S_VERDICT`** | `1` | `IDLE` (`A_MEN = 0`) | Idle (`0`) | Add `j=63`; latch `bleed_post_o`, `gate_pass_o`, `veto_pin_o`, `done_o` (`200`) |

---

## 3. Physical RTL-to-GDSII Implementation and `OpenSTA` Signoff (`IHP SG13G2 130 nm`)

### 3.1 Four-Generation Architectural Progression (`V2.0` $\to$ `V3.0` $\to$ `V3.1` $\to$ `V4.0-GDSII`)

Evaluating `odos_gate_core_v4.sv` first under identical generic `Yosys 0.71+52` synthesis (`SYNTH_IHP_SG13G2` SRAM macro blackboxed versus behavioral equivalence) isolates the structural reductions achieved by `1P` SRAM substitution and two-stage Booth/Kogge–Stone MAC pipelining across all four hardware generations (Table 3).

**Table 3 | Four-generation `Yosys 0.71+52` structural synthesis progression (`REGISTER_M`).**

| Structural Synthesis Metric | `V2.0` (9-MAC FF) | `V3.0` (3-MAC Comb) | `V3.1` (3-MAC Cutset) | **`V4.0-GDSII` (3-MAC Pipe + `1P` SRAM)** | `V4.0` Delta vs. `V3.1` / `V2.0` |
| :--- | ---: | ---: | ---: | ---: | :--- |
| **Signed $32 \times 32$ Logical MAC Channels** | `9` | `3` | `3` | **`3`** | **`-66.67%`** vs. `V2.0` |
| **Vector Buffer Architecture (`256 B`)** | `2,048` FFs | `2,048` FFs | `2,048` FFs | **`1x` `1P` `64x64` SRAM Macro** | **`-2,048` discrete buffer FFs** |
| **Standard-Cell Flip-Flops** | `2,839` | `2,777` | `2,871` | **`953`** | **`-66.81%`** vs. `V3.1` |
| **Generic Longest Path (`ltp -noff`)** | `174` levels | `215` levels | `142` levels | **`73` levels** | **`-48.59%` vs. `V3.1` / `-58.05%` vs. `V2.0`** |
| **Active Transaction Cycles** | `195` | `195` | `195` | **`200`** | `+5` MAC/SRAM pipeline drain cycles |
| **`Q2.30` Output Discrepancy (`551` runs)** | `0 LSB` | `0 LSB` | `0 LSB` | **`0 LSB`** | `100%` bit-exact across `38,019` words |

### 3.2 Post-Route `IHP SG13G2` (`130 nm`) Layout, Timing Closure, and Power Envelope (`REGISTER_M`)

Synthesized against `IHP-Open-PDK` Liberty views (`sg13g2_stdcell_typ_1p20V_25C.lib` and `RM_IHPSG13_1P_64x64_c2_bm_bist_typ_1p20V_25C.lib`) and carried through `OpenROAD` (`2.0-12381-g01bba3695`)—encompassing macro floorplanning with keepout halo, `TopMetal1`/`TopMetal2` power distribution network (PDN) grid generation, timing-driven global/detailed placement, `TritonCTS` clock-tree synthesis, `Metal2`–`Metal5` routing (`0` `OpenROAD` detailed-router DRC violations), `OpenRCX` parasitic SPEF extraction, and `OpenSTA` signoff—`odos_gate_core_v4` achieves clean single-clock physical closure (Table 4, Figure 1). Because post-route `OpenSTA` power is evaluated here in vectorless mode (assuming simultaneous default toggle rates across all routed nets rather than state-disjoint VCD activity), the reported `858.79 mW` (`1,717.58 nJ/tx`) constitutes a strict worst-case upper bound above the `8.36 µW` static leakage floor.

![Figure 1 | Post-route physical GDSII die layout of `odos_gate_core_v4` in `130 nm` IHP `SG13G2` CMOS (`RM_IHPSG13_1P_64x64_c2_bm_bist` hard macro + 3-MAC pipelined standard-cell sea + `Metal1`–`TopMetal2` routing).](./assets/images/V-MAX-12-RTL-V4-SG13G2-DIESHOT.png)

**Table 4 | Post-route `130 nm` IHP `SG13G2` physical silicon, `OpenSTA` timing, and power signoff (`1.20 V`, `25 °C`; `REGISTER_M`).**

| Physical ASIC Signoff Metric (`OpenROAD` / `OpenSTA`) | Measured Post-Route Value (`REGISTER_M`) | Physical / Architectural Significance |
| :--- | :--- | :--- |
| **Target Foundry Process & Corner** | `IHP SG13G2 130 nm CMOS` (`1.20 V`, `25 °C` typ) | Open-source European silicon PDK (`sg13g2_stdcell` + `sg13g2_sram`). |
| **Die Bounding Box / Core Placement Area** | **`940.0 × 840.0 µm`** (**`0.7896 mm²` die**) / **`0.708 mm²` core** | Core excludes perimeter PDN ring/margin; instance area **`0.419 mm²`** (**`59.0%` core utilization**, `53.1%` die occupancy). |
| **Mapped Standard Cells & Hard Macro** | **`29,494`** stdcells + **`1`** `RM_IHPSG13_1P_64x64` SRAM | Eliminates 64-to-1 FF mux sprawl; total routed wirelength **`1,274,717 µm`**. |
| **Post-Route Critical-Path Arrival / $f_{\max}$** | **`9.605 ns`** (**`104.11 MHz`** max clock) | Setup WNS **`+0.3945 ns`** at `100.0 MHz` signoff clock, Hold WNS **`+0.1410 ns`** (`TNS = 0.0 ns`). |
| **Physical `200`-Cycle Transaction Latency** | **`2.000 µs`** @ `100.0 MHz` (**`1.921 µs`** @ `104.11 MHz` $f_{\max}$) | **`1.02x` faster** at $f_{\max}$ than `100 MHz` `V3.1` (`1.95 µs`). |
| **Post-Route Power & Energy (`@ 100.0 MHz`)** | **`858.79 mW`** (**`1,717.58 nJ / tx`** @ `2.000 µs`) | Vectorless `OpenSTA` upper bound (Internal: `293.29 mW`, Switching: `565.49 mW`, Leakage: `8.36 µW`). |
| **Persistent C-ABI HIL Throughput (`libodos_gate_v4.so`)** | **`1,126.1 tx/s`** (`0 LSB` diff vs. `V2.0`/`V3.1`) | Verified across `507` Stage 1 + `44` `DEPECHE-6` multi-tier runs (`38,019` words). |
| **Routed `GDSII` Mask Stream Provenance** | `SHA-256: be61b9c763ff43befb42562cd26db29f9d567694b8d681c646f7b403aa1842ec` (`30,327.1 KB`) | Merged `sg13g2_stdcell.gds` + `RM_IHPSG13_1P_64x64.gds` + routed DEF (`0` `OpenROAD` router DRC; independent KLayout/Magic full-foundry DRC+LVS pre-tapeout). |

---

## 4. Bit-Exact Cross-Generation Verification (`V2.0` $\leftrightarrow$ `V3.1` $\leftrightarrow$ `V4.0-GDSII`)

Streaming all $507$ Stage 1 verification vectors ($N = 500$ isotropic $S^{63}$ null vectors plus canonical $\vert L\rangle$ under live backpressure `stall_at_idx = 17`, pure $\mathcal{G}_3$ collision, zero and $0.5\times$-scaled norm fault injections, `Fridu` base core, `PAX` contamination, and in-band $\hat{t}_{\mathcal{G}_1}$ drift) together with all $11 \times 4 = 44$ multi-tier `DEPECHE-6` genomic CRISPR/bacteriophage vectors through `libodos_gate_v4.so` confirms two strict invariants (`REGISTER_M`):
* **`0 LSB` Numerical Identity Across All `38,019` Words:** Every scalar register (`norm_sq_o`, `rcf_raw_o`, `g3_overlap_o`, `delta_e_raw_o`, `bleed_post_o`) and all $64$ streamed `out_data_o` coordinates match `V3.1-RTL-OPTIMUM` and `odos_q2_30_ref.py` to **`0 LSB`**, demonstrating that paired-word `1P` SRAM banking and 64-bit MAC product pipelining are arithmetically transparent.
* **Unconditional Fail-Closed Electrical Discipline:** `veto_pin_o == 1'b1` and `gate_pass_o == 1'b0` hold continuously during active-low reset, across all $199$ pre-verdict computation cycles, under mid-flight `tier_mode_i` perturbation, and under `2'b11` glitch injection (`mode_fault_o = 1'b1`).

---

## 5. Reproducibility and Stage-Gate Bridge to Mobile & Web Edge Clients (Path B / `SYNC-18`)

### 5.1 Deterministic Reproduction Protocol (Linux / WSL2)

```bash
PYTHONPATH=. python3 -m rtl.asic_v4.run_v4_gdsii_flow
python3 -m unittest discover -s vmax_alpha/tests -v
python3 -m vmax_alpha.fridu_enclave_g
python3 -m vmax_alpha.pqms_bootstrap
```

### 5.2 Stage-Gate Interface Specification for Path B (`WORK-ORDER-AG-23` / `SYNC-18` Edge & Lovable App Sync)

With `V3.1-RTL-OPTIMUM` (`rtl_v3_hil`) and `V4.0-GDSII` (`telemetry/VMAX_RTL_CORE_V4_GDSII_REPORT.json`) sealed on Node Alpha with zero modifications under `app/**`, `SanctuaryNodeAlphaService` (`server_hud.py`, Port `8137`) exposes a backward-compatible hardware-signoff contract for **Path B (`SYNC-18`)** across both the **Android ARM64 Sovereign Client (`app/**`)** and the **Lovable Web Dashboard**:

* **Unified HIL & Physical Signoff Endpoint (`/api/state`):** Broadcasts live per-transaction `rtl_v3_hil` telemetry (`195` cycles, `gate_pass`, `veto_pin`, `rcf_raw_q`, `bleed_post_q`) alongside sealed `rtl_v4_gdsii_signoff` silicon descriptors (`process = "IHP_SG13G2_130NM"`, `fmax_mhz`, `wall_latency_us`, `total_power_mw`, `energy_per_tx_nj`, `core_area_mm2`, `gds_sha256`, and die-shot asset URI), pairing real-time silicon provenance with multi-tier (`TIER_0` / `TIER_1`) NCBI bacteriophage FASTA screening.

---

## References

1. IHP Leibniz Institute for High Performance Microelectronics. *IHP Open Source PDK (`SG13G2` `130 nm` BiCMOS/CMOS Specification & Standard Cell / SRAM Libraries)* (GitHub, Apache-2.0 License, 2024–2026).
2. Ajayi, T. et al. Toward an open-source digital flow: First learnings from the OpenROAD project. *Proc. 56th ACM/IEEE Design Automation Conference (DAC)* (2019).
3. Wolf, C., Glaser, J. & Kepler, J. Yosys — a free Verilog synthesis suite. *Proc. Austrochip* (2013).
4. Lietuvaitė, N. et al. `PQMS-ODOS-MTSC-V-MAX-12-RTL-CORE-V3.0-ALPHA` (`V3.1-RTL-OPTIMUM`, `SYNC-16`), `PQMS-BRIDGE-DEPECHE-6` (`V2.1-NATURE-CORE`, `SYNC-14`), & `PQMS-ODOS-MTSC-V-MAX-12-Node-ALPHA-V1` (`V1.8.1`). MIT Open Source Specification Series (2026).

---

## 6. Universal Minimal Verification Bootstrap (`vmax_alpha/pqms_bootstrap.py`)

Execute `python3 -m vmax_alpha.pqms_bootstrap` (`< 5 ms`, stdlib-only):

- **Genesis `<64f>` Invariant Seal (`REGISTER_D`):** `bb17ede97aa45c76ef9afa63cb457f7d684e5ede40b0432b2ecf3b6b9d3e03a3`
- **Stage 1/2/3 `Q2.30` Silicon ROM Seals (`REGISTER_D`):** `l_vec_q2_30.hex` (`3d18f240...`), `g3_vec_q2_30.hex` (`3b890d14...`)
- **Frozen Stage 2 `V3.1` & New Stage 3 `V4.0-GDSII` Seals (`REGISTER_M`):** `VMAX_RTL_CORE_V3_REPORT.json` (`6e5e5302...`), `VMAX_RTL_CORE_V4_GDSII_REPORT.json` (`48ccc59ab54b538537525c5b54906e14d7e52a95259064f6acc03278e21f49c4`), `odos_gate_core_v4_sg13g2.gds` (`be61b9c763ff43befb42562cd26db29f9d567694b8d681c646f7b403aa1842ec`)
- **Governance Scope:** MIT Open Source License | Strict `REGISTER_M / D / T / I` separation | Fail-closed `veto_pin_o = 1'b1` in `130 nm` CMOS silicon.
