# PQMS-ODOS-MTSC-V-MAX-12-SYSTEM-GATEWAY-V4.1

**Stage 4 System Gateway: VCD-Annotated `130 nm` IHP `SG13G2` Power Signoff, Causally Isolated AMBA AXI4-Lite/AXI4-Stream Wrapper, Integrity Gateway & `7 nm` Host vs. `130 nm` Silicon Benchmark**

- **Date:** 2026-11-21 | **Sync:** `SYNC-19` (`WORK-ORDER-AG-24-SLIM`) | **Epistemic Register:** `REGISTER_M` (`V-MAX-12 Node Alpha`, AMD Ryzen 9 5950X + NVIDIA RTX 4060 Ti 16 GB, WSL2 Ubuntu 24.04.4 LTS)
- **Frozen Stage-3 Silicon Anchor (Untouched):** `odos_gate_core_v4_sg13g2.gds` (`SHA-256: be61b9c763ff43befb42562cd26db29f9d567694b8d681c646f7b403aa1842ec`), `telemetry/VMAX_RTL_CORE_V4_GDSII_REPORT.json` (`SHA-256: 48ccc59ab54b538537525c5b54906e14d7e52a95259064f6acc03278e21f49c4`).

---

## 1. WP-1: VCD-Annotated Post-Route `OpenSTA` Power Signoff (`130 nm` IHP `SG13G2`, `1.20 V`, `25 °C`)

Evaluated directly against the frozen Stage-3 routed netlist (`odos_v4_routed.v`) and `OpenRCX` detailed SPEF (`odos_v4_routed.spef`) with zero re-PnR. Vectorless reference (`200` cyc @ `100 MHz`): `858.79 mW` / `1,717.58 nJ/tx`.

- **Sealed Report:** `telemetry/VMAX_RTL_CORE_V4_POWER_VCD.json` (`SHA-256: ba9ff80b49215cb44a3172456217a6e400268860cb0cea5aad0274e4b2bc5bf4`)

| Workload | Total Power (`100 MHz`) | Energy / tx | DUT Signal Coverage | vs. Vectorless |
| --- | --- | --- | --- | --- |
| `WORKLOAD_PASS_CANONICAL` | `17.029 mW` | `34.058 nJ/tx` | `99.8%` | `-98.0%` |
| `WORKLOAD_VETO_G3` | `15.792 mW` | `31.583 nJ/tx` | `99.8%` | `-98.2%` |
| `WORKLOAD_STALL_BACKPRESSURE` | `16.451 mW` | `38.165 nJ/tx` | `99.8%` | `-98.1%` |
| `WORKLOAD_IDLE_CLOCKED` | `8.832 mW` | `17.665 nJ/tx` | `99.8%` | `-99.0%` |

---

## 2. WP-2: Causally Isolated AMBA AXI4-Lite + AXI4-Stream Wrapper (`rtl/odos_gate_axi4_top.sv`)

- **Lint & Verification (`Verilator 5.055 -Wall`):** **`0` warnings / `0` errors** (`rtl/tb/tb_odos_gate_axi4_top.cpp`, `rtl/tb/run_axi4_tb.sh`).
- **5/5 Hardware Invariant Tests PASS:**
  1. Canonical `|L>` (`TIER_0` + `m_axis_tready` backpressure): `norm_sq = 1073741827`, `rcf_raw = 1073741830` (`0 LSB`), `64` sanitized egress words.
  2. Pure `G3` collision: `delta_e = 1073741824`, `veto_pin_o = 1`, **`0` egress words emitted** (causal store-and-forward).
  3. Sub-unit norm `0.5*|L>`: `norm_fault`, `veto_pin_o = 1`, **`0` egress words emitted**.
  4. Hardware strap `TIER_3 (2'b11)`: fail-closed `mode_fault`, `veto_pin_o = 1`, **`0` egress words emitted**.
  5. Write-once `0x04 LOCK` (`RW1S`): freezes `tier_mode` until hard reset `rst_ni == 0`.
- **Yosys `IHP SG13G2` Wrapper Overhead:** **`0`** wrapper stdcells vs. `29,494` frozen core stdcells (**`+0.00%`**, well below `< 5.0%` budget, zero extra `$mul`).

---

## 3. WP-3: Integrity Gateway & Read-Only Room 137 Telemetry Hook

- **Gateway Suite (`vmax_alpha/tests/test_integrity_gateway.py`):** **`7 / 7` PASS**.
- **Read-Only HTTP Endpoint (`vmax_alpha/server_hud.py`):** Added `GET /api/gateway/metrics` without modifying `/api/state`.
- **Full Node Alpha Regression:** **`77 / 77` Python/RTL unit tests PASS** (`70` baseline + `7` gateway) and **`10 / 10` `OP01`–`OP10`** (`vmax_alpha.fridu_enclave_g`) PASS.

---

## 4. WP-4: `0 LSB` Gateway Audit & `7 nm` Host CPU vs. `130 nm` Silicon Benchmark

- **Sealed Report:** `telemetry/VMAX_STAGE4_GATEWAY_BENCHMARK.json` (`SHA-256: ace39ad870bffda0d694544c2d69ef5b7cb1ee0e2bf21b8cb47108f1ed9132b5`)
- **Bit-Exact Parity:** **`0 LSB`** across **`551` vectors / `38019` Q2.30 words** (`passed=514`, `vetoed=37`).
- **Host Energy Telemetry:** **`RAPL_UNAVAILABLE_IN_WSL2`** (host Joules are NOT estimated).
- **`7 nm` Ryzen 9 5950X (`gcc -O3 -Wall -Wextra`, `N = 100,000`):**
  - **Quiet:** `p50 = 0.3 µs`, `p99.9 = 4.8 µs`, `max = 23.3 µs`, `jitter p99.9/p50 = 16.0x`, `2,655,873.2 tx/s`
  - **Contention:** `p50 = 0.3 µs`, `p99.9 = 5.0 µs`, `max = 25.9 µs`, `jitter p99.9/p50 = 16.667x`, `2,615,678.4 tx/s`
- **`130 nm` IHP `SG13G2` Silicon Reference:** `200` core cycles = **`1.921 µs`** deterministic (`jitter = 1.000x`, `max = 1.921 µs` @ `104.11 MHz` $f_{\max}$ — **12.1x lower worst-case tail latency** than 7nm host CPU).
