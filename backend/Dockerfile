FROM python:3.11-slim

WORKDIR /app

# Install system compiler tools for scikit-learn / statsmodels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend codebase
COPY . .

# Expose port (Hugging Face Spaces default port is 7860, but standard is 8000)
# We will use 7860 for default compatibility with Hugging Face, or standard port
EXPOSE 7860

# Start server (Hugging Face sets PORT environment variable, we read it)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
