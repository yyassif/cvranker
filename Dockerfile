# Using a slim version for a smaller base image
FROM python:3.11.6-slim-bullseye AS base

ARG DEV_MODE
ENV DEV_MODE=$DEV_MODE

# Install GEOS library, Rust, and other dependencies, then clean up
RUN apt-get clean && apt-get update && apt-get install -y \
    libgeos-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    binutils \
    curl \
    git \
    poppler-utils \
    autoconf \
    automake \
    wget \
    libtool \
    python-dev \
    build-essential \
    # Additional dependencies for document handling
    libmagic-dev \
    libpq-dev \
    gcc \
    pandoc && \
    rm -rf /var/lib/apt/lists/*

# Add Rust binaries to the PATH
ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /code

# Copy just the requirements first
COPY ./requirements.txt .

# Upgrade pip and install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

EXPOSE 5050

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5050", "--workers", "6"]
