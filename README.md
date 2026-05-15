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

# MedSight AI — Backend API

Multimodal Medical Diagnostic Platform powered by deep learning.

**Architecture:** VGG16 → VAE → ViT anomaly scorer (2.53M params)

## API Endpoints

- `POST /api/v1/analyze` — Upload X-ray for analysis
- `POST /api/v1/chat` — AI-powered clinical Q&A
- `GET /api/v1/health` — Health check
- `GET /docs` — Interactive API docs
