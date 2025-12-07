# Multi-stage build for Audio to MIDI Converter
FROM python:3.11-slim as backend

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Demucs models
RUN python -c "import demucs; from demucs import pretrained; pretrained.load_model('htdemucs_6s')"

# Install Basic Pitch models  
RUN python -c "import basic_pitch; basic_pitch.download_models()"

# Copy backend code
COPY backend/ ./backend/
COPY backend_test.py .

# Create necessary directories
RUN mkdir -p /app/uploads /app/processed

# Backend stage complete
# -------------------------------------------------

# Frontend stage
FROM node:18-alpine as frontend

WORKDIR /app/frontend

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy frontend source code
COPY frontend/ ./

# Build the frontend
RUN npm run build

# -------------------------------------------------

# Production stage
FROM python:3.11-slim as production

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY --from=backend /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend /usr/local/bin /usr/local/bin

# Set working directory
WORKDIR /app

# Copy application code
COPY --from=backend /app/backend ./backend/
COPY --from=backend /app/backend_test.py .
COPY --from=backend /app/uploads ./uploads/
COPY --from=backend /app/processed ./processed/

# Copy built frontend
COPY --from=frontend /app/frontend/build ./frontend/build/

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/ || exit 1

# Start the application
CMD ["python", "backend/server.py"]
