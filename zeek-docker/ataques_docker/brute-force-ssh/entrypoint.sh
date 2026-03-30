#!/usr/bin/env bash
source /tmp/target.var
PWDS="/tmp/pass.lst"
for i in $( seq 1 100 ); do
	cat /dev/urandom | tr -dc "a-zA-Z0-9" | fold -w 24 | head -n 1 >> "${PWDS}"
done
timeout 10 /usr/bin/hydra -l root -P ${PWDS} ssh://${TARGET_HOST}