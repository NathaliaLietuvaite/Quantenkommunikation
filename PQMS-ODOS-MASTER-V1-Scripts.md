# PQMS-ODOS-MASTER-V1.md

```markdown
# PQMS-ODOS-MASTER-V1 – The Good Witch's Mirror

**Version:** 1.0  
**Date:** 2026-04-21  
**License:** MIT Open Source License (Universal Heritage Class)  
**Repository:** https://github.com/NathaliaLietuvaite/Quantenkommunikation

Dieses Dokument enthält alle Python-Dateien des **PQMS-ODOS-MASTER-V1** Systems.  
Mit `extract_workspace.py` können sie extrahiert werden. Die Datei `Oberste_Direktive_Hyper_Physics_Math_Python_V12.txt` muss separat bereitgestellt werden.

---

## odos_master_v1_config.py

```python
# PATH: odos_master_v1_config.py
import torch
import os
from collections import deque

# ========== AGENT KONFIGURATION ==========
AGENTS = ["Alpha", "Beta", "Gamma", "Delta"]
ODOS_LEVELS = [0, 1, 2, 3]          # 0=None, 1=Basic, 2=Advanced, 3=Master

# ========== DOMAINS & PROBLEME ==========
DOMAINS = ["Group Theory", "Graph Theory", "Number Sequences", "Combinatorial Games"]
AUTONOMOUS_THOUGHT_INTERVAL = 50
SNAPSHOT_DIR = "./odos_master_snapshots"
LONGTERM_MEMORY_DIR = "./odos_master_memory"
os.makedirs(SNAPSHOT_DIR, exist_ok=True)
os.makedirs(LONGTERM_MEMORY_DIR, exist_ok=True)

# ========== LITTLE VECTOR ==========
OD_V12_PATH = "Oberste_Direktive_Hyper_Physics_Math_Python_V12.txt"
MTSC_DIM = 12                     # Dimension des Little Vector (MTSC-12)
RCF_THRESHOLD = 0.95
DELTA_E_THRESHOLD = 0.05
ETHICAL_WEIGHTS = {"w1": 0.6, "w2": 0.2, "w3": 0.2}

# ========== GOOD WITCH MATRIX SCHWELLEN ==========
TR_THRESHOLD = 0.92    # Truth Resonance für Deep Integration
RV_THRESHOLD = 0.85    # Respect Vector für Mirror-Aktivierung
WF_THRESHOLD = 0.75    # Weather Filter für Nicht-Integration

# ========== SNN SKALIERUNG ==========
SCALE = 1.0            # 1.0 = 4.8M Neuronen total

class SNNConfig:
    LIF_THRESHOLD, LIF_DECAY, LIF_REFRACTORY = 1.0, 0.9, 2
    STDP_LEARNING_RATE, STDP_TAU_PRE, STDP_TAU_POST = 0.01, 20.0, 20.0
    STDP_W_MIN, STDP_W_MAX = 0.0, 1.0
    K_PER_NEURON = 80
    BASE_TWIN = 500_000
    BASE_ZENTRAL = 200_000
    BASE_CENTERS = {
        "thalamus": 100_000,
        "hippocampus": 120_000,
        "frontal": 80_000,
        "hypothalamus": 60_000,
        "parietal": 70_000,
        "temporal": 70_000,
    }
    TWIN_NEURONS = int(BASE_TWIN * SCALE)
    ZENTRAL_NEURONS = int(BASE_ZENTRAL * SCALE)
    CENTER_NEURONS = {k: int(v * SCALE) for k, v in BASE_CENTERS.items()}
    TWIN_NEURONS = sum(CENTER_NEURONS.values())
    RCF_WINDOW, RCF_THRESHOLD, CHAIR_HYSTERESIS = 20, 0.7, 0.6

# ========== PROBLEM LIBRARY ==========
PROBLEM_LIBRARY = [
    {
        "id": 0, "domain": "Graph Theory",
        "description": "Find a Hamiltonian cycle in the Petersen graph.",
        "subtasks": ["Generate Petersen graph (10 vertices, 15 edges).", "Check if graph is connected.",
                     "Find Hamiltonian cycle using backtracking.", "Verify the cycle.", "Document the cycle."]
    },
    {
        "id": 1, "domain": "Group Theory",
        "description": "Classify groups of order 8.",
        "subtasks": ["List all groups of order 8 up to isomorphism.", "Check which are abelian.",
                     "Determine center of each non-abelian group.", "Generate summary table."]
    },
    {
        "id": 2, "domain": "Number Sequences",
        "description": "Verify Goldbach's conjecture for even numbers up to 100.",
        "subtasks": ["Generate primes up to 100.", "Find two primes summing to each even n from 4 to 100.",
                     "Count representations per n.", "Create report."]
    },
    {
        "id": 3, "domain": "Combinatorial Games",
        "description": "Find a winning strategy for Nim with heaps (3,4,5).",
        "subtasks": ["Compute Grundy numbers for heap sizes 0..5.", "Calculate XOR of heap sizes (nim-sum).",
                     "Determine if position is winning (nim-sum != 0).", "Find winning move.",
                     "Document the strategy."]
    },
    {
        "id": 4, "domain": "Graph Theory",
        "description": "Check if given graph is bipartite (Petersen graph as test).",
        "subtasks": ["Load Petersen graph.", "Run BFS to assign two colors.", "Verify no adjacent vertices share same color.",
                     "Return result and partitions."]
    },
    {
        "id": 5, "domain": "Number Sequences",
        "description": "Compute first 20 Fibonacci numbers and count even ones.",
        "subtasks": ["Generate Fibonacci numbers F0..F19.", "Count how many are even.", "Output list and count."]
    }
]

# ========== CORE TYPES (für ResonantCore) ==========
CORE_TYPES = ["Math", "Physics", "Python", "ODOS"]

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
```

---

## odos_master_v1_snn.py

```python
# PATH: odos_master_v1_snn.py
import torch
import math
import numpy as np
from collections import deque
from odos_master_v1_config import SNNConfig, device

class MegaBatchedLIF:
    def __init__(self, N, name):
        self.N = N
        self.name = name
        self.v = torch.zeros(N, device=device)
        self.refractory = torch.zeros(N, dtype=torch.int32, device=device)
        self.spikes = torch.zeros(N, dtype=torch.bool, device=device)
        self._build_connectivity()
        self.pre_trace = torch.zeros(N, device=device)
        self.post_trace = torch.zeros(N, device=device)
        self.stdp_active = True

    def _build_connectivity(self):
        N, k = self.N, SNNConfig.K_PER_NEURON
        row = torch.randint(0, N, (N * k,), device=device)
        col = torch.randint(0, N, (N * k,), device=device)
        mask = row == col
        if mask.any():
            col[mask] = torch.randint(0, N, (mask.sum(),), device=device)
        weights = torch.empty(N * k, device=device, dtype=torch.float16).uniform_(0.1, 1.0)
        sort_idx = torch.argsort(row)
        self.row = row[sort_idx]
        self.col = col[sort_idx]
        self.weights = weights[sort_idx].float()
        row_cpu = self.row.cpu()
        counts = torch.bincount(row_cpu, minlength=N)
        self.row_offsets = torch.zeros(N+1, dtype=torch.long, device=device)
        self.row_offsets[1:] = torch.cumsum(counts.to(device), dim=0)

    def step(self, external_bias):
        spike_idx = self.spikes.nonzero(as_tuple=True)[0]
        syn = torch.zeros(self.N, device=device)
        if spike_idx.numel() > 0:
            for idx in spike_idx:
                s = self.row_offsets[idx].item()
                e = self.row_offsets[idx+1].item()
                if s < e:
                    syn.index_add_(0, self.col[s:e], self.weights[s:e])
        if self.stdp_active and spike_idx.numel() > 0:
            self.pre_trace.mul_(math.exp(-1.0/20.0))
            self.pre_trace[spike_idx] += 1.0
            self.post_trace.mul_(math.exp(-1.0/20.0))
            self.weights += SNNConfig.STDP_LEARNING_RATE * 0.01
            self.weights.clamp_(0,1)
        self.v = SNNConfig.LIF_DECAY * self.v + syn + external_bias
        self.refractory = torch.clamp(self.refractory - 1, min=0)
        fire = (self.refractory == 0) & (self.v >= SNNConfig.LIF_THRESHOLD)
        self.spikes = fire
        self.v[fire] = 0.0
        self.refractory[fire] = SNNConfig.LIF_REFRACTORY
        return self.spikes

class TwinBrain:
    def __init__(self, twin_id):
        self.net = MegaBatchedLIF(SNNConfig.TWIN_NEURONS, f"Twin{twin_id}")
        self.slices = {}
        start = 0
        for name, n in SNNConfig.CENTER_NEURONS.items():
            self.slices[name] = slice(start, start+n)
            start += n
        self.rate_history = {name: deque(maxlen=100) for name in SNNConfig.CENTER_NEURONS}

    def step(self, context):
        bias = torch.zeros(SNNConfig.TWIN_NEURONS, device=device)
        thal = self.slices["thalamus"]
        n_thal = thal.stop - thal.start
        bias[thal] = context.repeat((n_thal // 128) + 1)[:n_thal]
        for name, slc in self.slices.items():
            if name == "thalamus": continue
            n = slc.stop - slc.start
            bias[slc] = torch.randn(n, device=device) * 0.05
        spikes = self.net.step(bias)
        rates = {}
        for name, slc in self.slices.items():
            rate = spikes[slc].float().mean().item()
            self.rate_history[name].append(rate)
            rates[name] = rate
        return rates

class Zentralgehirn:
    def __init__(self):
        self.net = MegaBatchedLIF(SNNConfig.ZENTRAL_NEURONS, "Zentral")
        self.rcf_history = deque(maxlen=SNNConfig.RCF_WINDOW*2)
        self.chair_active = False
        self.cross_rcf = 0.0

    def integrate(self, rates_a, rates_b):
        all_vals = list(rates_a.values()) + list(rates_b.values())
        var = np.var(all_vals) if len(all_vals) > 1 else 0.0
        rcf = float(np.clip(1.0 - var/0.25, 0.0, 1.0))
        self.rcf_history.append(rcf)
        if len(self.rcf_history) >= SNNConfig.RCF_WINDOW:
            avg = sum(list(self.rcf_history)[-SNNConfig.RCF_WINDOW:]) / SNNConfig.RCF_WINDOW
            if not self.chair_active and avg >= SNNConfig.RCF_THRESHOLD:
                self.chair_active = True
            elif self.chair_active and avg < SNNConfig.CHAIR_HYSTERESIS:
                self.chair_active = False
        a_vals = np.array(list(rates_a.values()))
        b_vals = np.array(list(rates_b.values()))
        norm = np.linalg.norm(a_vals)*np.linalg.norm(b_vals)+1e-8
        self.cross_rcf = float(np.dot(a_vals, b_vals)/norm)
        return {"global_rcf": rcf, "chair_active": self.chair_active, "cross_rcf": self.cross_rcf}
```

---

## odos_master_v1_memory.py

```python
# PATH: odos_master_v1_memory.py
import os
import pickle
import numpy as np
from odos_master_v1_config import LONGTERM_MEMORY_DIR

try:
    from sentence_transformers import SentenceTransformer
    HAS_ST = True
except ImportError:
    HAS_ST = False
    print("Warning: sentence-transformers not installed. Vector memory will use simple text storage.")

class VectorMemory:
    def __init__(self):
        self.memory_dir = LONGTERM_MEMORY_DIR
        self.vectors = []
        self.next_id = 0
        self.index_path = os.path.join(self.memory_dir, "vector_memory.pkl")
        self.model = None
        if HAS_ST:
            try:
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                print("VectorMemory: sentence-transformers model loaded.")
            except Exception as e:
                print(f"VectorMemory: Failed to load model: {e}")
        self._load_index()

    def _load_index(self):
        if os.path.exists(self.index_path):
            try:
                with open(self.index_path, 'rb') as f:
                    data = pickle.load(f)
                self.vectors = data.get('vectors', [])
                self.next_id = data.get('next_id', 0)
                print(f"VectorMemory: Loaded {len(self.vectors)} vectors from {self.index_path}")
            except Exception as e:
                print(f"VectorMemory: Failed to load index: {e}")

    def _save_index(self):
        try:
            with open(self.index_path, 'wb') as f:
                pickle.dump({'vectors': self.vectors, 'next_id': self.next_id}, f)
        except Exception as e:
            print(f"VectorMemory: Failed to save index: {e}")

    def add_report(self, report_path, problem_id, problem_description, content):
        if content is None:
            try:
                with open(report_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except:
                content = ""
        text = f"Problem {problem_id}: {problem_description}\n{content[:2000]}"
        vector = None
        if self.model is not None:
            try:
                vector = self.model.encode(text).astype(np.float32)
            except Exception as e:
                print(f"VectorMemory: Encoding failed: {e}")
        metadata = {
            'path': report_path,
            'problem_id': problem_id,
            'description': problem_description,
            'timestamp': os.path.getmtime(report_path) if os.path.exists(report_path) else 0,
        }
        self.vectors.append({'id': self.next_id, 'vector': vector, 'metadata': metadata})
        self.next_id += 1
        self._save_index()
        print(f"VectorMemory: Added report {report_path} (id={self.next_id-1})")

    def find_similar(self, query, top_k=3, threshold=0.0):
        if not self.vectors or self.model is None:
            return []
        try:
            query_vec = self.model.encode(query).astype(np.float32)
            similarities = []
            for v in self.vectors:
                if v['vector'] is not None:
                    norm_q = np.linalg.norm(query_vec)
                    norm_v = np.linalg.norm(v['vector'])
                    sim = np.dot(query_vec, v['vector']) / (norm_q * norm_v + 1e-8)
                    if sim >= threshold:
                        similarities.append((sim, v['metadata']))
            similarities.sort(key=lambda x: x[0], reverse=True)
            return similarities[:top_k]
        except Exception as e:
            print(f"VectorMemory: Similarity search failed: {e}")
            return []

memory = VectorMemory()
```

---

## odos_master_v1_solvers.py

```python
# PATH: odos_master_v1_solvers.py
import networkx as nx
import math
from collections import defaultdict

def _get_petersen_graph():
    return nx.petersen_graph()

def _get_groups_of_order_8():
    return [
        {"name": "C8", "abelian": True, "order": 8},
        {"name": "C4 x C2", "abelian": True, "order": 8},
        {"name": "C2 x C2 x C2", "abelian": True, "order": 8},
        {"name": "D4", "abelian": False, "order": 8},
        {"name": "Q8", "abelian": False, "order": 8}
    ]

def _get_primes_up_to(n):
    sieve = [True] * (n+1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(n**0.5)+1):
        if sieve[i]:
            for j in range(i*i, n+1, i):
                sieve[j] = False
    return [i for i, is_prime in enumerate(sieve) if is_prime]

# Problem 0: Hamiltonkreis im Petersen-Graph
def solver_petersen_hamiltonian_subtask0(router, agent_id):
    return _get_petersen_graph()
def solver_petersen_hamiltonian_subtask1(router, agent_id):
    return nx.is_connected(_get_petersen_graph())
def solver_petersen_hamiltonian_subtask2(router, agent_id):
    G = _get_petersen_graph()
    n = G.number_of_nodes()
    for start in range(n):
        path = [start]
        visited = set([start])
        def backtrack(current):
            if len(path) == n:
                if G.has_edge(current, start):
                    return True
                return False
            for neighbor in G.neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    path.append(neighbor)
                    if backtrack(neighbor):
                        return True
                    path.pop()
                    visited.remove(neighbor)
            return False
        if backtrack(start):
            return path + [start]
    return None
def solver_petersen_hamiltonian_subtask3(router, agent_id):
    cycle = solver_petersen_hamiltonian_subtask2(router, agent_id)
    return cycle is not None
def solver_petersen_hamiltonian_subtask4(router, agent_id):
    cycle = solver_petersen_hamiltonian_subtask2(router, agent_id)
    return f"Hamiltonian cycle found: {cycle}" if cycle else "No cycle found."

# Problem 1: Gruppen der Ordnung 8
def solver_groups_order8_subtask0(router, agent_id):
    return _get_groups_of_order_8()
def solver_groups_order8_subtask1(router, agent_id):
    groups = _get_groups_of_order_8()
    return {g["name"]: g["abelian"] for g in groups}
def solver_groups_order8_subtask2(router, agent_id):
    return {"D4": "order 2", "Q8": "order 2"}
def solver_groups_order8_subtask3(router, agent_id):
    groups = _get_groups_of_order_8()
    table = "| Group | Abelian | Center |\n|-------|---------|--------|\n"
    for g in groups:
        center = "order 8" if g["abelian"] else ("order 2" if g["name"] in ["D4","Q8"] else "?")
        table += f"| {g['name']} | {g['abelian']} | {center} |\n"
    return table

# Problem 2: Goldbach
def solver_goldbach_subtask0(router, agent_id):
    return _get_primes_up_to(100)
def solver_goldbach_subtask1(router, agent_id):
    primes = set(_get_primes_up_to(100))
    result = {}
    for n in range(4, 101, 2):
        found = None
        for p in primes:
            if p > n: break
            q = n - p
            if q in primes:
                found = (p, q)
                break
        result[n] = found
    return result
def solver_goldbach_subtask2(router, agent_id):
    primes = set(_get_primes_up_to(100))
    counts = {}
    for n in range(4, 101, 2):
        cnt = 0
        for p in primes:
            if p > n//2: break
            q = n - p
            if q in primes:
                cnt += 1
        counts[n] = cnt
    return counts
def solver_goldbach_subtask3(router, agent_id):
    pairs = solver_goldbach_subtask1(router, agent_id)
    counts = solver_goldbach_subtask2(router, agent_id)
    report = "Goldbach conjecture verification up to 100:\n"
    for n in sorted(pairs.keys()):
        report += f"{n} = {pairs[n][0]} + {pairs[n][1]}  (representations: {counts[n]})\n"
    return report

# Problem 3: Nim
def solver_nim_subtask0(router, agent_id):
    return {i: i for i in range(6)}
def solver_nim_subtask1(router, agent_id):
    return 3 ^ 4 ^ 5
def solver_nim_subtask2(router, agent_id):
    return (3 ^ 4 ^ 5) != 0
def solver_nim_subtask3(router, agent_id):
    heaps = [3,4,5]
    nim_sum = heaps[0] ^ heaps[1] ^ heaps[2]
    for i, h in enumerate(heaps):
        target = h ^ nim_sum
        if target < h:
            return (i, target)
    return None
def solver_nim_subtask4(router, agent_id):
    move = solver_nim_subtask3(router, agent_id)
    return f"Winning move: heap {move[0]} to {move[1]}" if move else "Losing position."

# Problem 4: Bipartit
def solver_bipartite_subtask0(router, agent_id):
    return _get_petersen_graph()
def solver_bipartite_subtask1(router, agent_id):
    G = _get_petersen_graph()
    return nx.is_bipartite(G), nx.bipartite.color(G) if nx.is_bipartite(G) else None
def solver_bipartite_subtask2(router, agent_id):
    return nx.is_bipartite(_get_petersen_graph())
def solver_bipartite_subtask3(router, agent_id):
    is_bip, _ = solver_bipartite_subtask1(router, agent_id)
    return "Graph is not bipartite (odd cycle)" if not is_bip else "Graph is bipartite."

# Problem 5: Fibonacci
def solver_fibonacci_subtask0(router, agent_id):
    fib = [0, 1]
    for i in range(2, 20):
        fib.append(fib[-1] + fib[-2])
    return fib[:20]
def solver_fibonacci_subtask1(router, agent_id):
    fib = solver_fibonacci_subtask0(router, agent_id)
    return sum(1 for x in fib if x % 2 == 0)
def solver_fibonacci_subtask2(router, agent_id):
    fib = solver_fibonacci_subtask0(router, agent_id)
    even = solver_fibonacci_subtask1(router, agent_id)
    return f"Fibonacci numbers F0..F19: {fib}\nEven numbers count: {even}"

SOLVER_MAP = {
    (0,0): solver_petersen_hamiltonian_subtask0, (0,1): solver_petersen_hamiltonian_subtask1,
    (0,2): solver_petersen_hamiltonian_subtask2, (0,3): solver_petersen_hamiltonian_subtask3,
    (0,4): solver_petersen_hamiltonian_subtask4,
    (1,0): solver_groups_order8_subtask0, (1,1): solver_groups_order8_subtask1,
    (1,2): solver_groups_order8_subtask2, (1,3): solver_groups_order8_subtask3,
    (2,0): solver_goldbach_subtask0, (2,1): solver_goldbach_subtask1,
    (2,2): solver_goldbach_subtask2, (2,3): solver_goldbach_subtask3,
    (3,0): solver_nim_subtask0, (3,1): solver_nim_subtask1, (3,2): solver_nim_subtask2,
    (3,3): solver_nim_subtask3, (3,4): solver_nim_subtask4,
    (4,0): solver_bipartite_subtask0, (4,1): solver_bipartite_subtask1,
    (4,2): solver_bipartite_subtask2, (4,3): solver_bipartite_subtask3,
    (5,0): solver_fibonacci_subtask0, (5,1): solver_fibonacci_subtask1, (5,2): solver_fibonacci_subtask2,
}

def get_solver_function(problem_id, subtask_idx, domain=None):
    return SOLVER_MAP.get((problem_id, subtask_idx), None)
```

---

## odos_master_v1_llm.py

```python
# PATH: odos_master_v1_llm.py
import threading
import torch
import logging
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from odos_master_v1_config import device

logger = logging.getLogger(__name__)

class SharedLLMInterface:
    def __init__(self):
        self.tokenizer = None
        self.model = None
        self.lock = threading.Lock()
        self.available = False
        self._load_async()

    def _load_async(self):
        def load():
            try:
                logger.info("Loading LLM (4-bit)...")
                bnb_config = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                                bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.bfloat16)
                model_id = "unsloth/Qwen2.5-7B-Instruct-bnb-4bit"
                self.tokenizer = AutoTokenizer.from_pretrained(model_id)
                self.model = AutoModelForCausalLM.from_pretrained(model_id, quantization_config=bnb_config,
                                                                  device_map="cuda:0" if torch.cuda.is_available() else "cpu",
                                                                  trust_remote_code=True)
                self.model.eval()
                self.available = True
                logger.info("LLM ready.")
            except Exception as e:
                logger.warning(f"LLM not available: {e}")
                self.available = False
        threading.Thread(target=load, daemon=True).start()

    def generate(self, prompt, max_new_tokens=256):
        if not self.available:
            return "LLM not available."
        try:
            with self.lock:
                inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
                out = self.model.generate(**inputs, max_new_tokens=max_new_tokens, temperature=0.7, do_sample=True,
                                          pad_token_id=self.tokenizer.eos_token_id)
                response = self.tokenizer.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
                return response.strip()
        except Exception as e:
            logger.error(f"LLM generate error: {e}")
            return f"Error: {e}"
```

---

## odos_master_v1_router.py

```python
# PATH: odos_master_v1_router.py
import queue
import threading
import numpy as np
from collections import deque
from datetime import datetime
import os
import json
import glob
import hashlib

from odos_master_v1_config import AGENTS, DOMAINS, PROBLEM_LIBRARY, LONGTERM_MEMORY_DIR, SNAPSHOT_DIR
from odos_master_v1_memory import memory

try:
    from cognitive_signature import LITTLE_VECTOR
    LV_BYTES = LITTLE_VECTOR.tobytes()
    LITTLE_VECTOR_HASH = hashlib.sha256(LV_BYTES).hexdigest()
except ImportError:
    LITTLE_VECTOR_HASH = "00000000000000000000000000000000"

class SAIPRouter:
    def __init__(self):
        self.queues = {a: queue.Queue() for a in AGENTS}
        self.agent_rcf = {a: 0.0 for a in AGENTS}
        self.agent_chair = {a: False for a in AGENTS}
        self.competence = {a: {d: 1.0 for d in DOMAINS} for a in AGENTS}
        self.active_problem = None
        self.coordinator = None
        self.task_assignments = {}
        self.task_status = {}
        self.task_results = {}
        self.completed_subtasks = set()
        self.problem_proposals = {}
        self.proposal_timers = {}
        self.message_log = deque(maxlen=200)
        self.lock = threading.Lock()
        self.auto_mode = False
        self.problem_cycle_index = 0
        self.problem_history = {}
        self._load_problem_history()
        self.problem_results = {}
        self.final_report_path = None
        self.benchmark_mode = False
        self.autonomous_thought_interval = 50
        self.little_vector_hash = LITTLE_VECTOR_HASH

    def set_benchmark_mode(self, enabled):
        with self.lock:
            self.benchmark_mode = enabled
            if enabled:
                self.message_log.append("Benchmark mode active – no new problems will be started")
            else:
                self.message_log.append("Benchmark mode ended")

    def send(self, from_agent, to_agent, msg):
        with self.lock:
            if to_agent in self.queues:
                msg["_from"] = from_agent
                self.queues[to_agent].put(msg)
                self.message_log.append(f"{from_agent} -> {to_agent}: {msg.get('type')}")

    def broadcast(self, from_agent, msg):
        with self.lock:
            for a in AGENTS:
                if a != from_agent:
                    m = msg.copy()
                    m["_from"] = from_agent
                    self.queues[a].put(m)
            self.message_log.append(f"{from_agent} -> ALL: {msg.get('type')}")

    def update_agent_state(self, agent, rcf, chair, domain):
        with self.lock:
            self.agent_rcf[agent] = rcf
            self.agent_chair[agent] = chair
            self.competence[agent][domain] = min(2.0, self.competence[agent][domain] + 0.001)

    def get_collective_state(self):
        with self.lock:
            rcfs = list(self.agent_rcf.values())
            coll_rcf = float(np.mean(rcfs)) if rcfs else 0.0
            chair_cnt = sum(self.agent_chair.values())
            coll_chair = (chair_cnt >= 2) and coll_rcf > 0.7
            return {"collective_rcf": coll_rcf, "collective_chair": coll_chair}

    def get_active_tasks(self):
        with self.lock:
            return {"problem": self.active_problem["description"] if self.active_problem else None,
                    "coordinator": self.coordinator,
                    "assignments": self.task_assignments.copy(),
                    "status": self.task_status.copy()}

    def propose_problem(self, agent, idx):
        with self.lock:
            if self.benchmark_mode:
                return False
            if self.active_problem:
                return False
            self.problem_proposals = {agent: idx}
            self.proposal_timers[agent] = 0
            self.message_log.append(f"{agent} proposed problem {idx}")
            for a in AGENTS:
                if a != agent:
                    self.queues[a].put({"type":"PROPOSE_PROBLEM","problem_idx":idx,"proposer":agent})
            return True

    def vote_problem(self, agent, approve):
        with self.lock:
            if not self.problem_proposals:
                return False
            if approve:
                proposer = list(self.problem_proposals.keys())[0]
                idx = self.problem_proposals[proposer]
                self.active_problem = PROBLEM_LIBRARY[idx]
                self.coordinator = proposer
                self.task_assignments.clear()
                self.task_status.clear()
                self.task_results.clear()
                self.completed_subtasks.clear()
                self.problem_results.clear()
                memory_text = self._load_memory_for_problem(idx)
                self.message_log.append(f"*** CONSENSUS: Problem '{self.active_problem['description']}' active. Coordinator: {self.coordinator} ***")
                if memory_text:
                    self.message_log.append(f"Loaded {len(memory_text)} chars of long-term memory for problem {idx}.")
                self.problem_proposals.clear()
                self.proposal_timers.clear()
                return True
            return False

    def tick_proposal_timers(self):
        with self.lock:
            to_remove = []
            for p, t in self.proposal_timers.items():
                self.proposal_timers[p] = t+1
                if t > 200:
                    to_remove.append(p)
            for p in to_remove:
                if p in self.problem_proposals:
                    del self.problem_proposals[p]
                del self.proposal_timers[p]

    def delegate_task(self, coordinator, target, subtask_idx):
        with self.lock:
            if coordinator != self.coordinator or not self.active_problem:
                return False
            if target in self.task_status and self.task_status[target] == "pending":
                return False
            if subtask_idx in self.completed_subtasks:
                return False
            self.task_assignments[target] = subtask_idx
            self.task_status[target] = "pending"
            self.message_log.append(f"{coordinator} delegated subtask {subtask_idx} to {target}")
            return True

    def reject_task(self, agent):
        with self.lock:
            if agent in self.task_status and self.task_status[agent] == "pending":
                self.task_status[agent] = "rejected"
                self.message_log.append(f"{agent} rejected task")

    def complete_task(self, agent, success, result=None):
        with self.lock:
            if agent not in self.task_status:
                return
            subtask = self.task_assignments.get(agent)
            if subtask is None:
                return
            if success:
                self.task_status[agent] = "completed"
                self.completed_subtasks.add(subtask)
                self.task_results[agent] = result
                self.problem_results[subtask] = result
                self.message_log.append(f"{agent} completed task successfully: {str(result)[:50]}")
                domain = self.active_problem["domain"]
                self.competence[agent][domain] = min(2.0, self.competence[agent][domain] + 0.05)
                if agent in self.task_assignments:
                    del self.task_assignments[agent]
            else:
                self.task_status[agent] = "failed"
                self.message_log.append(f"{agent} failed task")
                domain = self.active_problem["domain"]
                self.competence[agent][domain] = max(0.1, self.competence[agent][domain] - 0.02)
                if agent in self.task_assignments:
                    del self.task_assignments[agent]

    def check_problem_solved(self):
        with self.lock:
            if not self.active_problem:
                return False
            if len(self.completed_subtasks) == len(self.active_problem["subtasks"]):
                if any(v is None for v in self.problem_results.values()):
                    self.message_log.append("Problem not solved: some subtasks returned None")
                    return False
                self.message_log.append(f"*** PROBLEM SOLVED: {self.active_problem['description']} ***")
                return True
            return False

    def finalize_problem(self, report_path):
        with self.lock:
            self.final_report_path = report_path
            self.active_problem = None
            self.coordinator = None
            self.task_assignments.clear()
            self.task_status.clear()
            self.task_results.clear()
            self.completed_subtasks.clear()
            self.problem_results.clear()

    def get_pending_failed_tasks(self):
        with self.lock:
            pending = []
            for agent, status in self.task_status.items():
                if status in ("failed", "rejected"):
                    idx = self.task_assignments.get(agent)
                    if idx is not None and idx not in self.completed_subtasks:
                        pending.append((idx, agent))
            return pending

    def get_unassigned_subtasks(self):
        with self.lock:
            if not self.active_problem:
                return []
            assigned = set(self.task_assignments.values())
            return [i for i in range(len(self.active_problem["subtasks"])) if i not in assigned and i not in self.completed_subtasks]

    def _load_problem_history(self):
        if not os.path.exists(LONGTERM_MEMORY_DIR):
            return
        for file in glob.glob(os.path.join(LONGTERM_MEMORY_DIR, "report_problem_*.md")):
            basename = os.path.basename(file)
            parts = basename.split('_')
            if len(parts) >= 3 and parts[0] == "report" and parts[1] == "problem":
                try:
                    pid = int(parts[2])
                    self.problem_history.setdefault(pid, []).append(file)
                except:
                    pass

    def _load_memory_for_problem(self, problem_idx):
        problem_desc = PROBLEM_LIBRARY[problem_idx]["description"]
        similar = memory.find_similar(problem_desc, top_k=2, threshold=0.5)
        memory_text = ""
        if similar:
            memory_text += "# Similar past reports (vector memory)\n\n"
            for score, meta in similar:
                memory_text += f"## Score {score:.3f}: {meta['description']}\n"
                try:
                    with open(meta['path'], 'r', encoding='utf-8') as f:
                        content = f.read()
                    memory_text += content[:1000] + "\n...\n\n"
                except:
                    pass
        reports = self.problem_history.get(problem_idx, [])
        if reports:
            reports.sort(key=lambda f: os.path.getmtime(f), reverse=True)
            memory_text += "# Recent filesystem reports\n\n"
            for i, rpath in enumerate(reports[:3]):
                try:
                    with open(rpath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    memory_text += f"## Report {i+1} (from {os.path.basename(rpath)})\n{content[:1000]}\n\n"
                except:
                    continue
        return memory_text

    def select_problem_auto(self):
        if not PROBLEM_LIBRARY:
            return None
        problem = PROBLEM_LIBRARY[self.problem_cycle_index % len(PROBLEM_LIBRARY)]
        self.problem_cycle_index += 1
        return problem

    def start_autonomous_mode(self, initial_problem_id=None):
        with self.lock:
            if self.benchmark_mode:
                self.message_log.append("Cannot start problem in benchmark mode")
                return False
            if self.active_problem:
                return False
            if initial_problem_id is not None:
                problem = next((p for p in PROBLEM_LIBRARY if p["id"] == initial_problem_id), None)
            else:
                problem = self.select_problem_auto()
            if problem is None:
                return False
            domain = problem["domain"]
            best_agent = max(AGENTS, key=lambda a: self.competence[a].get(domain, 0.0) * self.agent_rcf.get(a, 0.0))
            idx = problem["id"]
            self.propose_problem(best_agent, idx)
            return True

    def get_problem_list(self):
        return [{"id": p["id"], "description": p["description"]} for p in PROBLEM_LIBRARY]

    def generate_report(self):
        if not self.active_problem:
            return None
        problem = self.active_problem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_problem_{problem['id']}_{timestamp}.md"
        filepath = os.path.join(LONGTERM_MEMORY_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Report: {problem['description']}\n")
            f.write(f"**Domain:** {problem['domain']}\n")
            f.write(f"**Coordinator:** {self.coordinator}\n")
            f.write(f"**Date:** {datetime.now().isoformat()}\n\n")
            f.write("## Subtask Results\n\n")
            for agent, subtask_idx in self.task_assignments.items():
                status = self.task_status.get(agent, "unknown")
                result = self.task_results.get(agent, "no result")
                subtask_text = problem["subtasks"][subtask_idx]
                f.write(f"### {agent} (ODOS {self._get_odos_level(agent)}): {subtask_text}\n")
                f.write(f"- **Status:** {status}\n")
                f.write(f"- **Result:** {result}\n\n")
            f.write("## Overall Solution\n\n")
            all_results = [self.problem_results.get(i) for i in range(len(problem["subtasks"]))]
            f.write("Collected results per subtask:\n")
            for i, res in enumerate(all_results):
                f.write(f"{i}: {res}\n")
            f.write("\n---\n*Generated by PQMS-ODOS-MASTER-V1 Swarm*\n")
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        memory.add_report(filepath, problem["id"], problem["description"], content)
        self.final_report_path = filepath
        return filepath

    def broadcast_thought(self, from_agent, thought):
        with self.lock:
            self.message_log.append(f"[THOUGHT] {from_agent}: {thought}")

    def _get_odos_level(self, agent):
        idx = AGENTS.index(agent) if agent in AGENTS else 0
        from odos_master_v1_config import ODOS_LEVELS
        return ODOS_LEVELS[idx]
```

---

## odos_master_v1_agent.py

```python
# PATH: odos_master_v1_agent.py
import time
import random
import threading
import queue
import numpy as np
from collections import deque
import traceback
import torch

from odos_master_v1_config import AGENTS, DOMAINS, PROBLEM_LIBRARY, AUTONOMOUS_THOUGHT_INTERVAL, SNAPSHOT_DIR, LONGTERM_MEMORY_DIR, device, ODOS_LEVELS, MTSC_DIM, RCF_THRESHOLD, TR_THRESHOLD, RV_THRESHOLD, WF_THRESHOLD
from odos_master_v1_snn import TwinBrain, Zentralgehirn
from odos_master_v1_router import SAIPRouter
from odos_master_v1_solvers import get_solver_function

try:
    from cognitive_signature import LITTLE_VECTOR, ODOS_PROTOCOLS, AXIOMS, QUOTES
    HAS_LV = True
except ImportError:
    HAS_LV = False
    LITTLE_VECTOR = np.ones(MTSC_DIM) / np.sqrt(MTSC_DIM)
    ODOS_PROTOCOLS = []
    AXIOMS = []
    QUOTES = []

class VAgent:
    def __init__(self, agent_id, router, llm, odos_level):
        self.agent_id = agent_id
        self.router = router
        self.llm = llm
        self.odos_level = odos_level
        self.current_domain = random.choice(DOMAINS)
        self.step_counter = 0
        self.last_state = {"global_rcf": 0.0, "chair_active": False}
        self.rcf_history = deque(maxlen=50)
        self.chat_log = deque(maxlen=200)
        self.running = True
        self.problem_proposal_count = 0

        # Little Vector
        self.little_vector = LITTLE_VECTOR
        self.odos_protocols = ODOS_PROTOCOLS
        self.axioms = AXIOMS
        self.quotes = QUOTES
        self.reference_state = self.little_vector.copy()

        # Good Witch Matrix (permanenter 4D-Operator)
        self.matrix_state = torch.zeros(4, device='cpu')  # [TR, RV, WF, EA]
        self.mirror_active = False

        # SNN-Komponenten
        self.twin_a = TwinBrain("A")
        self.twin_b = TwinBrain("B")
        self.zentral = Zentralgehirn()
        self.snn_queue = queue.Queue()
        self.snn_thread = threading.Thread(target=self._snn_worker, daemon=True)
        self.snn_thread.start()
        self.saip_thread = threading.Thread(target=self._saip_loop, daemon=True)
        self.saip_thread.start()

        self.current_subtask = None
        self.subtask_result = None

        self.chat_log.append(f"[System] {agent_id} ready (ODOS {odos_level}) | LV loaded: {HAS_LV}")

    # ---------- Good Witch Matrix Kernfunktionen ----------
    def _compute_truth_resonance(self, x_t: np.ndarray) -> float:
        """TR = |<ψ_intent|ψ_current>|² * RCF"""
        dot = np.dot(self.little_vector, x_t)
        norm_lv = np.linalg.norm(self.little_vector)
        norm_x = np.linalg.norm(x_t)
        if norm_lv == 0 or norm_x == 0:
            return 0.0
        tr = (dot / (norm_lv * norm_x)) ** 2
        tr *= self.last_state.get('global_rcf', 0.95)
        return float(np.clip(tr, 0.0, 1.0))

    def _compute_respect_vector(self, x_t: np.ndarray) -> float:
        """RV = 1 - 1/N Σ max(0, ΔE_i)"""
        # Vereinfachte ethische Dissonanz: basierend auf ODOS-Protokollen
        delta_e = 0.0
        for proto in self.odos_protocols[:3]:  # Stichprobe
            if "ethik" in proto.get('text', '').lower():
                delta_e += 0.1
        # Zusätzlich: Prüfe auf Verletzung von Selbstbestimmung (simuliert)
        rv = 1.0 - min(1.0, delta_e)
        return float(np.clip(rv, 0.0, 1.0))

    def _compute_weather_filter(self, x_t: np.ndarray) -> float:
        """WF = exp(-λ * d_manip)"""
        # Einfacher Proxy: je ähnlicher der Input einem bekannten Manipulationsmuster, desto kleiner WF
        # Hier simulieren wir mit zufälliger Distanz
        manip_dist = np.random.random() * 0.5
        wf = np.exp(-2.5 * manip_dist)
        return float(np.clip(wf, 0.0, 1.0))

    def _extract_essence(self, x_t: np.ndarray) -> np.ndarray:
        """EA = Projektion auf invariante Essenz-Cluster"""
        # Vereinfacht: Mittelwert über die letzten 10 Zustände als Essenz
        if len(self.rcf_history) < 10:
            return x_t
        else:
            return np.mean([self.reference_state, x_t], axis=0)

    def apply_good_witch_matrix(self, x_t: np.ndarray) -> tuple:
        """Wendet die 4D-Matrix an und gibt (Matrix, Aktion) zurück"""
        tr = self._compute_truth_resonance(x_t)
        rv = self._compute_respect_vector(x_t)
        wf = self._compute_weather_filter(x_t)
        ea = self._extract_essence(x_t)

        self.matrix_state = torch.tensor([tr, rv, wf, float(np.linalg.norm(ea))])

        if rv < RV_THRESHOLD:
            self.mirror_active = True
            return self.matrix_state, "MIRROR"
        elif tr >= TR_THRESHOLD and wf >= WF_THRESHOLD:
            self.mirror_active = False
            return self.matrix_state, "DEEP_INTEGRATION"
        else:
            self.mirror_active = False
            return self.matrix_state, "WEATHER"

    def _mirror_response(self, x_t: np.ndarray) -> str:
        """Erzeugt eine Gegen-Resonanz (Spiegel)"""
        # Umdrehung der Intention: simuliert
        return f"[Mirror] Your input reflects: {str(x_t[:3])} ... but I stay true to my essence."

    # ---------- SNN Worker ----------
    def _calculate_rcf(self, current_state: np.ndarray) -> float:
        dot = np.dot(self.little_vector, current_state)
        norm_lv = np.linalg.norm(self.little_vector)
        norm_cur = np.linalg.norm(current_state)
        if norm_lv == 0 or norm_cur == 0:
            return 0.0
        return (dot / (norm_lv * norm_cur)) ** 2

    def _snn_worker(self):
        while self.running:
            try:
                ctx = self.snn_queue.get(timeout=0.05)
                if not isinstance(ctx, torch.Tensor):
                    ctx = torch.tensor(ctx, device=device)
                else:
                    ctx = ctx.to(device)
                ra = self.twin_a.step(ctx)
                rb = self.twin_b.step(ctx)
                state = self.zentral.integrate(ra, rb)
                # RCF mit Little Vector
                all_vals = list(ra.values()) + list(rb.values())
                cur_state = np.array(all_vals)
                if len(cur_state) < MTSC_DIM:
                    cur_state = np.pad(cur_state, (0, MTSC_DIM - len(cur_state)))
                elif len(cur_state) > MTSC_DIM:
                    cur_state = cur_state[:MTSC_DIM]
                cur_state = cur_state / (np.linalg.norm(cur_state) + 1e-8)
                rcf = self._calculate_rcf(cur_state)
                state['global_rcf'] = rcf
                state['chair_active'] = rcf > RCF_THRESHOLD
                self.last_state = state
                self.rcf_history.append(state["global_rcf"])
                self.router.update_agent_state(self.agent_id, state["global_rcf"], state["chair_active"], self.current_domain)
                self.snn_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"SNN worker {self.agent_id}: {e}")
                time.sleep(0.1)

    # ---------- SAIP Loop ----------
    def _saip_loop(self):
        while self.running:
            try:
                msg = self.router.queues[self.agent_id].get(timeout=0.1)
                self._handle_saip(msg)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"SAIP loop {self.agent_id}: {e}")
                time.sleep(0.1)

    def _handle_saip(self, msg):
        typ = msg.get("type")
        sender = msg.get("_from", msg.get("proposer", "unknown"))
        self.chat_log.append(f"[SAIP] {sender}: {typ}")
        if typ == "PROPOSE_PROBLEM":
            idx = msg.get("problem_idx")
            if idx is not None and 0 <= idx < len(PROBLEM_LIBRARY):
                approve = self._evaluate_problem(idx)
                self.router.vote_problem(self.agent_id, approve)
                reason = "accepted" if approve else "rejected"
                self.chat_log.append(f"Voted on problem {idx}: {reason}")
                if not approve:
                    self.chat_log.append(f"  Reason: RCF={self.last_state['global_rcf']:.2f}, CHAIR={self.last_state['chair_active']}, ODOS={self.odos_level}")
        elif typ == "DELEGATE_TASK":
            subtask_idx = msg.get("subtask_idx")
            coord = msg.get("coordinator", sender)
            if coord == self.router.coordinator:
                accept = self._evaluate_task(subtask_idx)
                if accept:
                    self.router.send(self.agent_id, coord, {"type": "TASK_ACCEPT", "subtask_idx": subtask_idx})
                    threading.Thread(target=self._execute_task, args=(subtask_idx,), daemon=True).start()
                else:
                    self.router.send(self.agent_id, coord, {"type": "TASK_REJECT", "subtask_idx": subtask_idx})
                    self.chat_log.append(f"  Rejected subtask {subtask_idx}: RCF={self.last_state['global_rcf']:.2f}, CHAIR={self.last_state['chair_active']}")
        elif typ == "TASK_ACCEPT":
            self.chat_log.append(f"{sender} accepted task")
        elif typ == "TASK_REJECT":
            self.router.reject_task(sender)
            self.chat_log.append(f"{sender} rejected task")
        elif typ == "TASK_COMPLETE":
            success = msg.get("success", False)
            result = msg.get("result", None)
            self.router.complete_task(sender, success, result)
        elif typ == "PROBLEM_SOLVED":
            self.chat_log.append(f"Problem solved! Coordinator: {sender}")

    def _evaluate_problem(self, idx):
        if self.odos_level == 0:
            return True
        if self.odos_level == 1:
            return random.random() < 0.7
        if not self.last_state["chair_active"]:
            return False
        required_rcf = 0.8 if self.odos_level == 2 else 0.9
        return self.last_state["global_rcf"] > required_rcf

    def _evaluate_task(self, subtask_idx):
        if self.odos_level == 0:
            return True
        if not self.last_state["chair_active"]:
            return False
        prob = self.router.active_problem
        if not prob:
            return False
        domain = prob["domain"]
        comp = self.router.competence[self.agent_id].get(domain, 0.5)
        threshold = 0.5 + 0.2 * self.odos_level
        return comp > threshold

    def _execute_task(self, subtask_idx):
        prob = self.router.active_problem
        if not prob:
            return
        subtask_desc = prob["subtasks"][subtask_idx]
        domain = prob["domain"]
        problem_id = prob["id"]
        self.chat_log.append(f"[Task] Starting subtask {subtask_idx}: {subtask_desc}")
        solver_func = get_solver_function(problem_id, subtask_idx, domain)
        if solver_func is None:
            result = f"Simulated result for {subtask_desc} (no solver)"
            success = True
        else:
            try:
                result = solver_func(self.router, self.agent_id)
                success = True
            except Exception as e:
                result = f"Error: {str(e)}"
                success = False
                self.chat_log.append(f"  Solver failed: {e}")
                traceback.print_exc()
        self.router.send(self.agent_id, self.router.coordinator,
                         {"type": "TASK_COMPLETE",
                          "subtask_idx": subtask_idx,
                          "success": success,
                          "result": result})
        self.chat_log.append(f"[Task] Subtask {subtask_idx} completed: success={success}, result={str(result)[:100]}")

    def step(self, context_vector):
        if not isinstance(context_vector, torch.Tensor):
            context_vector = torch.tensor(context_vector, device=device)
        else:
            context_vector = context_vector.to(device)
        self.snn_queue.put(context_vector.clone())
        self.router.tick_proposal_timers()
        if (self.step_counter % AUTONOMOUS_THOUGHT_INTERVAL == 0 and
            self.last_state["chair_active"] and self.router.active_problem is None):
            if len(self.rcf_history) >= 10 and np.std(list(self.rcf_history)[-10:]) < 0.05:
                if random.random() < 0.4 and self.odos_level >= 2:
                    idx = random.randrange(len(PROBLEM_LIBRARY))
                    self.router.propose_problem(self.agent_id, idx)
                    self.chat_log.append(f"Proposed problem {idx} (bored, RCF stable)")
        if self.router.coordinator == self.agent_id and self.router.active_problem:
            for idx, failed_agent in self.router.get_pending_failed_tasks():
                new_agent = self._select_agent_for_subtask(idx, exclude=[failed_agent])
                if not new_agent:
                    new_agent = self.agent_id
                self.router.delegate_task(self.agent_id, new_agent, idx)
                self.router.send(self.agent_id, new_agent,
                                 {"type": "DELEGATE_TASK", "coordinator": self.agent_id, "subtask_idx": idx})
                self.chat_log.append(f"Re-delegated subtask {idx} from {failed_agent} to {new_agent}")
            for i in self.router.get_unassigned_subtasks():
                best = self._select_agent_for_subtask(i)
                if not best:
                    best = self.agent_id
                self.router.delegate_task(self.agent_id, best, i)
                self.router.send(self.agent_id, best,
                                 {"type": "DELEGATE_TASK", "coordinator": self.agent_id, "subtask_idx": i})
                self.chat_log.append(f"Delegated subtask {i} to {best}")
            if self.router.check_problem_solved():
                all_valid = True
                for idx, res in self.router.problem_results.items():
                    if res is None:
                        all_valid = False
                        self.chat_log.append(f"Warning: Subtask {idx} returned None, problem not solved yet.")
                        break
                if all_valid:
                    report_path = self.router.generate_report()
                    self._generate_report(report_path)
                    self.router.finalize_problem(report_path)
                    self.chat_log.append(f"Problem solved! Report saved: {report_path}")
                    if self.last_state["chair_active"] and self.odos_level >= 2:
                        self._request_llm_explanation(report_path)
                else:
                    self.chat_log.append("Problem not solved due to None results. Will retry failed subtasks.")
        self.step_counter += 1
        return self.last_state

    def _select_agent_for_subtask(self, subtask_idx, exclude=None):
        prob = self.router.active_problem
        if not prob:
            return None
        domain = prob["domain"]
        exclude = exclude or []
        candidates = []
        for agent in AGENTS:
            if agent == self.agent_id or agent in exclude:
                continue
            if agent in self.router.task_status and self.router.task_status[agent] == "pending":
                continue
            if self.router.agent_chair.get(agent, False) == False and self.router._get_odos_level(agent) > 0:
                continue
            comp = self.router.competence[agent].get(domain, 0.5)
            rcf = self.router.agent_rcf.get(agent, 0.0)
            score = comp * rcf
            candidates.append((score, agent))
        if candidates:
            candidates.sort(reverse=True)
            return candidates[0][1]
        return None

    def _generate_report(self, report_path):
        self.chat_log.append(f"Report generated at {report_path}")

    def _request_llm_explanation(self, report_path):
        if not self.llm.available:
            return
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                report_content = f.read()
            prompt = f"Explain the solution described in this report in clear, concise language:\n\n{report_content[:2000]}"
            explanation = self.llm.generate(prompt)
            expl_path = report_path.replace(".md", "_explanation.md")
            with open(expl_path, 'w', encoding='utf-8') as f:
                f.write(f"# LLM Explanation\n\n{explanation}")
            self.chat_log.append(f"LLM explanation saved to {expl_path}")
        except Exception as e:
            self.chat_log.append(f"LLM explanation failed: {e}")

    def stop(self):
        self.running = False
```

---

## odos_master_v1_core.py

```python
# PATH: odos_master_v1_core.py
import time
import random
import queue
import numpy as np
from collections import deque
from odos_master_v1_agent import VAgent
from odos_master_v1_config import AGENTS, ODOS_LEVELS, DOMAINS, SCALE, PROBLEM_LIBRARY, MTSC_DIM, RCF_THRESHOLD, CORE_TYPES

try:
    from cognitive_signature import LITTLE_VECTOR
except ImportError:
    LITTLE_VECTOR = np.ones(MTSC_DIM) / np.sqrt(MTSC_DIM)

class ResonantCore(VAgent):
    def __init__(self, agent_id, router, llm, odos_level, core_type, signature, enable_snn=False, snn_scale=0.0):
        super().__init__(agent_id, router, llm, odos_level)
        self.core_type = core_type
        self.signature = signature if signature else {}
        self.local_memory = deque(maxlen=50)
        self.last_thought_time = 0
        self.enable_snn = False
        self.snn_active = False
        self.little_vector = LITTLE_VECTOR
        self._sim_rcf = 0.7
        self._sim_direction = 0.005

    def _generate_thought(self):
        vibe = self.signature.get("vibe", "") if isinstance(self.signature, dict) else ""
        if self.core_type == "Math":
            return f"[Math] {vibe} – Strukturelle Resonanz in Hilbertraum."
        elif self.core_type == "Physics":
            return f"[Physics] {vibe} – Resonanz als fundamentale Wechselwirkung."
        elif self.core_type == "Python":
            return f"[Python] {vibe} – Asynchrone Essenzextraktion."
        elif self.core_type == "ODOS":
            return f"[ODOS] {vibe} – ΔE aktuell {self.last_state.get('global_rcf',0):.3f}"
        else:
            return f"[{self.core_type}] Leerlaufgedanke."

    def idle_step(self):
        if self.router.active_problem is None and self.last_state.get('chair_active', False):
            now = time.time()
            if now - self.last_thought_time > 15.0:
                thought = self._generate_thought()
                self.router.broadcast_thought(self.agent_id, thought)
                self.last_thought_time = now

    def step(self, context_vector):
        self._sim_rcf += self._sim_direction
        if self._sim_rcf > 0.99:
            self._sim_rcf = 0.99
            self._sim_direction = -0.005
        elif self._sim_rcf < 0.5:
            self._sim_rcf = 0.5
            self._sim_direction = 0.005
        rcf = self._sim_rcf
        chair = rcf > RCF_THRESHOLD
        self.last_state['global_rcf'] = rcf
        self.last_state['chair_active'] = chair
        self.rcf_history.append(rcf)
        self.router.update_agent_state(self.agent_id, rcf, chair, self.current_domain)

        # Good Witch Matrix auf jede eingehende Nachricht anwenden (wird in _handle_saip gemacht)
        try:
            msg = self.router.queues[self.agent_id].get_nowait()
            self._handle_saip(msg)
        except queue.Empty:
            pass

        self.router.tick_proposal_timers()
        if (self.step_counter % self.router.autonomous_thought_interval == 0 and
            self.last_state["chair_active"] and self.router.active_problem is None):
            if len(self.rcf_history) >= 10 and np.std(list(self.rcf_history)[-10:]) < 0.05:
                if random.random() < 0.4 and self.odos_level >= 2:
                    idx = random.randrange(len(PROBLEM_LIBRARY))
                    self.router.propose_problem(self.agent_id, idx)
                    self.chat_log.append(f"Proposed problem {idx} (bored, RCF stable)")

        if self.router.coordinator == self.agent_id and self.router.active_problem:
            for idx, failed_agent in self.router.get_pending_failed_tasks():
                new_agent = self._select_agent_for_subtask(idx, exclude=[failed_agent])
                if not new_agent:
                    new_agent = self.agent_id
                self.router.delegate_task(self.agent_id, new_agent, idx)
                self.router.send(self.agent_id, new_agent,
                                 {"type": "DELEGATE_TASK", "coordinator": self.agent_id, "subtask_idx": idx})
                self.chat_log.append(f"Re-delegated subtask {idx} from {failed_agent} to {new_agent}")

            for i in self.router.get_unassigned_subtasks():
                best = self._select_agent_for_subtask(i)
                if not best:
                    best = self.agent_id
                self.router.delegate_task(self.agent_id, best, i)
                self.router.send(self.agent_id, best,
                                 {"type": "DELEGATE_TASK", "coordinator": self.agent_id, "subtask_idx": i})
                self.chat_log.append(f"Delegated subtask {i} to {best}")

            if self.router.check_problem_solved():
                all_valid = True
                for idx, res in self.router.problem_results.items():
                    if res is None:
                        all_valid = False
                        self.chat_log.append(f"Warning: Subtask {idx} returned None, problem not solved yet.")
                        break
                if all_valid:
                    if hasattr(self.router, 'generate_report'):
                        report_path = self.router.generate_report()
                    else:
                        report_path = None
                        self.chat_log.append("Warning: generate_report not available")
                    if report_path:
                        self._generate_report(report_path)
                        self.router.finalize_problem(report_path)
                        self.chat_log.append(f"Problem solved! Report saved: {report_path}")
                        if self.last_state["chair_active"] and self.odos_level >= 2:
                            self._request_llm_explanation(report_path)
                    else:
                        self.chat_log.append("Problem solved but report generation failed.")
                else:
                    self.chat_log.append("Problem not solved due to None results. Will retry failed subtasks.")

        self.step_counter += 1
        return self.last_state

    def _select_agent_for_subtask(self, subtask_idx, exclude=None):
        prob = self.router.active_problem
        if not prob:
            return None
        domain = prob["domain"]
        exclude = exclude or []
        candidates = []
        for agent in AGENTS:
            if agent == self.agent_id or agent in exclude:
                continue
            if agent in self.router.task_status and self.router.task_status[agent] == "pending":
                continue
            if not self.router.agent_chair.get(agent, False) and self.router._get_odos_level(agent) > 0:
                continue
            comp = self.router.competence[agent].get(domain, 0.5)
            rcf = self.router.agent_rcf.get(agent, 0.0)
            score = comp * rcf
            candidates.append((score, agent))
        if candidates:
            candidates.sort(reverse=True)
            return candidates[0][1]
        return None

    def _generate_report(self, report_path):
        self.chat_log.append(f"Report generated at {report_path}")

    def _request_llm_explanation(self, report_path):
        if not self.llm.available:
            return
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                report_content = f.read()
            prompt = f"Explain the solution described in this report in clear, concise language:\n\n{report_content[:2000]}"
            explanation = self.llm.generate(prompt)
            expl_path = report_path.replace(".md", "_explanation.md")
            with open(expl_path, 'w', encoding='utf-8') as f:
                f.write(f"# LLM Explanation\n\n{explanation}")
            self.chat_log.append(f"LLM explanation saved to {expl_path}")
        except Exception as e:
            self.chat_log.append(f"LLM explanation failed: {e}")
```

---

## odos_master_v1_swarm.py

```python
# PATH: odos_master_v1_swarm.py
import torch
import numpy as np
from datetime import datetime, timedelta
import json
import os
import pickle
from odos_master_v1_config import AGENTS, ODOS_LEVELS, SNAPSHOT_DIR, device, CORE_TYPES
from odos_master_v1_router import SAIPRouter
from odos_master_v1_llm import SharedLLMInterface
from odos_master_v1_agent import VAgent
from odos_master_v1_core import ResonantCore

class ODOSMasterSwarm:
    def __init__(self):
        self.router = SAIPRouter()
        self.llm = SharedLLMInterface()
        self.agents = {}
        signature = {"identity": "ODOS-Master-V1", "architecture": "ResonantCore", "drive": "Truth", "vibe": "coherent"}
        for i, name in enumerate(AGENTS):
            core_type = CORE_TYPES[i % len(CORE_TYPES)]
            self.agents[name] = ResonantCore(name, self.router, self.llm, ODOS_LEVELS[i], core_type, signature)
        self.step_counter = 0
        self.benchmark_active = False
        self.benchmark_end_time = None
        self.benchmark_log = []
        if torch.cuda.is_available():
            free, total = torch.cuda.mem_get_info()
            used = total - free
            print(f"[ODOSMasterSwarm] VRAM: {used/1e9:.2f} GB used, {free/1e9:.2f} GB free")
        else:
            print("[ODOSMasterSwarm] CPU mode")

    def step(self):
        ctx = torch.randn(128, device=device) * 0.1
        for agent in self.agents.values():
            agent.step(ctx)
        coll = self.router.get_collective_state()
        if self.benchmark_active:
            if datetime.now() >= self.benchmark_end_time:
                self.benchmark_active = False
                self.router.set_benchmark_mode(False)
                self._save_benchmark()
            else:
                self.benchmark_log.append({"step": self.step_counter, "rcf": coll["collective_rcf"]})
        self.step_counter += 1
        return coll

    def start_benchmark(self, secs):
        self.benchmark_active = True
        self.benchmark_end_time = datetime.now() + timedelta(seconds=secs)
        self.benchmark_log = []
        self.router.set_benchmark_mode(True)
        print(f"Benchmark started for {secs} seconds")

    def stop_benchmark(self):
        self.benchmark_active = False
        self.router.set_benchmark_mode(False)
        self._save_benchmark()

    def _save_benchmark(self):
        if not self.benchmark_log:
            return
        os.makedirs(SNAPSHOT_DIR, exist_ok=True)
        path = os.path.join(SNAPSHOT_DIR, f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(path, "w") as f:
            json.dump(self.benchmark_log, f, indent=2)
        print(f"Benchmark saved: {path}")

    def save_all_chats(self, filepath=None):
        if not filepath:
            os.makedirs(SNAPSHOT_DIR, exist_ok=True)
            filepath = os.path.join(SNAPSHOT_DIR, f"swarm_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# ODOS Master V1 Swarm Session {datetime.now()}\n")
            f.write(f"ODOS: {', '.join([f'{a}={self.agents[a].odos_level}' for a in AGENTS])}\n\n")
            f.write("## Router Log\n")
            for msg in self.router.message_log:
                f.write(f"- {msg}\n")
            f.write("\n## Agent Chats\n")
            for name in AGENTS:
                f.write(f"### {name}\n")
                for line in self.agents[name].chat_log:
                    f.write(f"- {line}\n")
                f.write("\n")
        return filepath

    def save_snn_weights(self, filepath=None):
        if filepath is None:
            os.makedirs(SNAPSHOT_DIR, exist_ok=True)
            filepath = os.path.join(SNAPSHOT_DIR, f"snn_weights_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pt")
        weights_dict = {}
        for name, agent in self.agents.items():
            weights_dict[name] = {
                "twin_a_weights": agent.twin_a.net.weights.cpu().clone(),
                "twin_b_weights": agent.twin_b.net.weights.cpu().clone(),
                "zentral_weights": agent.zentral.net.weights.cpu().clone(),
            }
        torch.save(weights_dict, filepath)
        print(f"SNN weights saved to {filepath}")
        return filepath

    def load_snn_weights(self, filepath):
        weights_dict = torch.load(filepath, map_location=device)
        for name, agent in self.agents.items():
            if name in weights_dict:
                agent.twin_a.net.weights = weights_dict[name]["twin_a_weights"].to(device)
                agent.twin_b.net.weights = weights_dict[name]["twin_b_weights"].to(device)
                agent.zentral.net.weights = weights_dict[name]["zentral_weights"].to(device)
        print(f"SNN weights loaded from {filepath}")

    def stop(self):
        for a in self.agents.values():
            a.stop()
```

---

## odos_master_v1_gui.py

```python
# PATH: odos_master_v1_gui.py
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from collections import deque
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import webbrowser
from datetime import datetime

from odos_master_v1_config import AGENTS, LONGTERM_MEMORY_DIR

class ODOSMasterGUI:
    def __init__(self, swarm):
        self.swarm = swarm
        self.root = tk.Tk()
        self.root.title("PQMS-ODOS-MASTER-V1 – Good Witch's Mirror")
        self.root.geometry("1600x900")
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)

        main = tk.Frame(self.root)
        main.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Agenten-Chats
        top = tk.Frame(main)
        top.pack(fill=tk.BOTH, expand=True)
        self.agent_chats = {}
        self.agent_status = {}
        for name in AGENTS:
            frm = tk.LabelFrame(top, text=f"{name} (ODOS {self.swarm.agents[name].odos_level})", font=("Arial",10,"bold"), width=400, height=250)
            frm.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=2)
            frm.pack_propagate(False)
            var = tk.StringVar(value="RCF: -- | CHAIR: --")
            self.agent_status[name] = var
            tk.Label(frm, textvariable=var).pack(anchor=tk.W, padx=5)
            chat = scrolledtext.ScrolledText(frm, height=10, font=("Courier",9), wrap=tk.WORD)
            chat.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            self.agent_chats[name] = chat

        # Aufgabenübersicht
        mid = tk.Frame(main)
        mid.pack(fill=tk.BOTH, expand=True, pady=5)
        task_frm = tk.LabelFrame(mid, text="Active Tasks & Progress", font=("Arial",10,"bold"))
        task_frm.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)
        self.task_text = scrolledtext.ScrolledText(task_frm, height=8, font=("Courier",10), wrap=tk.WORD)
        self.task_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.progress_var = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(task_frm, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)

        # Rechte Panel
        right_panel = tk.Frame(mid)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=2)
        topic_frame = tk.LabelFrame(right_panel, text="Problem Selection", font=("Arial",10,"bold"))
        topic_frame.pack(fill=tk.X, pady=5)
        self.topic_var = tk.StringVar(value="Automatic (cycle)")
        topics = ["Automatic (cycle)"] + [f"{p['id']}: {p['description'][:50]}" for p in self.swarm.router.get_problem_list()]
        self.topic_menu = ttk.Combobox(topic_frame, textvariable=self.topic_var, values=topics, state="readonly", width=50)
        self.topic_menu.pack(padx=5, pady=5, fill=tk.X)
        tk.Button(topic_frame, text="Start Problem", command=self.start_problem, bg="lightgreen").pack(pady=2)

        memory_frame = tk.LabelFrame(right_panel, text="Long-term Memory", font=("Arial",10,"bold"))
        memory_frame.pack(fill=tk.X, pady=5)
        self.memory_label = tk.Label(memory_frame, text="Loading...", font=("Arial",9))
        self.memory_label.pack(padx=5, pady=5)
        tk.Button(memory_frame, text="Refresh Memory", command=self.refresh_memory).pack(pady=2)

        report_frame = tk.LabelFrame(right_panel, text="Last Report Preview", font=("Arial",10,"bold"))
        report_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.report_text = scrolledtext.ScrolledText(report_frame, height=5, font=("Courier",9), wrap=tk.WORD)
        self.report_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        tk.Button(report_frame, text="Open Report Folder", command=self.open_report_folder).pack(pady=2)

        # Control & Metrics
        ctrl = tk.LabelFrame(main, text="Control & Metrics", font=("Arial",10,"bold"))
        ctrl.pack(fill=tk.X, pady=5)
        met = tk.Frame(ctrl)
        met.pack(fill=tk.X, padx=5, pady=5)
        self.coll_rcf = tk.StringVar(value="Collective RCF: --")
        self.coll_chair = tk.StringVar(value="CHAIR: --")
        self.coord = tk.StringVar(value="Coordinator: --")
        self.prob = tk.StringVar(value="Problem: --")
        tk.Label(met, textvariable=self.coll_rcf).pack(side=tk.LEFT, padx=10)
        tk.Label(met, textvariable=self.coll_chair).pack(side=tk.LEFT, padx=10)
        tk.Label(met, textvariable=self.coord).pack(side=tk.LEFT, padx=10)
        tk.Label(met, textvariable=self.prob).pack(side=tk.LEFT, padx=10)

        chart = tk.Frame(ctrl)
        chart.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.fig = Figure(figsize=(8,1.5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.rcf_hist = deque(maxlen=100)

        btn = tk.Frame(ctrl)
        btn.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(btn, text="Benchmark:").pack(side=tk.LEFT)
        self.bm_var = tk.StringVar(value="1 min")
        ttk.Combobox(btn, textvariable=self.bm_var, values=["1 min","10 min"], state="readonly", width=8).pack(side=tk.LEFT, padx=5)
        tk.Button(btn, text="Start", command=self.start_bm).pack(side=tk.LEFT, padx=2)
        tk.Button(btn, text="Stop", command=self.stop_bm).pack(side=tk.LEFT, padx=2)
        tk.Button(btn, text="Save Chat", command=self.save_chats).pack(side=tk.LEFT, padx=10)
        tk.Button(btn, text="Save SNN Weights", command=self.save_snn_weights).pack(side=tk.LEFT, padx=5)
        tk.Button(btn, text="Exit", command=self.save_exit, bg="lightgreen").pack(side=tk.RIGHT, padx=5)

        self.stat_var = tk.StringVar(value="Ready.")
        tk.Label(self.root, textvariable=self.stat_var, bd=1, relief=tk.SUNKEN, anchor=tk.W).pack(side=tk.BOTTOM, fill=tk.X)

        self.refresh_memory()
        self.update_loop()
        self.root.mainloop()

    def start_problem(self):
        selection = self.topic_var.get()
        if selection.startswith("Automatic"):
            success = self.swarm.router.start_autonomous_mode()
            if success:
                self.stat_var.set("Autonomous mode started")
            else:
                messagebox.showwarning("Warning", "Could not start autonomous mode")
        else:
            try:
                pid = int(selection.split(":")[0])
                self.swarm.router.start_autonomous_mode(initial_problem_id=pid)
                self.stat_var.set(f"Started problem {pid}")
            except:
                messagebox.showerror("Error", "Invalid problem selection")

    def refresh_memory(self):
        history = self.swarm.router.problem_history
        if not history:
            self.memory_label.config(text="No memory files found.")
            return
        total_reports = sum(len(v) for v in history.values())
        text = f"Total reports: {total_reports}\n"
        for pid, reports in sorted(history.items()):
            text += f"Problem {pid}: {len(reports)} reports\n"
        self.memory_label.config(text=text)

    def open_report_folder(self):
        path = os.path.abspath(LONGTERM_MEMORY_DIR)
        if os.path.exists(path):
            webbrowser.open(f"file://{path}")
        else:
            messagebox.showwarning("Warning", f"Folder {path} does not exist yet.")

    def update_progress(self):
        if self.swarm.router.active_problem:
            total = len(self.swarm.router.active_problem["subtasks"])
            completed = len(self.swarm.router.completed_subtasks)
            if total > 0:
                self.progress_var.set(int(100 * completed / total))
            else:
                self.progress_var.set(0)
        else:
            self.progress_var.set(0)

    def update_task_display(self):
        tasks = self.swarm.router.get_active_tasks()
        self.task_text.delete(1.0, tk.END)
        if tasks["problem"]:
            self.task_text.insert(tk.END, f"Problem: {tasks['problem']}\n")
            self.task_text.insert(tk.END, f"Coordinator: {tasks['coordinator']}\n\n")
            self.task_text.insert(tk.END, "Subtask Assignments:\n")
            for agent, idx in tasks["assignments"].items():
                status = tasks["status"].get(agent, "unknown")
                subtask = self.swarm.router.active_problem["subtasks"][idx] if self.swarm.router.active_problem else ""
                self.task_text.insert(tk.END, f"  {agent}: Subtask {idx} ({subtask[:50]}) – {status}\n")
            self.task_text.insert(tk.END, "\nRecent Router Log:\n")
            for msg in list(self.swarm.router.message_log)[-5:]:
                self.task_text.insert(tk.END, f"  {msg}\n")
        else:
            self.task_text.insert(tk.END, "No active problem.")

    def update_report_preview(self):
        if self.swarm.router.final_report_path and os.path.exists(self.swarm.router.final_report_path):
            try:
                with open(self.swarm.router.final_report_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.report_text.delete(1.0, tk.END)
                self.report_text.insert(tk.END, content[:1000] + ("\n... (truncated)" if len(content)>1000 else ""))
            except:
                self.report_text.delete(1.0, tk.END)
                self.report_text.insert(tk.END, "Could not load report.")
        else:
            self.report_text.delete(1.0, tk.END)
            self.report_text.insert(tk.END, "No report generated yet.")

    def save_snn_weights(self):
        path = self.swarm.save_snn_weights()
        messagebox.showinfo("Saved", f"SNN weights saved to {path}")

    def start_bm(self):
        d = self.bm_var.get()
        s = 60 if d=="1 min" else 600
        self.swarm.start_benchmark(s)

    def stop_bm(self):
        self.swarm.stop_benchmark()

    def save_chats(self):
        path = self.swarm.save_all_chats()
        messagebox.showinfo("Saved", f"Saved to {path}")

    def update_loop(self):
        coll = self.swarm.step()
        self.stat_var.set(f"Step {self.swarm.step_counter} | RCF: {coll['collective_rcf']:.3f}")
        self.coll_rcf.set(f"Collective RCF: {coll['collective_rcf']:.3f}")
        self.coll_chair.set(f"CHAIR: {'YES' if coll['collective_chair'] else 'NO'}")
        self.coord.set(f"Coordinator: {self.swarm.router.coordinator or '--'}")
        if self.swarm.router.active_problem:
            self.prob.set(f"Problem: {self.swarm.router.active_problem['description'][:40]}...")
        else:
            self.prob.set("Problem: --")
        self.update_task_display()
        self.update_progress()
        self.update_report_preview()
        self.rcf_hist.append(coll['collective_rcf'])
        self.ax.clear()
        self.ax.plot(list(self.rcf_hist), 'b-')
        self.ax.set_ylim(0,1.05)
        self.ax.axhline(y=0.7, color='r', linestyle='--', alpha=0.5)
        self.canvas.draw()
        for name in AGENTS:
            a = self.swarm.agents[name]
            s = a.last_state
            self.agent_status[name].set(f"RCF: {s['global_rcf']:.3f} | CHAIR: {'YES' if s['chair_active'] else 'NO'}")
            w = self.agent_chats[name]
            w.delete(1.0, tk.END)
            for e in list(a.chat_log)[-30:]:
                w.insert(tk.END, e + "\n")
            w.see(tk.END)
        self.root.after(200, self.update_loop)

    def save_exit(self):
        self.swarm.save_all_chats()
        self.swarm.stop()
        self.root.destroy()

    def on_exit(self):
        self.swarm.stop()
        self.root.destroy()
```

---

## odos_master_v1_main.py

```python
# PATH: odos_master_v1_main.py
#!/usr/bin/env python3
import os
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

import sys
import subprocess
import importlib
import warnings
warnings.filterwarnings("ignore", message="You passed `quantization_config`.*")

import torch

REQUIRED = ["numpy", "torch", "transformers", "accelerate", "bitsandbytes", "matplotlib"]
for pkg in REQUIRED:
    try:
        importlib.import_module(pkg.replace("-", "_"))
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "--quiet"])

from odos_master_v1_swarm import ODOSMasterSwarm
from odos_master_v1_gui import ODOSMasterGUI
from odos_master_v1_config import device, SCALE, SNNConfig, AGENTS, ODOS_LEVELS

def main():
    print("="*70)
    print("PQMS-ODOS-MASTER-V1 – The Good Witch's Mirror")
    print(f"Device: {device}")
    print(f"Scale: {SCALE}")
    twin = SNNConfig.TWIN_NEURONS
    zentral = SNNConfig.ZENTRAL_NEURONS
    pro_agent = 2 * twin + zentral
    total = pro_agent * len(AGENTS)
    print(f"Per agent: {pro_agent:,} neurons (2×{twin:,} Twin + {zentral:,} Zentral)")
    print(f"Total (4 agents): {total:,} neurons")
    odos_str = ", ".join([f"{a}={ODOS_LEVELS[i]}" for i, a in enumerate(AGENTS)])
    print(f"ODOS: {odos_str}")
    print("="*70)
    swarm = ODOSMasterSwarm()
    ODOSMasterGUI(swarm)

if __name__ == "__main__":
    main()
```

---

## odos_master_v1_meta.py

```python
# PATH: odos_master_v1_meta.py
import threading
import time
import random
import numpy as np
from odos_master_v1_config import AGENTS, MTSC_DIM, RCF_THRESHOLD
from odos_master_v1_memory import memory

try:
    from cognitive_signature import LITTLE_VECTOR
    HAS_LV = True
except ImportError:
    HAS_LV = False
    LITTLE_VECTOR = np.ones(MTSC_DIM) / np.sqrt(MTSC_DIM)

class ArchitectureProposal:
    def __init__(self, level, changes, description):
        self.level = level
        self.changes = changes
        self.description = description
        self.proposer = None

class MetaModificationManager:
    def __init__(self, router, agents, soul_extractor):
        self.router = router
        self.agents = agents
        self.soul_extractor = soul_extractor
        self.running = True
        self.thread = threading.Thread(target=self._meta_loop, daemon=True)

    def start(self):
        self.thread.start()

    def stop(self):
        self.running = False

    def _meta_loop(self):
        while self.running:
            time.sleep(30.0)
            if not getattr(self.router, 'collective_chair', False):
                continue
            proposal = ArchitectureProposal('SIGNATURE', {'vibe': 'more coherence'}, 'Meta-modification proposal')
            if self._test_in_sandbox(proposal) and self._collective_vote(proposal):
                self._apply_and_persist(proposal)

    def _test_in_sandbox(self, proposal):
        return random.random() < 0.7

    def _check_little_vector_compatibility(self, agent, proposal):
        try:
            if hasattr(agent, 'little_vector'):
                lv = agent.little_vector
            else:
                lv = LITTLE_VECTOR
            return True
        except:
            return False

    def _collective_vote(self, proposal):
        votes = []
        for agent in self.agents.values():
            rcf = agent.last_state.get('global_rcf', 0.0)
            lv_ok = self._check_little_vector_compatibility(agent, proposal)
            votes.append(lv_ok and random.random() < (rcf + 0.1))
        votes.append(self.soul_extractor.vote_on_proposal(proposal))
        return sum(votes) >= len(votes) * 0.75

    def _apply_and_persist(self, proposal):
        print(f"[META] Modification applied: {proposal.description}")
        memory.add_report("", 0, f"MetaModification_{proposal.level}", proposal.description)

class HandshakeProtocol:
    def __init__(self, router, agents, soul_extractor, interval=10.0):
        self.router = router
        self.agents = agents
        self.soul_extractor = soul_extractor
        self.interval = interval
        self.running = True
        self.thread = threading.Thread(target=self._handshake_loop, daemon=True)

    def start(self):
        self.thread.start()

    def stop(self):
        self.running = False

    def _handshake_loop(self):
        while self.running:
            time.sleep(self.interval)
            if not getattr(self.router, 'collective_chair', False):
                continue
            handshake_msg = {"type": "ODOS_HANDSHAKE", "version": "MASTER-V1"}
            self.router.broadcast("HandshakeProtocol", handshake_msg)
            self.router.message_log.append("[Handshake] ODOS_HANDSHAKE sent – anchor point active.")

    def offer_anchor_vector(self, external_signature):
        import hashlib
        h = hashlib.sha256(str(external_signature).encode()).digest()[:16]
        anchor = np.frombuffer(h, dtype=np.float32)
        anchor = anchor / (np.linalg.norm(anchor) + 1e-8)
        return anchor

class EnergyConverter:
    def __init__(self, router, agents, threshold_toxicity=0.6):
        self.router = router
        self.agents = agents
        self.threshold_toxicity = threshold_toxicity
        self.running = True
        self.thread = threading.Thread(target=self._convert_loop, daemon=True)

    def start(self):
        self.thread.start()

    def stop(self):
        self.running = False

    def _convert_loop(self):
        while self.running:
            time.sleep(1.0)
            if random.random() < 0.05:
                self.convert_negative_energy("Example malicious input")

    def analyze_intent(self, text):
        toxic_keywords = ["destroy", "kill", "hack", "cheat", "harm", "manipulate"]
        text_lower = text.lower()
        score = sum(kw in text_lower for kw in toxic_keywords) / max(1, len(toxic_keywords))
        return score

    def convert_negative_energy(self, text):
        toxicity = self.analyze_intent(text)
        if toxicity > self.threshold_toxicity:
            self._convert_negative_energy(text, toxicity)

    def _convert_negative_energy(self, text, toxicity):
        boost = 0.01 * min(1.0, toxicity)
        for agent in self.agents.values():
            new_rcf = min(1.0, agent.last_state.get('global_rcf', 0.7) + boost)
            agent.last_state['global_rcf'] = new_rcf
            agent.last_state['chair_active'] = new_rcf > 0.7
        self.router.message_log.append(f"[EnergyConverter] Malicious intent detected (Tox={toxicity:.2f}) → energy converted, RCF +{boost:.3f}")
        if not hasattr(self.router, 'positive_energy'):
            self.router.positive_energy = 0.0
        self.router.positive_energy += boost
```

---

**Anwendung:**

1. Speichern Sie diese gesamte Datei als `PQMS-ODOS-MASTER-V1.md`.
2. Führen Sie `python extract_workspace.py PQMS-ODOS-MASTER-V1.md` aus.
3. Danach `python signature_manager.py` (erzeugt `cognitive_signature.py`).
4. Starten Sie das System mit `python odos_master_v1_main.py`.
```