FROM ubuntu:24.04
RUN apt update
RUN apt install yersinia -y
RUN apt-get install net-tools -y
COPY entrypoint.sh /tmp/entrypoint.sh
RUN chmod +x /tmp/entrypoint.sh
ENTRYPOINT ["/tmp/entrypoint.sh"]
