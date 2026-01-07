FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && \
    apt install -y suricata && \
    apt clean

COPY etc/ /etc/suricata/
COPY rules/ /var/lib/suricata/rules/

CMD ["suricata", "-c", "/etc/suricata/suricata.yaml", "-i", "enp4s0"]
