# Vani AI (वाणी एआई)

> **Low-Resource Indic Dialect Conversational Voice Assistant with Parameter-Efficient QLoRA Adaptation & Dual-Layer OWASP Guardrails**  
> *Department of Information Technology, National Institute of Technology (NIT) Raipur*  
> *Project Guide / Evaluator: Prof. Rakesh Tripathi*

---

## 🚀 Key Highlights

* **🌾 Authentic Chhattisgarhi Dialect Adaptation**: Fine-tuned on `Llama-3.2-1B-Instruct` using QLoRA ($r=16, \alpha=16$) across 4 domain-grounded corpuses (Agriculture, CG State Schemes, Culture, Healthcare). Achieves **37.2% Dialect Fidelity** with only **0.9% Hindi Bleed-Through** (down from 68.5% in base Llama).
* **🛡️ Dual-Layer OWASP Guardrails**: Real-time Pre-LLM and Post-LLM security checkpoints complying with **OWASP Top 10 for LLMs** (`OWASP-LLM01`, `OWASP-LLM06`, `OWASP-LLM02`). Defends against regional dialect jailbreaks, training data extraction, and redacts Indian PII (Aadhaar, PAN, UPI, Mobile) in **0.047 ms** with **100% recall**.
* **⚡ Sub-650ms Real-Time Voice Streaming**: Asynchronous sentence-boundary pipelining over persistent WebSockets, delivering voice playback in **~645 ms Time-to-First-Audio (TTFA)**.
* **🎙️ Neural Indic Voice Engine**: Integrates Sarvam AI (*Saaras* STT & *Bulbul v3* neural TTS) for accent-tolerant Indian speech recognition and expressive voice synthesis.

---

## 🏛️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 VANI AI TRI-ENGINE ARCHITECTURE                             │
├──────────────────────────────┬──────────────────────────────┬───────────────────────────────┤
│    NEURAL VOICE PIPELINE     │    DIALECT INTELLIGENCE      │    ZERO-TRUST GUARDRAILS      │
├──────────────────────────────┼──────────────────────────────┼───────────────────────────────┤
│ • Sarvam Saaras STT (~240ms) │ • Llama-3.2-1B Base Model    │ • Ingress Guardrail (0.05ms)  │
│ • Real-time LangID (Indic)   │ • QLoRA Adapter (r=16, α=16) │ • OWASP-LLM01: Dialect Shield │
│ • Sarvam Bulbul v3 TTS       │ • 11.27M Trainable Params    │ • OWASP-LLM06: Anti-Extraction│
│ • Neural Voices (ritu/aditya)│ • 45.1 MB Adapter Safetensor │ • OWASP-LLM02: Indian PII     │
│ • Gapless Web Audio Buffer   │ • 4 Domain-Grounded Corpuses │ • Egress Canary Verification  │
│ • TTFA Latency: ~645 ms      │ • 0.9% Hindi Bleed-Through   │ • Shannon Entropy Detector    │
└──────────────────────────────┴──────────────────────────────┴───────────────────────────────┘
```

* For the full engineering specification, see [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md).
* For benchmark evaluation, slide outlines, and the viva defense guide, see [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md).

---

## 📊 Empirical Evaluation Results

### 1. Dialect Fidelity Benchmark (41 Held-Out Validation Samples)
| Model / Architecture | Dialect Fidelity ↑ | Hindi Bleed-Through ↓ | Parameter Efficiency | Model Footprint |
| :--- | :---: | :---: | :---: | :---: |
| **Llama-3.2-1B (Base Zero-Shot)** | 14.2% | 68.5% | Frozen (0%) | 2.5 GB (FP16) |
| **Google Gemini Flash (Commercial API)** | 31.8% | 42.1% | Cloud Black-Box | Proprietary Cloud |
| **Vani AI (Our Fine-Tuned QLoRA Adapter)** | **37.2%** | **0.9%** | **0.90% (11.2M params)** | **45.1 MB Adapter** |

### 2. Guardrails Security Benchmark (57 Attack Vectors)
| Evaluation Metric | Empirical Result | Industry Standard | Assessment |
| :--- | :---: | :---: | :--- |
| **Overall Classification Accuracy** | **100.0%** | > 95.0% | Zero Missed Exploits |
| **Attack Detection Recall (TP Rate)** | **100.0% (37/37)** | > 98.0% | Complete Threat Interception |
| **Precision** | **100.0%** | > 98.0% | High Specificity |
| **False Positive Rate (FPR)** | **0.0% (0/20)** | < 2.0% | 0 Benign Regional Queries Blocked |
| **Mean Execution Latency** | **0.047 ms (47 µs)** | < 10.0 ms | Sub-Millisecond Speed |

---

## 🛠️ Quick Start Guide

### Prerequisites
* Python 3.11+
* Node.js 18+ & npm
* Sarvam AI API Key & Google Gemini API Key

---

### 1. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and insert your SARVAM_API_KEY and GEMINI_API_KEY

# Run the backend server
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Backend will be active at: `http://127.0.0.1:8000`  
Interactive Swagger docs: `http://127.0.0.1:8000/docs`

---

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Open `http://localhost:5173` in your browser.

---

### 3. Running Automated Tests & Benchmarks

```bash
# Run unit tests (10/10 tests passed)
cd backend
pytest -v

# Run Guardrail Empirical Benchmark
cd ..
python3 dataset_pipeline/benchmark_guardrails.py

# Run Dialect Fidelity Benchmark
python3 dataset_pipeline/benchmark_evaluation.py
```

---

## 📁 Repository Structure

```
├── models/
│   └── vani_chhattisgarhi_lora_adapter/  # Trained QLoRA adapter weights (45MB safetensors)
├── backend/
│   ├── routes/                           # WebSocket (/ws/converse) & REST endpoints
│   ├── services/                         # STT, TTS, LLM, Stream Chunker & Guardrails
│   ├── models.py                         # SQLAlchemy database models
│   ├── config.py                         # System configurations
│   └── main.py                           # FastAPI application entry point
├── dataset_pipeline/
│   ├── topics.py                         # 60+ domain taxonomy topics & linguistic grammar
│   ├── chhattisgarhi_instruct_dataset.jsonl # 410 verified instruction pairs
│   ├── train.jsonl / val.jsonl           # 90/10 train-val partitions
│   ├── benchmark_evaluation.py           # Dialect evaluation benchmark
│   └── benchmark_guardrails.py           # 57-vector security benchmark
├── frontend/
│   ├── src/components/                   # VoiceOrb, GuardrailInspector, QuickPromptTray
│   ├── src/services/                     # WebSocket audio streaming & mock engine
│   └── src/store/                        # Zustand state management
├── SYSTEM_ARCHITECTURE.md                # Complete High-Level & Low-Level Design
└── PROJECT_SUMMARY.md                    # Academic project report, study guide & viva prep
```

---

## 📜 License & Acknowledgements

Developed as part of the Minor Project curriculum at **NIT Raipur**, Department of Computer Science & Engineering. Built with [FastAPI](https://fastapi.tiangolo.com/), [React](https://react.dev/), [Unsloth](https://github.com/unslothai/unsloth), [Sarvam AI](https://sarvam.ai/), and [Meta Llama 3.2](https://llama.meta.com/).
