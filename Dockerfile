
# Stage 1: Build React frontend
FROM node:22-bookworm-slim AS frontend

WORKDIR /frontend

COPY frontend/react/package*.json ./
RUN npm ci

COPY frontend/react/ ./

ENV VITE_API_BASE_URL=""

RUN npm run build


# Stage 2: Python backend and DistilBERT
FROM python:3.14-slim-bookworm

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    CLASSIFIER_MODEL_DIR=/app/models/claims-document-classifier-v4

# Libraries required by native Python dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      ca-certificates \
      libgomp1 \
      libglib2.0-0 \
      libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Install CPU-only PyTorch
RUN python -m pip install --no-cache-dir \
    --index-url https://download.pytorch.org/whl/cpu \
    "torch==2.15.0+cpu"

# Install backend runtime dependencies
COPY requirements.deploy.txt ./

RUN python -m pip install --no-cache-dir \
    -r requirements.deploy.txt

# Copy backend
COPY backend/ ./backend/

# Copy trained classifier and tokenizer
COPY models/claims-document-classifier-v4/ \
    ./models/claims-document-classifier-v4/

# Copy built React frontend
COPY --from=frontend /frontend/dist/ \
    ./frontend/react/dist/

# Temporary processing directory
RUN mkdir -p /app/data/uploads

EXPOSE 8000

CMD ["python", "-m", "uvicorn", \
     "backend.app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1"]
