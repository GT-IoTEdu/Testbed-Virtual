#!/bin/sh
set -e

# Executa o sqlmap com a variável (usamos exec para substituir o shell pelo processo)
exec python /sqlmap/sqlmap.py -u "http://host.docker.internal:8090" --batch --level=3
