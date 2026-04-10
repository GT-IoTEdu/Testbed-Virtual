FROM ubuntu:24.04

RUN apt-get update && apt-get install -y \
    apache2-utils \
    curl \
    wget \
    python3 \
    python3-pip \
    isc-dhcp-client\
    iproute2\
    iputils-ping\
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages slowloris


COPY  entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
