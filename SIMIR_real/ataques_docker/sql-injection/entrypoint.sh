#!/bin/sh
set -e
. /sqlmap/target.var
# Executa o sqlmap com a variável (usamos exec para substituir o shell pelo processo)
exec python /sqlmap/sqlmap.py -u "$TARGET_WEB" --batch --level=3