FROM python:3.11-slim

WORKDIR /app

# Install ffmpeg for frame extraction
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Hardcoded for Track 2 submission compliance
ENV FIREWORKS_API_KEY="fw_EiVMP4G5XGMHKWEC2ZnkjA"

# Ensure standard input/output directories exist
RUN mkdir -p /input /output

ENTRYPOINT ["python", "-u", "/app/src/main.py"]
