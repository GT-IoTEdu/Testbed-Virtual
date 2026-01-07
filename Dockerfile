FROM ubuntu:24.04

WORKDIR /API_IoT_EDU

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    unzip \
    dos2unix \
    pkg-config \
    libmariadb-dev \
    build-essential \
    npm \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /API_IoT_EDU/backend

# Create virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip
RUN pip install --upgrade pip

# Install Python dependencies
RUN pip install mysql-connector-python

# Copy application code
COPY . /API_IoT_EDU

# Install backend dependencies
WORKDIR /API_IoT_EDU/backend
RUN pip install -r requirements.txt

# Install frontend dependencies
WORKDIR /API_IoT_EDU/frontend
RUN npm install --legacy-peer-deps

# Copy environment file
WORKDIR /API_IoT_EDU/backend
RUN cp env_example.txt .env

# Copy wait script
COPY wait_for_db.py /wait_for_db.py

# Make scripts executable
RUN chmod +x /API_IoT_EDU/backend/scripts/*.py

WORKDIR /API_IoT_EDU/ 

CMD ["/bin/bash","/API_IoT_EDU/start.sh"]
