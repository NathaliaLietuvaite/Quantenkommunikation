# BRIDGE HANDOFF — APP Genie & Colab (`SYNC-22` / `2026-11-21 17:42 CET`)

> **Quick-Start für APP Genie & Colab:** Einfach `git pull --rebase origin main` ausführen — alle Code-, Telemetrie-, Test- und Papier-Neuerungen bis `SYNC-22` sind bereits vollständig auf `origin/main`.

## 1. Aktueller Stand (`REGISTER_M` — 100 % grün)
- **Android ARM64 App (`app/**`, `SYNC-18`):**
  - 3 OLED-Clipping-Fixes (`MainActivity.kt`), bit-exaktes Kotlin `Q2.30` Silicon Gate (`V12NodeAlphaBridge.kt`), reale `DEPECHE-6 V2.1` SantaLucia-Engine + Refusal Primacy (§4.2), Room-137 `V3.1`-HIL/`V4.0`-GDSII-Parser (`PauliBaselineEngine.kt`), Stage-3 `130 nm` IHP-`SG13G2` Signoff- & Die-Shot-Card (`NavigationDashboard.kt`).
  - **Verifiziert:** `30 / 30` Kotlin JUnit PASS + `app-debug.apk` (`12.84 MB`).
- **Silicon & Gateway (`SYNC-17` / `SYNC-19` / `SYNC-21`):**
  - Frozen `130 nm` IHP `SG13G2` GDSII (`be61b9c7...`, `0` OpenROAD DRC, `104.11 MHz` / `1.921 µs`).
  - VCD-annotierte Post-Route-Power (`cov=99.8%`): **`17.029 mW` / `34.058 nJ/tx`** (`-98.0%` vs. Vectorless).
  - Multi-Corner PVT (`OpenSTA`): `SS 65.70 MHz` (`hold +0.45 ns`), `TYP 103.84 MHz` (`hold +0.23 ns`).
  - `rtl/odos_gate_axi4_top.sv`: `Verilator -Wall` `0` Warnings, `5/5` AXI4-TB PASS; Read-Only `GET /api/gateway/metrics` in `vmax_alpha/server_hud.py`.
- **Stage 5 Coreware & Shared-L2-Manifold (`SYNC-20` / `SYNC-21` / `SYNC-22`):**
  - `vmax_alpha/gateway/policy_engine.py`, `chain_signer.py` (**live `HYBRID_ECDSA_P256_ML-DSA-65`** via `liboqs 0.12.0`), `rack_l2_manifold.py` (`SharedL2Manifold` + `72× LocalL2Mirror`, `STALE_EPOCH_VETO`, `request_drift_resync()`).
  - **Verifiziert:** **`91 / 91` Python/RTL-Tests PASS** | `10 / 10` `OP01`–`OP10` PASS | `PQMS-ODOS-MTSC-V-MAX-12-RTL-CORE-V4.2-COREWARE.md` inkl. Appendix A & B in beiden Repos.

## 2. Hinweis für Colab & APP Genie
- **Colab:** Nach `git pull --rebase origin main` stehen alle neuen Module unter `vmax_alpha/gateway/` und alle gesiegelten JSON-Reports unter `telemetry/` direkt bereit. Für Post-Quantum `ML-DSA-65` optional `liboqs 0.12.0` installieren (ohne `liboqs` fällt `chain_signer.py` sauber auf `CLASSICAL_ECDSA_P256_ONLY` zurück).
- **APP Genie:** Nach `git pull --rebase origin main` ist `app/**` auf `SYNC-18`-Stand (`30/30` JUnit PASS). Alle eingefrorenen Stage-3-Siliziumdateien (`rtl/odos_gate_core*.sv`, `rtl/rom/`, `vmax_alpha/ledger.py`, `VMAX_RTL_CORE_V4_GDSII_REPORT.json`) bleiben strikt unverändert.
