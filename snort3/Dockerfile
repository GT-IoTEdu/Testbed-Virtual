# Use uma imagem base comum
FROM ubuntu:22.04

# Evita prompts interativos durante a instalação
ENV DEBIAN_FRONTEND=noninteractive

# 1. Instala TODAS as dependências que descobrimos de uma vez
RUN apt update && apt install -y \
    build-essential \
    g++ \
    cmake \
    pkg-config \
    flex \
    libhwloc-dev \
    libluajit-5.1-dev \
    libssl-dev \
    libpcre2-dev \
    zlib1g-dev \
    libpcap-dev \
    libdaq-dev \
    libdnet-dev \
    libgoogle-perftools-dev \
    wget \
    iproute2 \
    nano \
    && apt clean && rm -rf /var/lib/apt/lists/*

# 2. Compila o libdaq v3.0.22 (A lição que aprendemos)
WORKDIR /tmp
RUN wget https://github.com/snort3/libdaq/archive/refs/tags/v3.0.22.tar.gz -O libdaq-3.0.22.tar.gz \
    && tar -xzvf libdaq-3.0.22.tar.gz \
    && cd libdaq-3.0.22 \
    && ./bootstrap \
    && ./configure \
    && make \
    && make install \
    && cd .. \
    && rm -rf libdaq-3.0.22.tar.gz libdaq-3.0.22

# 3. Atualiza o cache da biblioteca (A boa prática)
RUN ldconfig

# 4. Baixa, compila e instala o Snort
# (AJUSTE: Trocamos o 'COPY' por 'wget' para espelhar seu histórico)
ENV my_path=/opt/snort3

RUN wget https://github.com/snort3/snort3/archive/refs/tags/3.9.7.0.tar.gz -O /tmp/snort3-3.9.7.0.tar.gz \
    && tar -xzvf /tmp/snort3-3.9.7.0.tar.gz -C /tmp \
    && cd /tmp/snort3-3.9.7.0 \
    && ./configure_cmake.sh --prefix=$my_path \
    && cd build \
    && make \
    && make install \
    && cd / \
    && rm -rf /tmp/snort3-3.9.7.0*

# Configuração final do ambiente
ENV PATH="${my_path}/bin:${PATH}"
WORKDIR $my_path

# 6. Cria diretório de logs
RUN mkdir -p /opt/snort3/logs

# 7. Copia arquivos de configuração e script
COPY local.rules /opt/snort3/etc/snort/rules/local.rules
COPY snort.lua /opt/snort3/etc/snort/snort.lua
COPY start_snort.sh /opt/snort3/start_snort.sh

# 8. Torna o script executável
RUN chmod +x /opt/snort3/start_snort.sh
# 9. Define o ponto de entrada
ENTRYPOINT ["/opt/snort3/start_snort.sh"]

# 10. Interface padrão (pode ser substituída)
CMD ["enp0s3"]
# Comando para manter o container vivo para inspeção
# CMD ["tail", "-f", "/dev/null"]