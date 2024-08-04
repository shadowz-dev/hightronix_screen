FROM python:3.9.17-alpine3.17

# Install ffmpeg and other dependencies
RUN apk add --no-cache gcc musl-dev sqlite-dev ntfs-3g ffmpeg build-base linux-headers

# Install Rust and Cargo
RUN apk add --no-cache curl \
    && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
    && source $HOME/.cargo/env \
    && rustup default stable \

WORKDIR /app

COPY . .

# Install Python dependencies
RUN /root/.cargo/bin/cargo --version \
    && pip install -r requirements.txt

ENTRYPOINT ["python", "/app/obscreen.py"]
