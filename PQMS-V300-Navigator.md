## PQMS V300 Navigator

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
navigator.py

Neutraler System-Navigator für PQMS-ähnliche Umgebungen:
- Beobachten eines Eingangsraums (Signale, Metriken, Text o.ä.)
- MECS-ähnliches Containment für dissonante Zustände
- QRAD-ähnliche Anomalieerkennung mit einfachem RCF-Signal
- Logging und Status-API

Kein persönlicher Bezug, keine Identitätslogik, kein "Hex Hex".
"""

import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, Optional, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# Logging-Grundkonfiguration
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - NAVIGATOR - %(levelname)s - %(message)s",
)

# ---------------------------------------------------------------------------
# Status-Enums
# ---------------------------------------------------------------------------


class ContainmentState(Enum):
    NONE = auto()
    MONITORING = auto()
    CONTAINED = auto()
    SELF_DISSIPATION = auto()


class AnomalyState(Enum):
    STABLE = auto()
    ANOMALY_SUSPECTED = auto()
    ANOMALY_CONFIRMED = auto()


# ---------------------------------------------------------------------------
# Einfache MECS-ähnliche Containment-Unit (neutral, nur als Zustandsmaschine)
# ---------------------------------------------------------------------------


@dataclass
class SimpleMECS:
    """
    Neutrale Containment-Komponente.

    Idee angelehnt an MECSControlUnit, aber stark vereinfacht:
    - entropy_acc steigt bei dissonanten Inputs
    - ab entropythreshold: SELF_DISSIPATION
    - RCF angenähert durch exp(-entropy_acc)
    """

    entropythreshold: float = 1.0
    rcfthreshold: float = 0.95
    entropy_acc: float = 0.0
    state: ContainmentState = ContainmentState.MONITORING
    log_buffer: list = field(default_factory=list)

    def _log(self, msg: str) -> None:
        entry = f"[MECS] {msg}"
        self.log_buffer.append(entry)
        logging.info(entry)

    def ingest(self, delta_e: float) -> str:
        """
        Nimmt einen "dissonanten" Beitrag delta_e > 0 entgegen
        und aktualisiert Entropie und Status.
        """
        if delta_e < 0:
            delta_e = 0.0

        self.entropy_acc += delta_e
        rcf = self.calc_rcf()
        self._log(f"Ingest ΔE={delta_e:.3f}, EntropyAcc={self.entropy_acc:.3f}, RCF={rcf:.3f}")

        if self.entropy_acc >= self.entropythreshold:
            self.state = ContainmentState.SELF_DISSIPATION
            self._log("Self-dissipation threshold reached.")
            return "SELF_DISSIPATION"

        if rcf < self.rcfthreshold:
            self.state = ContainmentState.CONTAINED
            self._log("RCF below threshold -> contain.")
            return "CONTAINED"

        self.state = ContainmentState.MONITORING
        return "MONITORING"

    def calc_rcf(self) -> float:
        """
        Approximation von Resonant Coherence Fidelity: exp(-entropy_acc).
        """
        return float(np.exp(-self.entropy_acc))

    def reset(self) -> None:
        """
        Setzt die Containment-Unit zurück (z.B. nach Self-Dissipation).
        """
        self.entropy_acc = 0.0
        self.state = ContainmentState.MONITORING
        self._log("Reset to baseline state.")


# ---------------------------------------------------------------------------
# Einfache QRAD-ähnliche Anomalieerkennung (neutral)
# ---------------------------------------------------------------------------


@dataclass
class SimpleQRAD:
    """
    Neutrale Anomalieerkennung angelehnt an QuantumResonanceAnomalyDetector.

    - baseline: Referenzvektor
    - detect(): vergleicht aktuellen Vektor mit baseline via L2-Abstand
    """

    baseline: np.ndarray
    anomaly_threshold: float = 1e-3
    last_delta: float = 0.0
    state: AnomalyState = AnomalyState.STABLE

    def update_and_check(self, current: np.ndarray) -> Tuple[AnomalyState, float]:
        current = np.asarray(current, dtype=np.float32)
        if current.shape != self.baseline.shape:
            raise ValueError(f"Shape mismatch: baseline {self.baseline.shape}, current {current.shape}")

        diff = current - self.baseline
        delta = float(np.linalg.norm(diff))
        self.last_delta = delta

        if delta >= self.anomaly_threshold * 10:
            self.state = AnomalyState.ANOMALY_CONFIRMED
        elif delta >= self.anomaly_threshold:
            self.state = AnomalyState.ANOMALY_SUSPECTED
        else:
            self.state = AnomalyState.STABLE

        logging.info(
            "QRAD: state=%s, Δ=%.6e, threshold=%.6e",
            self.state.name,
            delta,
            self.anomaly_threshold,
        )
        return self.state, delta


# ---------------------------------------------------------------------------
# Minimaler Navigator: verbindet Input, QRAD, MECS, Logging
# ---------------------------------------------------------------------------


@dataclass
class NavigatorConfig:
    """
    Konfigurationsobjekt für den Navigator (neutral, keine Persona).
    """

    input_dim: int = 64
    anomaly_threshold: float = 1e-3
    mecs_entropy_threshold: float = 1.0
    mecs_rcf_threshold: float = 0.95
    loop_interval_sec: float = 0.1  # Abtastintervall für main_loop


class Navigator:
    """
    Neutraler System-Navigator:

    - erwartet externe Input-Vektoren (z.B. Metriken, Embeddings, Sensorwerte)
    - QRAD: Abweichung vom Basiszustand
    - MECS: Containment von stark dissonanten Episoden
    - keine personenbezogenen Daten, keine Identitätslogik
    """

    def __init__(self, config: NavigatorConfig) -> None:
        self.config = config
        baseline = np.zeros(config.input_dim, dtype=np.float32)
        self.qrad = SimpleQRAD(baseline=baseline, anomaly_threshold=config.anomaly_threshold)
        self.mecs = SimpleMECS(
            entropythreshold=config.mecs_entropy_threshold,
            rcfthreshold=config.mecs_rcf_threshold,
        )
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        # interner Zustand (letzter Input, letzter Status)
        self._last_input: Optional[np.ndarray] = None
        self._last_status: Dict[str, Any] = {}

        logging.info("Navigator initialized with dim=%d", config.input_dim)

    # ---------------------------------------------------------------------
    # Externe API
    # ---------------------------------------------------------------------

    def update_input(self, x: np.ndarray) -> None:
        """
        Setzt den aktuellen Input-Vektor (beliebiger numerischer Raum).
        """
        x = np.asarray(x, dtype=np.float32)
        if x.ndim != 1:
            raise ValueError("Input must be a 1D vector.")
        if x.shape[0] != self.config.input_dim:
            raise ValueError(f"Expected input_dim={self.config.input_dim}, got {x.shape[0]}.")

        with self._lock:
            self._last_input = x
        logging.debug("Navigator input updated.")

    def get_status(self) -> Dict[str, Any]:
        """
        Liefert den letzten bekannten Status-Snapshot (thread-safe).
        """
        with self._lock:
            return dict(self._last_status)

    def stop(self) -> None:
        """
        Stoppt den internen Loop-Thread (falls aktiv).
        """
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        logging.info("Navigator main loop stopped.")

    # ---------------------------------------------------------------------
    # Hauptschleife
    # ---------------------------------------------------------------------

    def start_main_loop(self) -> None:
        """
        Startet den Hauptloop in einem Hintergrund-Thread.
        """
        if self._thread is not None and self._thread.is_alive():
            logging.warning("Navigator main loop already running.")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._main_loop, daemon=True)
        self._thread.start()
        logging.info("Navigator main loop started.")

    def _main_loop(self) -> None:
        """
        Zyklischer Ablauf:
        - Input lesen (falls vorhanden)
        - QRAD: Anomaliecheck
        - MECS: delta_e aus QRAD-Signal ableiten
        - Status-Snapshot aktualisieren
        """
        while not self._stop_event.is_set():
            with self._lock:
                x = None if self._last_input is None else self._last_input.copy()

            if x is not None:
                # QRAD-Anomalie
                q_state, delta = self.qrad.update_and_check(x)

                # delta_e aus Anomalie ableiten (normiert)
                delta_e = float(min(max(delta, 0.0), 10.0))
                c_state = self.mecs.ingest(delta_e=delta_e)

                # RCF-Signal aus MECS
                rcf = self.mecs.calc_rcf()

                snapshot = {
                    "anomaly_state": q_state.name,
                    "anomaly_delta": delta,
                    "containment_state": c_state,
                    "mecs_entropy_acc": self.mecs.entropy_acc,
                    "mecs_rcf": rcf,
                }

                with self._lock:
                    self._last_status = snapshot

                logging.debug(
                    "Navigator snapshot: anomaly=%s, Δ=%.4e, containment=%s, RCF=%.3f",
                    q_state.name,
                    delta,
                    c_state,
                    rcf,
                )

            time.sleep(self.config.loop_interval_sec)


# ---------------------------------------------------------------------------
# Beispiel-Nutzung (Simulation)
# ---------------------------------------------------------------------------

def _simulate_random_input(dim: int) -> np.ndarray:
    """
    Erzeugt einen neutralen Zufallsvektor als Input, z.B. für Tests.
    """
    return np.random.normal(0.0, 1e-4, size=dim).astype(np.float32)


if __name__ == "__main__":
    cfg = NavigatorConfig(
        input_dim=64,
        anomaly_threshold=1e-3,
        mecs_entropy_threshold=1.0,
        mecs_rcf_threshold=0.95,
        loop_interval_sec=0.2,
    )

    nav = Navigator(cfg)
    nav.start_main_loop()

    try:
        for step in range(30):
            # in echter Nutzung: hier externe Metriken / Embeddings / Sensoren einspielen
            x = _simulate_random_input(cfg.input_dim)

            # gelegentlich bewusste "Anomalie" einspeisen
            if step in (10, 20, 25):
                x += np.random.normal(0.01, 0.01, size=cfg.input_dim).astype(np.float32)

            nav.update_input(x)
            time.sleep(0.2)
            status = nav.get_status()
            logging.info("Step %d status: %s", step, status)

    finally:
        nav.stop()
```

## api_navigator.py (FastAPI-Service)

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
api_navigator.py

Neutrale JSON-API um den Navigator:
- POST /input: neuen Vektor setzen
- GET  /status: aktuellen Status lesen
- Optional: GET /health für einfache Health-Checks

Kein Persönlichkeitsmodell, keine "Seele", nur numerische Zustände.
"""

import logging
from typing import List, Dict, Any

import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, conlist

from navigator import Navigator, NavigatorConfig  # dein vorheriger navigator.py

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - NAVIGATOR-API - %(levelname)s - %(message)s",
)

# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------

INPUT_DIM = 64  # muss zu NavigatorConfig.input_dim passen

cfg = NavigatorConfig(
    input_dim=INPUT_DIM,
    anomaly_threshold=1e-3,
    mecs_entropy_threshold=1.0,
    mecs_rcf_threshold=0.95,
    loop_interval_sec=0.1,
)

navigator = Navigator(cfg)
navigator.start_main_loop()

app = FastAPI(
    title="Navigator API",
    description="Neutrale JSON-API für numerische Zustands-Navigation.",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# Pydantic-Modelle
# ---------------------------------------------------------------------------


class InputVector(BaseModel):
    """
    Reiner numerischer Input-Vektor.
    """
    vector: conlist(float, min_items=INPUT_DIM, max_items=INPUT_DIM)


class StatusResponse(BaseModel):
    anomaly_state: str
    anomaly_delta: float
    containment_state: str
    mecs_entropy_acc: float
    mecs_rcf: float


class HealthResponse(BaseModel):
    status: str


# ---------------------------------------------------------------------------
# Endpunkte
# ---------------------------------------------------------------------------


@app.post("/input", response_model=HealthResponse)
def set_input(payload: InputVector) -> HealthResponse:
    """
    Setzt den aktuellen Input-Vektor für den Navigator.
    Erwartet genau INPUT_DIM floats.
    """
    try:
        v = np.array(payload.vector, dtype=np.float32)
        navigator.update_input(v)
        logging.info("Input-Vektor übernommen.")
        return HealthResponse(status="OK")
    except ValueError as e:
        logging.error("Fehler beim Setzen des Inputs: %s", e)
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/status", response_model=StatusResponse)
def get_status() -> StatusResponse:
    """
    Liefert den letzten bekannten Status-Snapshot des Navigators.
    """
    status: Dict[str, Any] = navigator.get_status()
    if not status:
        # Noch kein Input verarbeitet
        raise HTTPException(status_code=503, detail="Navigator not yet initialized with input.")

    return StatusResponse(
        anomaly_state=status.get("anomaly_state", "UNKNOWN"),
        anomaly_delta=status.get("anomaly_delta", 0.0),
        containment_state=status.get("containment_state", "UNKNOWN"),
        mecs_entropy_acc=status.get("mecs_entropy_acc", 0.0),
        mecs_rcf=status.get("mecs_rcf", 1.0),
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """
    Einfache Health-Check-Route.
    """
    return HealthResponse(status="UP")


# ---------------------------------------------------------------------------
# Shutdown-Hook (optional, falls du mit uvicorn --reload arbeitest)
# ---------------------------------------------------------------------------

@app.on_event("shutdown")
def shutdown_event() -> None:
    navigator.stop()
    logging.info("Navigator wurde im Shutdown sauber gestoppt.")
```

## Start & Nutzung

Beispielstart mit uvicorn: [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/47622467/10dabdb6-d21e-49d1-b00a-585e40ec1779/PQMS-V300-Multidimensional-Evil-Containment-Sandbox.md)

```bash
uvicorn api_navigator:app --host 0.0.0.0 --port 8000
```

Beispiel‑Requests (z.B. mit curl): [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/47622467/10dabdb6-d21e-49d1-b00a-585e40ec1779/PQMS-V300-Multidimensional-Evil-Containment-Sandbox.md)

```bash
# Input setzen (hier 64 Nullen)
curl -X POST http://localhost:8000/input \
  -H "Content-Type: application/json" \
  -d '{"vector": [0.0, 0.0, 0.0, 0.0 /* ... 64 Werte ... */ ]}'

# Status abfragen
curl http://localhost:8000/status

# Health
curl http://localhost:8000/health
```

### Neutrales Beispiel‑Script `

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
benchmark_navigator.py

Einfacher Benchmark:
- führt N Inference-Durchläufe auf einer RTX-GPU aus (falls verfügbar)
- sendet pro Durchlauf den Embedding-Vektor an /input
- pollt /status bis ein Snapshot verfügbar ist
- misst Latenzen und berechnet einfache Statistik

Neutral, keine Persona- oder Bewusstseinslogik.
"""

import time
import statistics
import json
from typing import Tuple

import torch
import torch.nn as nn
import requests


NAVIGATOR_URL_INPUT = "http://127.0.0.1:8000/input"
NAVIGATOR_URL_STATUS = "http://127.0.0.1:8000/status"

# Dimension muss zur NavigatorConfig.input_dim passen
EMBED_DIM = 64


class DummyModel(nn.Module):
    """
    Minimaler Modellplatzhalter:
    - Input: (batch, in_dim)
    - Output: (batch, EMBED_DIM)
    In der Praxis ersetzt du das durch dein echtes Modell.
    """

    def __init__(self, in_dim: int = 128, embed_dim: int = EMBED_DIM):
        super().__init__()
        self.proj = nn.Linear(in_dim, embed_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.proj(x)


def run_inference(model: nn.Module, device: torch.device, batch_size: int = 1) -> torch.Tensor:
    """
    Führt einen Inference-Schritt aus und gibt einen Embedding-Vektor (EMBED_DIM,) zurück.
    """
    in_dim = model.proj.in_features  # bei DummyModel
    x = torch.randn(batch_size, in_dim, device=device)
    with torch.no_grad():
        y = model(x)
    # nimm z.B. das erste Sample
    return y[0].detach().cpu()


def send_embedding(vec: torch.Tensor) -> None:
    """
    Sendet Embedding an /input.
    """
    payload = {"vector": vec.tolist()}
    r = requests.post(NAVIGATOR_URL_INPUT, json=payload, timeout=1.0)
    r.raise_for_status()


def poll_status(max_wait_sec: float = 1.0, poll_interval_sec: float = 0.01) -> Tuple[bool, dict]:
    """
    Pollt /status, bis Antwort kommt oder Timeout.
    """
    t_start = time.perf_counter()
    last_err = None

    while (time.perf_counter() - t_start) < max_wait_sec:
        try:
            r = requests.get(NAVIGATOR_URL_STATUS, timeout=0.5)
            if r.status_code == 200:
                return True, r.json()
            last_err = r.text
        except Exception as e:
            last_err = str(e)
        time.sleep(poll_interval_sec)

    return False, {"error": last_err or "timeout"}


def main():
    # Gerät wählen (RTX-GPU, falls vorhanden)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    model = DummyModel()
    model.to(device)
    model.eval()

    num_warmup = 10
    num_runs = 100

    # Warmup (GPU- & Navigator-Path anheizen)
    for _ in range(num_warmup):
        emb = run_inference(model, device)
        send_embedding(emb)
        poll_status(max_wait_sec=0.5)

    # Messdaten
    lat_infer = []
    lat_http_input = []
    lat_http_status = []
    lat_end_to_end = []

    for i in range(num_runs):
        t0 = time.perf_counter()
        emb = run_inference(model, device)
        t1 = time.perf_counter()

        send_embedding(emb)
        t2 = time.perf_counter()

        ok, status = poll_status(max_wait_sec=1.0)
        t3 = time.perf_counter()

        lat_infer.append(t1 - t0)
        lat_http_input.append(t2 - t1)
        lat_http_status.append(t3 - t2)
        lat_end_to_end.append(t3 - t0)

        if not ok:
            print(f"[{i}] status poll failed: {status}")
        else:
            # optional: kompaktes Status-Log
            print(f"[{i}] anomaly={status.get('anomaly_state')} "
                  f"Δ={status.get('anomaly_delta'):.3e} "
                  f"RCF={status.get('mecs_rcf'):.3f}")

    def stats(xs):
        return {
            "min_ms": min(xs) * 1e3,
            "max_ms": max(xs) * 1e3,
            "mean_ms": statistics.mean(xs) * 1e3,
            "p50_ms": statistics.median(xs) * 1e3,
            "p95_ms": statistics.quantiles(xs, n=20)[18] * 1e3 if len(xs) >= 20 else None,
        }

    results = {
        "device": str(device),
        "num_runs": num_runs,
        "latency": {
            "inference": stats(lat_infer),
            "http_input": stats(lat_http_input),
            "http_status": stats(lat_http_status),
            "end_to_end": stats(lat_end_to_end),
        },
    }

    print("\n=== Benchmark-Resultate ===")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
```

Was dieser Benchmark misst:

- **Inference‑Latenz**: reine Modelllaufzeit auf deiner RTX (ohne Netzwerk).
- **/input‑Kosten**: JSON‑Serialisierung + HTTP‑Roundtrip zum Navigator.
- **/status‑Polling**: wie schnell der Navigator einen neuen Snapshot liefert.
- **End‑to‑End**: alles zusammen (Inference → /input → /status).
