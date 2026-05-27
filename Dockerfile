# ── MedSight AI Backend — HuggingFace Spaces (Docker SDK) ──
# Runtime: Python 3.11 + PyTorch CPU
# RAM: ~2GB at rest, 4GB peak during inference

FROM python:3.11-slim

# HuggingFace Spaces requires port 7860
ENV PORT=7860
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libmagic1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install PyTorch CPU (much smaller than CUDA)
RUN pip install --no-cache-dir \
    torch==2.2.0+cpu \
    torchvision==0.17.0+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# Copy and install requirements (without CUDA torch lines)
COPY backend/requirements-prod.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY results/outputs/README.md ./results/outputs/

# Create necessary directories
RUN mkdir -p data/uploads data/chromadb data/raw data/processed \
    models/cache backend/temp backend/logs results/outputs

# HuggingFace Spaces runs as user 1000
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 7860

# Start with uvicorn
CMD ["python", "-m", "uvicorn", "backend.main:app", \
     "--host", "0.0.0.0", "--port", "7860", \
     "--workers", "1", "--timeout-keep-alive", "120"]
