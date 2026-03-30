FROM ubuntu:24.04
RUN apt-get update && apt-get install -y hping3 && rm -rf /var/lib/apt/lists/*
COPY entrypoint.sh /tmp/entrypoint.sh
RUN chmod +x /tmp/entrypoint.sh
# target.var será montado como volume ou copiado pelo build-images.sh
RUN echo 'TARGET_HOST="172.18.0.2"' > /tmp/target.var
ENTRYPOINT ["/tmp/entrypoint.sh"]
