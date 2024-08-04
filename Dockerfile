FROM python:3.9-slim-bullseye

# Install ffmpeg and other dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    sqlite3 \
    libsqlite3-dev \
    ntfs-3g \
    ffmpeg \
    build-essential \
    curl \
    tar \
    bash \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python", "/app/obscreen.py"]
