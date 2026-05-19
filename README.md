---
title: MedSight AI Backend
emoji: 🏥
colorFrom: blue
colorTo: blue
sdk: docker
app_port: 7860
pinned: true
license: apache-2.0
---

<div align="center">

# 🏥 MedSight AI

### Multimodal Medical Diagnostic Platform

**AI-Powered Pulmonary Anomaly Detection Fusing Computer Vision, NLP, and Retrieval-Augmented Generation**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PyTorch 2.2](https://img.shields.io/badge/PyTorch-2.2-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue?style=for-the-badge)](LICENSE)

[Live Demo](#deployment) · [Research Paper](#research-paper) · [API Docs](#api-reference) · [Architecture](#system-architecture)

</div>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
  - [7-Stage Analysis Pipeline](#7-stage-analysis-pipeline)
  - [VRAM-Aware Model Registry](#vram-aware-model-registry)
  - [NLP Pipeline](#nlp-pipeline)
  - [3-Tier RAG Conversational Architecture](#3-tier-rag-conversational-architecture)
- [Model Pipeline — VGG16 → VAE → ViT](#model-pipeline--vgg16--vae--vit)
  - [Fused Anomaly Score](#fused-anomaly-score)
  - [Interpretability — Clinical Attention Heatmaps](#interpretability--clinical-attention-heatmaps)
- [Training & Experimental Results](#training--experimental-results)
  - [Ablation Study](#ablation-study--fusion-component-analysis)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Deployment](#deployment)
- [Research Paper](#research-paper)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

**MedSight AI** is a full-stack multimodal medical diagnostic platform that performs automated pulmonary anomaly detection from chest X-ray images. The system fuses deep learning–based computer vision with clinical NLP and a retrieval-augmented generation (RAG) pipeline to deliver comprehensive diagnostic reports, clinical Q&A, and explainable AI visualizations — all through a modern clinical dashboard.

The platform is designed as a **clinical decision-support tool** (not a replacement for physicians) that assists radiologists and clinicians by:

- Detecting pulmonary anomalies in chest X-rays using a novel **VGG16 → VAE → ViT** architecture (2.53M trainable parameters)
- Extracting clinical entities from patient symptom descriptions via **scispaCy NER** and **zero-shot disease classification**
- Generating patient-friendly diagnostic explanations through **Gemini 2.0 Flash**–powered conversational AI
- Producing downloadable **PDF diagnostic reports** with heatmap visualizations

> ⚠️ **Disclaimer:** MedSight AI is a research prototype for educational and clinical decision-support purposes. It is **not** FDA-approved and should not be used as the sole basis for medical diagnosis or treatment.

---

## Key Features

| Feature | Description |
|---|---|
| 🔬 **Anomaly Detection** | Novel VGG16 → VAE → ViT pipeline that detects anomalies via reconstruction error, KL divergence, and attention-based scoring |
| 🗺️ **Heatmap Visualization** | Clinical Grad-CAM–style attention overlays showing regions of interest on X-rays |
| 🧠 **NLP Entity Extraction** | scispaCy-powered medical NER extracting diseases, symptoms, medications, and anatomical entities |
| 🏷️ **Disease Classification** | Zero-shot classification using DistilBART-MNLI with rule-based fallbacks |
| 🔗 **Multimodal Fusion** | Image-text alignment scoring to correlate imaging findings with clinical narratives |
| 💬 **AI Clinical Chat** | Gemini 2.0 Flash–powered RAG chatbot with session-aware context and intent detection |
| 📄 **PDF Reports** | Auto-generated diagnostic reports with heatmaps, findings, and recommendations |
| 🎙️ **Voice Input** | Whisper-powered speech-to-text for hands-free symptom entry |
| 🔐 **Authentication** | JWT + Google OAuth 2.0 with secure session management and brute-force protection |
| 📊 **Patient Dashboard** | Comprehensive analysis history, risk tracking, and session management |

---

## System Architecture

<p align="center">
  <img src="docs/images/system_architecture.png" alt="MedSight AI System Architecture" width="800"/>
</p>

MedSight AI is deployed as a **production-grade web application** with a React/Next.js 14 frontend and an async FastAPI backend. The architecture cleanly separates vision, NLP, and conversational AI pipelines behind a unified REST API.

### 7-Stage Analysis Pipeline

Every X-ray analysis request flows through a deterministic 7-stage orchestration pipeline (`backend/orchestration/pipeline.py`):

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ 1. Input │──▶│ 2. Vision│──▶│ 3. VRAM  │──▶│ 4. NLP   │──▶│ 5. Multi │──▶│ 6. Report│──▶│ 7. Status│
│ Validate │   │ Analysis │   │ Cleanup  │   │ Analysis │   │  Fusion  │   │   Gen    │   │  Return  │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
  Preprocess     VGG16→VAE     torch.cuda     scispaCy NER   BiomedVLP      BioGPT or      COMPLETE /
  224×224 RGB    →ViT scorer   empty_cache    + DistilBART    alignment      Template       PARTIAL /
  LANCZOS        + heatmap     (GPU only)     zero-shot       scoring        fallback       FAILED
```

Each stage runs asynchronously with **independent error handling** — if vision fails, NLP still runs. The system returns `COMPLETE`, `PARTIAL`, or `FAILED` depending on which stages succeeded.

### VRAM-Aware Model Registry

A custom `ModelRegistry` manages six ML models with **priority-based loading**, **LRU GPU eviction**, and **async initialization**. This enables deployment on consumer hardware with as little as **4 GB VRAM**:

| Priority | Model | HuggingFace ID | RAM | Required | Purpose |
|:---:|---|---|:---:|:---:|---|
| 1 | VGG16+VAE+ViT | `hoshikrana/VAE_and_VIT_Anomaly_detection` | 50 MB | ✅ | Anomaly detection |
| 1 | MiniLM-L6-v2 | `sentence-transformers/all-MiniLM-L6-v2` | 100 MB | ✅ | RAG embeddings |
| 2 | scispaCy NER | `en_core_sci_sm` | 100 MB | ✅ | Medical entity extraction |
| 3 | Whisper Tiny | `openai/whisper-tiny` | 300 MB | ❌ | Voice transcription |
| 4 | BioGPT | `microsoft/biogpt` | 700 MB | ❌ | Report generation |
| 5 | DistilBART | `valhalla/distilbart-mnli-12-1` | 300 MB | ❌ | Zero-shot classification |

The registry supports **dynamic GPU↔CPU migration** — when a higher-priority model needs GPU memory, the least-recently-used GPU model is evicted to CPU automatically.

### NLP Pipeline

The NLP module processes clinical notes through three stages:

1. **Named Entity Recognition** — scispaCy (`en_core_sci_sm`) extracts diseases, symptoms, medications, and anatomical references from patient text
2. **Zero-Shot Classification** — DistilBART-MNLI classifies clinical text against 20 pulmonary conditions without task-specific fine-tuning (falls back to rule-based matching if the model isn't loaded)
3. **Multimodal Fusion** — Optional BiomedVLP image-text alignment scoring correlates imaging findings with clinical narratives, with a keyword-based fallback for constrained environments

### 3-Tier RAG Conversational Architecture

The conversational module implements a **highly resilient 3-tier Retrieval-Augmented Generation** system that never fails silently:

| Tier | Engine | Method | Latency |
|:---:|---|---|:---:|
| **Tier 1** | Gemini 2.0 Flash (Cloud) | Streaming SSE with dynamic system instructions | ~1.5s |
| **Tier 2** | BioGPT (Local) | Beam search decoding (num_beams=4) | ~3s |
| **Tier 3** | Heuristic Templates | Intent-detection rule engine with 8 intent categories | ~5ms |

**Context construction** aggregates: vision anomaly scores → NLP predictions → fusion similarity → patient session history → retrieved PubMed abstracts (via MiniLM-L6-v2 + ChromaDB HNSW indexing). All tiers prohibit dosage recommendations and append medical disclaimers.

---

## Model Pipeline — VGG16 → VAE → ViT

<p align="center">
  <img src="docs/images/model_architecture.png" alt="Three-Stage Anomaly Detection Architecture" width="800"/>
</p>

The core anomaly detection system implements a novel **three-stage unsupervised architecture** with only **2.53M trainable parameters**. The model is trained exclusively on normal chest X-rays and detects anomalies by learning the distribution of healthy pulmonary anatomy — requiring **zero pathology-specific labels**.

### Stage 1 — VGG16 Feature Extraction (0 trainable params)

Pre-trained VGG16 (ImageNet) serves as a **frozen feature extractor**. Convolutional feature maps are globally average-pooled to produce a compact representation per image.

```
Input: 224×224×3 RGB (ImageNet-normalized)
  → VGG16.features (frozen)
  → AdaptiveAvgPool2d(1,1)
  → Flatten
  → Output: ℝ⁵¹² feature vector
```

**Why freeze?** (i) Deterministic features ensure stable VAE training; (ii) zero gradient storage saves VRAM; (iii) ImageNet features transfer well to medical imaging (Raghu et al., 2019).

### Stage 2 — Variational Autoencoder (1,318,656 params)

The VAE learns a **smooth, continuous latent manifold** of normal pulmonary anatomy. During inference, pathological images produce higher reconstruction error and KL divergence because they fall outside the learned normal distribution.

```
Encoder: 512 → 512 → 384 → 256 → [μ, log σ²]  (each with LayerNorm + GELU + Dropout 0.1)
         ↓
     Reparameterization: z = μ + ε·σ    (ε ~ N(0,1))
         ↓
Decoder: 256 → 384 → 512 → 512          (symmetric architecture)
         ↓
     Output: x̂ (reconstructed features)
```

**Loss function** — Evidence Lower Bound (ELBO):

```
L_VAE = L_recon + β · L_KL

where:  L_recon = MSE(x̂, x)
        L_KL   = -½ Σ(1 + log σ² - μ² - σ²)
        β      = 0.001  (β-VAE formulation to prevent posterior collapse)
```

### Stage 3 — Vision Transformer Anomaly Scorer (1,209,729 params)

The ViT operates on the **latent vector z** (not raw pixels), treating it as a sequence of patches for self-attention-based anomaly scoring. This is a key architectural decision — the ViT scores the quality of the latent representation rather than the image directly.

```
z ∈ ℝ²⁵⁶ → reshape to 8 patches of dim 32
  → Linear projection to d_model = 128
  → Prepend learnable [CLS] token
  → Add positional embeddings (9 tokens = 8 patches + CLS)
  → 6× Transformer Blocks (8-head attention, MLP dim 512, GELU, Dropout 0.1)
  → LayerNorm
  → [CLS] token → MLP head → Sigmoid → anomaly score ∈ [0, 1]
```

| Hyperparameter | Value |
|---|:---:|
| Latent dimension | 256 |
| Patch dimension | 32 |
| Number of patches | 8 |
| Model dimension (d_model) | 128 |
| Transformer depth | 6 layers |
| Attention heads | 8 |
| MLP dimension | 512 |
| Dropout | 0.1 |
| Output activation | Sigmoid → [0, 1] |

### Fused Anomaly Score

The final anomaly score fuses **three complementary signals** via weighted linear combination after normalizing each component using calibration statistics computed on the training set:

```
S_anomaly = w₁ · σ((e_recon - μ_recon) / σ_recon)
          + w₂ · σ((d_KL - μ_KL) / σ_KL)
          + w₃ · s_ViT

where:  w₁ = 0.4  (reconstruction error — pixel-level deviations)
        w₂ = 0.2  (KL divergence — distributional shift)
        w₃ = 0.4  (ViT score — higher-order latent abnormalities)
        σ  = sigmoid normalization
```

The optimal threshold of **0.348** was determined by maximizing the Youden index on the validation set.

### Interpretability — Clinical Attention Heatmaps

To provide **visual explainability**, the system extracts [CLS] token attention weights from the final ViT layer:

1. Average attention across all 8 heads → patch-level attention vector
2. Reshape into 2D grid and upsample to 384×384 via bicubic interpolation
3. Apply clinical colormap (black → dark red → orange → bright yellow)
4. Adaptive transparency mask ensures only anomalous regions glow over the X-ray
5. CLAHE enhancement on base radiograph maximizes anatomical contrast

The result is a three-panel visualization: **Original X-ray** | **Attention Heatmap** | **Clinical Overlay** with anomaly score.

---

## Training & Experimental Results

### Dataset — COVID-19 Radiography Database

| Class | Count | Usage |
|---|:---:|---|
| Normal | 10,192 | Training (unsupervised — model only sees this) |
| COVID-19 | 3,616 | Evaluation only |
| Lung Opacity | 6,012 | Evaluation only |
| Viral Pneumonia | 1,345 | Evaluation only |
| **Total** | **21,165** | — |

**Preprocessing:** 224×224 Lanczos resize, RGB, ImageNet normalization. Training augmentations: random horizontal flip (p=0.5), rotation (±10°), color jitter (±0.2).

### Two-Phase Training Protocol

**Phase 1 — VAE Training (50 epochs)**
- AdamW optimizer (lr=1×10⁻⁴, weight_decay=1×10⁻⁵)
- ReduceLROnPlateau scheduler (factor=0.5, patience=3)
- Batch size 32, β=0.001, early stopping patience 10
- Resource-efficient: mixed-precision FP16, gradient accumulation (4 steps → effective batch 128)

**Phase 2 — ViT Scorer Training (30 epochs)**
- AdamW optimizer (lr=5×10⁻⁵, weight_decay=1×10⁻⁵)
- Binary cross-entropy: Normal→0, Anomaly→1
- Only the ViT uses labels; the VAE remains **fully unsupervised**

### Results

| Metric | Value |
|---|:---:|
| **AUROC** | **0.718** |
| ViT Validation Accuracy | 98.6% |
| VAE Final Reconstruction MSE | 0.0152 |
| VAE β·KL Divergence | 6.97×10⁻⁴ |
| True Positives (Anomaly→Anomaly) | 4,974 |
| True Negatives (Normal→Normal) | 1,017 |
| Sensitivity (Recall) | 64.7% |
| Specificity | 66.5% |
| Optimal Threshold | 0.348 |
| Total Trainable Parameters | **2,528,385** |

### Ablation Study — Fusion Component Analysis

| Configuration | AUROC | Notes |
|---|:---:|---|
| Reconstruction error only | 0.62 | MSE between VGG features and reconstruction |
| KL divergence only | 0.68 | Strongest single signal |
| ViT score only | 0.65 | Latent-space attention scoring |
| Recon. + KL (w/o ViT) | 0.69 | Traditional VAE anomaly detection |
| **Full fusion (0.4 / 0.2 / 0.4)** | **0.718** | **Best configuration** |

Each component provides **complementary information** — reconstruction error captures pixel-level deviations, KL divergence captures distributional shift, and the ViT captures higher-order latent abnormalities via attention.

### Latent Space Validation (UMAP)

UMAP projection of the 256-dimensional VAE latent space reveals **emergent clustering without supervision**:
- **Normal** images cluster tightly — the VAE learned a compact representation of healthy anatomy
- **Lung Opacity** forms a distinct separable cluster — the most detectable anomaly class
- **Viral Pneumonia** partially overlaps with normal — explaining its harder detectability
- **COVID-19** cases are sparse and widely distributed — reflecting heterogeneous radiographic presentations

---

## Tech Stack

### Backend
| Component | Technology |
|---|---|
| Framework | FastAPI 0.110 (async, Pydantic v2) |
| ML Runtime | PyTorch 2.2 + ONNX Runtime |
| NLP | scispaCy, HuggingFace Transformers, BioGPT |
| Embeddings | Sentence-Transformers (MiniLM-L6-v2) |
| Vector DB | ChromaDB 0.4.24 |
| Generative AI | Google Gemini 2.0 Flash |
| Database | SQLAlchemy 2.0 (SQLite dev / PostgreSQL prod) |
| Auth | JWT + Google OAuth 2.0 (Authlib) |
| Task Scheduling | APScheduler |
| PDF Generation | ReportLab |

### Frontend
| Component | Technology |
|---|---|
| Framework | Next.js 14 (App Router) |
| Styling | Tailwind CSS 3.4 |
| Animations | Framer Motion 11 |
| Charts | Recharts 2.12 |
| Icons | Lucide React |
| HTTP Client | Axios |
| Deployment | Vercel |

### Infrastructure
| Component | Technology |
|---|---|
| Containerization | Docker (Python 3.11-slim) |
| Backend Hosting | HuggingFace Spaces (Docker SDK) |
| Frontend Hosting | Vercel |
| Model Distribution | HuggingFace Hub |
| Object Storage | Cloudflare R2 (optional) |
| Database (Prod) | Supabase PostgreSQL |

---

## Project Structure

```
MedSightAI/
├── backend/
│   ├── api/v1/
│   │   ├── routers/          # FastAPI route handlers
│   │   │   ├── analyze.py    # X-ray upload & analysis
│   │   │   ├── auth.py       # JWT + OAuth authentication
│   │   │   ├── chat.py       # RAG-powered clinical Q&A
│   │   │   ├── report.py     # PDF report generation
│   │   │   └── users.py      # User profiles & session history
│   │   └── schemas/          # Pydantic v2 request/response models
│   ├── core/
│   │   ├── config.py         # Pydantic settings (env-driven)
│   │   ├── security.py       # JWT, password hashing, API keys
│   │   ├── middleware.py      # CORS, rate limiting, security headers
│   │   └── exceptions.py     # Custom exception hierarchy
│   ├── db/
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── migrations/       # Alembic migration scripts
│   │   └── session.py        # Async database session factory
│   ├── ml/
│   │   ├── vision/
│   │   │   ├── pulmonary_anomaly.py  # VGG16→VAE→ViT detector
│   │   │   ├── anomaly.py    # ONNX ConvAE fallback
│   │   │   └── hf_download.py # HuggingFace model auto-download
│   │   ├── nlp/
│   │   │   ├── ner.py        # scispaCy medical NER
│   │   │   ├── classifier.py # Zero-shot disease classification
│   │   │   └── whisper.py    # Voice-to-text transcription
│   │   ├── rag/
│   │   │   ├── gemini_client.py  # Gemini 2.0 Flash integration
│   │   │   ├── generator.py  # BioGPT report + chat generation
│   │   │   ├── retriever.py  # ChromaDB vector retrieval
│   │   │   └── vectorstore.py # Embedding + indexing pipeline
│   │   ├── fusion/
│   │   │   └── medclip.py    # Multimodal image-text alignment
│   │   └── registry.py       # Model lifecycle manager
│   ├── orchestration/
│   │   ├── pipeline.py       # 7-stage analysis orchestrator
│   │   ├── queue.py          # Async task queue
│   │   ├── resilience.py     # Retry, circuit-breaker, fallbacks
│   │   ├── scheduler.py      # Periodic cleanup tasks
│   │   └── workers.py        # Background worker pool
│   └── utils/
│       ├── pdf.py            # Clinical PDF report builder
│       ├── image.py          # Image preprocessing utilities
│       ├── audio.py          # Audio format handling
│       └── validators.py     # Input validation helpers
├── frontend/
│   ├── app/                  # Next.js App Router pages
│   │   ├── (auth)/           # Login / Registration pages
│   │   ├── (dashboard)/      # Analysis dashboard
│   │   ├── about/            # About page
│   │   └── profile/          # User profile & history
│   ├── components/
│   │   ├── analysis/         # Upload panel, results viewer
│   │   ├── chat/             # AI chat interface
│   │   ├── shared/           # Navbar, layout components
│   │   └── ui/               # Reusable UI primitives
│   └── lib/                  # API client, auth context, utilities
├── training/
│   ├── notebooks/            # Jupyter training notebooks
│   └── scripts/              # Data preparation & training scripts
├── data/                     # Raw/processed data & uploads
├── models/                   # Cached model weights
├── results/                  # Training outputs & evaluation
├── Dockerfile                # Production Docker image
├── requirements.txt          # Python dependencies
└── .env.example              # Environment variable template
```

---

## Getting Started

### Prerequisites

- **Python** 3.10 or higher
- **Node.js** 18+ and npm
- **Git** and **Git LFS** (for model weights)
- **(Optional)** CUDA 11.8+ compatible GPU for accelerated inference

### 1. Clone the Repository

```bash
git clone https://github.com/hoshikrana/MedSightAI.git
cd MedSightAI
```

### 2. Backend Setup

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install PyTorch (GPU — CUDA 11.8)
pip install torch==2.2.0+cu118 torchvision==0.17.0+cu118 --index-url https://download.pytorch.org/whl/cu118

# OR install PyTorch (CPU-only)
pip install torch==2.2.0+cpu torchvision==0.17.0+cpu --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies
pip install -r requirements.txt

# Install scispaCy model
pip install https://s3-us-west-2.amazonaws.com/ai2-s3-scispacy/releases/v0.5.1/en_core_sci_sm-0.5.1.tar.gz
```

### 3. Environment Configuration

```bash
# Copy the example environment file
cp .env.example .env

# Generate secure keys
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(32))"
```

Edit `.env` with your configuration. Required variables:
- `SECRET_KEY` — Application secret (min 32 chars)
- `JWT_SECRET_KEY` — JWT signing key (min 32 chars)
- `GEMINI_API_KEY` — [Get free API key](https://aistudio.google.com/app/apikey) for AI chat
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` — For OAuth (optional)

### 4. Frontend Setup

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=MedSight AI
```

### 5. Run the Application

```bash
# Terminal 1 — Backend (from project root)
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `ENVIRONMENT` | `development` | `development` / `production` / `test` |
| `SECRET_KEY` | *required* | Application secret key (≥32 chars) |
| `DATABASE_URL` | `sqlite+aiosqlite:///./medsight.db` | Database connection string |
| `GEMINI_API_KEY` | — | Google Gemini API key for AI chat |
| `HF_TOKEN` | — | HuggingFace token for model downloads |
| `VISION_ANOMALY_BACKEND` | `auto` | `auto` / `onnx` / `pulmonary` |
| `GPU_VRAM_BUDGET_MB` | `3500` | Max VRAM budget for model loading |
| `MAX_UPLOAD_SIZE_MB` | `10` | Maximum upload file size |
| `STORAGE_BACKEND` | `local` | `local` / `r2` (Cloudflare R2) |
| `RATE_LIMIT_ANALYZE` | `10/hour` | Analysis endpoint rate limit |
| `RATE_LIMIT_CHAT` | `50/hour` | Chat endpoint rate limit |

See [`.env.example`](.env.example) for the complete list of configurable options.

### Vision Backend Selection

The `VISION_ANOMALY_BACKEND` setting controls which vision model is used:

| Mode | Description |
|---|---|
| `auto` | Auto-detects available checkpoints (prefers `pulmonary` → `onnx`) |
| `pulmonary` | Uses the VGG16→VAE→ViT `.pth` checkpoint |
| `onnx` | Uses the ConvAE ONNX model for lightweight CPU inference |

---

## API Reference

### Core Endpoints

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/api/v1/analyze` | Upload X-ray image + symptoms for analysis | ✅ |
| `GET` | `/api/v1/analyze/status/{task_id}` | Poll analysis task status | ✅ |
| `GET` | `/api/v1/analyze/result/{session_id}` | Retrieve completed analysis results | ✅ |
| `POST` | `/api/v1/chat` | AI-powered clinical Q&A (streaming) | ✅ |
| `GET` | `/api/v1/report/{session_id}` | Generate & download PDF report | ✅ |
| `GET` | `/api/v1/health` | System health check | ❌ |
| `GET` | `/docs` | Interactive Swagger UI (dev only) | ❌ |

### Authentication Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Email/password registration |
| `POST` | `/api/v1/auth/login` | Email/password login → JWT tokens |
| `POST` | `/api/v1/auth/refresh` | Refresh access token |
| `GET` | `/api/v1/auth/google` | Initiate Google OAuth flow |
| `GET` | `/api/v1/auth/google/callback` | Google OAuth callback |

### Analysis Response Schema

```json
{
  "session_id": "uuid",
  "overall_status": "COMPLETE | PARTIAL | FAILED",
  "vision": {
    "anomaly_score": 72.5,
    "risk_level": "HIGH",
    "heatmap_base64": "data:image/png;base64,...",
    "top_regions": [{"x": 76, "y": 56, "width": 72, "height": 86, "confidence": 0.85}],
    "model_confidence": 0.82
  },
  "nlp": {
    "entities": {"diseases": [...], "symptoms": [...], "medications": [...]},
    "primary_diagnosis": "Pneumonia",
    "diagnosis_confidence": 0.78,
    "differential": [{"disease": "Pleural Effusion", "confidence": 0.45}]
  },
  "fusion": {
    "image_text_similarity": 0.72,
    "alignment": "moderate",
    "final_risk": "MEDIUM"
  },
  "report_text": "## AI Diagnostic Report ...",
  "timings": {
    "preprocess_ms": 45,
    "vision_ms": 1200,
    "nlp_ms": 350,
    "fusion_ms": 120,
    "report_ms": 800,
    "total_ms": 2515
  }
}
```

---

## Deployment

### Production Architecture

| Service | Platform | Purpose |
|---|---|---|
| **Backend API** | HuggingFace Spaces (Docker SDK) | FastAPI + ML inference on port 7860 |
| **Frontend** | Vercel | Next.js static + SSR |
| **Database** | Supabase | Managed PostgreSQL |
| **Models** | HuggingFace Hub | Model weight distribution |
| **Storage** | Cloudflare R2 | Medical image storage (optional) |

### Docker Deployment

```bash
# Build the production image
docker build -t medsight-ai .

# Run locally
docker run -p 7860:7860 --env-file .env medsight-ai
```

The Dockerfile uses `python:3.11-slim`, installs CPU-only PyTorch (~800MB smaller than CUDA), and runs Uvicorn with a single worker. Peak memory is approximately **4GB** during inference.

### HuggingFace Spaces

The backend is configured to deploy directly to HuggingFace Spaces via the Docker SDK. The HuggingFace metadata is in the `README.md` frontmatter. Models are auto-downloaded from `hoshikrana/VAE_and_VIT_Anomaly_detection` on startup.

---

## Research Paper

This project is accompanied by a peer-reviewed research paper:

> **"MedSight AI: A Multimodal Deep Learning Framework for Unsupervised Pulmonary Anomaly Detection with Retrieval-Augmented Clinical Decision Support"**
>
> Kasala Hoshik, V. Vineel Reddy, K. Chanikya
> Lovely Professional University, Phagwara, Punjab, India
> Research | May 2026

### Key Research Contributions

1. **Novel three-stage architecture (VGG16 → VAE → ViT)** — Decomposes anomaly detection into feature extraction, distributional learning, and attention-based scoring with only 2.53M trainable parameters (vs. 86M in ViT-Base or 307M in DINOv2)
2. **Unsupervised paradigm shift** — Trained exclusively on normal radiographs, eliminating the need for expensive per-pathology annotation. Can detect novel/rare pathologies absent from training data
3. **Multi-signal interpretable scoring** — Fusion of reconstruction error, KL divergence, and ViT attention provides clinicians with three complementary perspectives on why an image was flagged
4. **UMAP-validated latent representations** — Emergent clustering in the VAE latent space demonstrates pathology-relevant structure without any supervised signal
5. **Production-grade multimodal system** — Complete clinical platform integrating vision, NLP, and 3-tier RAG conversational AI with graceful degradation when individual components fail
6. **Resource-constrained deployment** — Full pipeline operates within 4 GB VRAM, enabling deployment on consumer hardware and CPU-only environments

### Strengths Highlighted in the Paper

- **Clinical viability** — AUROC of 0.718 demonstrates unsupervised detection can provide clinically useful screening as a triage tool
- **Extreme parameter efficiency** — 2.53M params vs. 86M (ViT-Base) or 307M (DINOv2)
- **Interpretable multi-signal scoring** — Three complementary anomaly signals provide richer diagnostic information than single-metric approaches

### Future Directions

- Perceptual loss (instead of MSE) for VAE reconstruction to better capture structural anomalies
- Larger backbones (DINOv2 ViT-S/14 producing 384-d features)
- Multi-scale latent analysis using hierarchical VAEs
- Contrastive pre-training of the anomaly scorer
- Domain-specific backbones (CheXNet) for improved viral pneumonia sensitivity

---

## Reproduce Training

See [Training & Experimental Results](#training--experimental-results) above for full methodology and hyperparameters.

```bash
# Prepare and preprocess the dataset
python training/scripts/prepare_dataset.py

# Train the VAE + ViT anomaly detector
python training/scripts/train_anomaly.py

# Or use the Jupyter notebook for interactive training
jupyter notebook training/notebooks/covid\ \(1\).ipynb

# Upload trained models to HuggingFace
python training/scripts/upload_models.py
```

---

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and ensure tests pass
4. Commit with descriptive messages (`git commit -m 'Add amazing feature'`)
5. Push to your branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

### Development Guidelines

- **Backend:** Follow `ruff` and `black` formatting (see `pyproject.toml`)
- **Frontend:** Follow ESLint + Prettier configuration
- **Tests:** Add tests for new features (`pytest` for backend, `npm test` for frontend)
- **Commits:** Use conventional commit messages

### Running Tests

```bash
# Backend tests
pytest backend/tests/ -v --tb=short

# With specific markers
pytest -m "unit" -v        # Fast unit tests only
pytest -m "integration" -v # Integration tests
pytest -m "ml" -v          # ML model tests

# Frontend lint
cd frontend && npm run lint
```

---

## Acknowledgements

- [COVID-19 Radiography Dataset](https://www.kaggle.com/datasets/tawsifurrahman/covid19-radiography-database) — Training data
- [scispaCy](https://allenai.github.io/scispacy/) — Biomedical NLP models
- [HuggingFace Transformers](https://huggingface.co/docs/transformers) — Model hub and inference
- [Google Gemini](https://ai.google.dev/) — Generative AI for clinical chat
- [FastAPI](https://fastapi.tiangolo.com/) — High-performance async API framework
- [Next.js](https://nextjs.org/) — React framework for the frontend

---

## License

This project is licensed under the **Apache License 2.0** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with ❤️ for advancing medical AI research**

*MedSight AI is a research project and should not be used for clinical diagnosis without physician oversight.*

</div>
