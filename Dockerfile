FROM python:3.9.17-alpine3.17

# Install ffmpeg and other dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    sqlite-dev \
    ntfs-3g \
    ffmpeg \
    build-base \
    linux-headers \
    curl \
    tar \
    bash

# Install Rust using rustup
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y --default-toolchain stable \
    && source $HOME/.cargo/env

# Set environment variable to add Rust to the path
ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /app

COPY . .

# Install Python dependencies
RUN pip install -r requirements.txt

ENTRYPOINT ["python", "/app/obscreen.py"]
