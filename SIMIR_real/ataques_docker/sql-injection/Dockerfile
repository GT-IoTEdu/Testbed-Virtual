FROM python:3.9-alpine
RUN apk add --no-cache git \
    && git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git /sqlmap
WORKDIR /sqlmap
COPY sql-injection/entrypoint.sh /sqlmap/entrypoint.sh
RUN chmod +x /sqlmap/entrypoint.sh
COPY target.var /sqlmap/target.var
ENTRYPOINT ["/sqlmap/entrypoint.sh"]