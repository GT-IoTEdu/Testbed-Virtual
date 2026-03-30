FROM ubuntu:24.04
RUN apt-get update
RUN apt-get install hydra -y
COPY brute-force-ssh/entrypoint.sh /tmp/entrypoint.sh
RUN chmod +x /tmp/entrypoint.sh

ENTRYPOINT ["/tmp/entrypoint.sh"]
