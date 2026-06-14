FROM python:3.10-slim

WORKDIR /app

# Install system dependencies required by PyMuPDF and others
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set up a volume for persistent ChromaDB storage if deployed properly
VOLUME ["/app/data", "/app/temp_charts"]

# Hugging Face Spaces expose port 7860 by default
EXPOSE 7860

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
