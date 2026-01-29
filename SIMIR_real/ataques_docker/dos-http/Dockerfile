FROM ubuntu:24.04

RUN apt-get update && apt-get install -y \
    apache2-utils \
    curl \
    wget \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages slowloris

COPY target.var /tmp/target.var
COPY dos-http/entrypoint.sh /tmp/entrypoint.sh
RUN chmod +x /tmp/entrypoint.sh

ENTRYPOINT ["/tmp/entrypoint.sh"]
