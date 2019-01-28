#!/bin/bash

echo "{"
echo "    \"sysinfo\": { "

mpstat | tail -n 2 | awk '{print $4, $6, $7, $13}' | tr '\n' ' ' | awk '{printf "        \"CPU%s\": %s,\n        \"CPU%s\": %s,\n        \"CPU%s\": %s,\n        \"CPU%s\": %s,\n",$1,$5, $2,$6, $3,$7, $4,$8}'

free -m | grep Mem | awk '{printf "        \"Mem-unit\": \"MB\",\n        \"Mem-total\": %s,\n        \"Mem-used\": %s,\n        \"Mem-free\": %s,\n        \"Mem-shared\": %s,\n        \"Mem-buff/cache\": %s,\n        \"Mem-available\": %s,\n", $2,$3,$4,$5,$6,$7}'

free -m | grep Swap | awk '{printf "        \"Swap-unit\": \"MB\",\n        \"Swap-total\": %s,\n        \"Swap-used\": %s,\n        \"Swap-free\": %s,\n", $2,$3,$4}'

ips -a | grep -v "Server: 130.186.17.96"  | wc -l | awk '{printf "        \"iRodsNumProcs\": %s,\n", $1}'

ps -eo pcpu,pid,user,args | sort -k 1 -r  | wc -l | awk '{printf "        \"TotNumProcs\": %s\n", $1}'

echo "    }"
echo "}"
