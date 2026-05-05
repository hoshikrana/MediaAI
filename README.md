# MedSight AI 🧠

![Python 3.10.13](https://img.shields.io/badge/python-3.10.13-blue.svg)
![PyTorch 2.2](https://img.shields.io/badge/PyTorch-2.2-EE4C2C.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688.svg)
![Next.js 14](https://img.shields.io/badge/Next.js-14-black.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

MedSight AI is a multimodal medical diagnostic platform powered by deep learning. It fuses vision (chest X-ray analysis via DINOv2) and NLP (clinical note extraction via BioBERT) to deliver zero-shot disease classification and RAG-augmented medical reports.

## Features
- **Vision Module:** Anomaly detection & Grad-CAM visualizer using frozen DINOv2.
- **NLP Module:** Medical NER and zero-shot disease classification.
- **Multimodal Fusion:** Image-text alignment via BiomedVLP.
- **RAG Chatbot:** BioGPT streaming assistant grounded in PubMed abstracts.

## Tech Stack
- **Backend:** FastAPI, SQLAlchemy 2.0 (async), Pydantic v2
- **Frontend:** Next.js 14 (App Router), TailwindCSS
- **ML/Data:** PyTorch 2.2, HuggingFace Transformers, ChromaDB, SQLite/PostgreSQL

## Quick Start
```bash
conda activate medsight
pip install -r backend/requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn backend.main:app --reload --port 8000
```

## API Docs & Deployment
API Documentation available locally at `/docs` via Swagger UI.
Deploys automatically to Render.com (Backend) and Vercel (Frontend).
