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

WORKDIR /frontend 
COPY . /frontend
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install -r requirements.txt

# Install frontend dependencies
 
RUN npm install --legacy-peer-deps

  

CMD ["/bin/bash","/frontend/start.sh"]
