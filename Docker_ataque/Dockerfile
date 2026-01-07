FROM ubuntu:24.04
RUN apt-get update && apt-get install -y hping3 && rm -rf /var/lib/apt/lists/*
RUN apt-get update && apt-get install -y --no-install-recommends \
    g++ cmake make libpcap-dev iproute2 net-tools gdb nano curl gettext \
    python3 python3-pip nmap \
    iputils-ping nginx php-fpm php-cli \
    && rm -rf /var/lib/apt/lists/*
COPY attack.sh /tmp/attack.sh
RUN chmod +x /tmp/attack.sh
# target.var será montado como volume ou copiado pelo build-images.sh
RUN echo 'TARGET_HOST="172.20.0.20"' > /tmp/target.var
ENTRYPOINT ["/tmp/attack.sh"]
