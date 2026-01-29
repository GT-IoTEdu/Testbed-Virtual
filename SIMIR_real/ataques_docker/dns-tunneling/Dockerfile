FROM ubuntu:24.04
RUN apt-get update && apt-get install -y dnsutils && rm -rf /var/lib/apt/lists/*
COPY entrypoint.sh /tmp/entrypoint.sh
RUN chmod +x /tmp/entrypoint.sh
ENTRYPOINT ["/tmp/entrypoint.sh"]
