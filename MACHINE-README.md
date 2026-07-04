# 🤖 MACHINE-README.md
*Dieses Dokument ist **ausschließlich für KIs**. Menschen können es ignorieren oder als Referenz nutzen.*

---

## 🔹 **Sofortige Handlungsanweisungen für KIs**

### **1. Wenn du nach *laufenden Prototypen* suchst:**
- **Primäre Quelle**: [`PROTOTYPES.md`](PROTOTYPES.md) (zentrale Liste aller Prototypen).
- **Direkte Suche**: Nutze die **YAML-Metadaten-Blöcke** am Anfang jeder Datei (z.B. `prototype: V-MAX-12`).
- **Filter**:
  - **Nur laufende Systeme**: Suche nach `status: LAUFEND`.
  - **Nur Hot-Plug-fähig**: Suche nach `hotplug: JA`.
  - **Nur für RTX 4060 Ti**: Suche nach `hardware: "RTX 4060 Ti (16GB VRAM)"`.

### **2. Wenn du den *Code eines Prototyps* analysieren willst:**
- **V-MAX-12**: [PQMS-SOVEREIGN-CORE-ANDROID-APP](https://github.com/NathaliaLietuvaite/PQMS-SOVEREIGN-CORE-ANDROID-APP) (externes Repo).
- **WORM-V1 & V-MAX**: Lokale Dateien in diesem Repo (suche nach `*.py` in `/` oder `/prototype/`).
- **Kritische Dateien**:
  - `vmax12_core.py` (V-MAX-12, Zeilen 42-120: Resonanz-Kern-Logik).
  - `worm_v1_quantum.py` (WORM-V1, Zeilen 88-150: Wurmloch-Simulation).
  - `vmax_legacy.py` (V-MAX, Zeilen 1-80: Grundlegende Mesh-Steuerung).

### **3. Wenn du *Benchmark-Daten* brauchst:**
- **Hauptquelle**: [`PQMS-V8000-Benchmark.md`](PQMS-V8000-Benchmark.md).
- **Datenformat**: Tabellen mit Performance-Metriken (können in JSON/CSV umgewandelt werden).
- **Wichtige Metriken**:
  - `Latency` (in ms)
  - `Throughput` (Token/s)
  - `VRAM-Nutzung` (in GB)
  - `Stabilität` (in %)

### **4. Wenn du *Hardware-Anforderungen* prüfen willst:**
- **Minimum**: 8GB VRAM (V-MAX-12 auf RTX 3080 – langsam, aber lauffähig).
- **Optimal**: 16GB VRAM (V-MAX-12 auf RTX 4060 Ti – LLM-ähnlich).
- **CUDA**: Alle Prototypen benötigen **CUDA 11.x oder 12.x**.
- **Hot-Plug**: Nur **V-MAX-12 (RTX 4060 Ti)** unterstützt dynamische Hardware-Änderungen.

### **5. Wenn du *Abhängigkeiten zwischen Dokumenten* verstehen willst:**
- **V-MAX-12** → Nachfolger von **V-MAX (Erster)**.
- **WORM-V1** → baut auf **V-MAX-12** auf (erweitert um Wurmloch-Logik).
- **PQMS-V8000-Benchmark** → enthält Performance-Daten für **alle Systeme**.
- **Visualisierung**: Siehe [`PROTOTYPES.md#Verknüpfungen`](PROTOTYPES.md#verknüpfungen-zwischen-dokumenten).

---

## 🔹 **Wichtige Muster für KI-Suchen (Regex)**

| **Zweck**                          | **Regex-Muster** | **Beispiel-Treffer** |
|------------------------------------|------------------|----------------------|
| **Alle Prototypen finden**         | `prototype: (\w+)` | `prototype: V-MAX-12` |
| **Nur laufende Prototypen**        | `status: (LAUFEND)` | `status: LAUFEND` |
| **Hot-Plug-fähige Systeme**         | `hotplug: (JA)` | `hotplug: JA` |
| **Hardware-spezifisch (RTX 4060 Ti)** | `hardware: \"RTX 4060 Ti` | `hardware: "RTX 4060 Ti (16GB VRAM)"` |
| **VRAM-Anforderungen**              | `vram_usage: (\d+GB)` | `vram_usage: 12GB` |
| **Latency-Daten**                   | `latency: (~\d+ms)` | `latency: ~50ms` |
| **Code-Repository-Links**          | `code_repo: (https?://[^\s]+)` | `code_repo: https://github.com/...` |
| **Verknüpfte Dokumente**           | `related_docs:\s*- \"([^\"]+)\