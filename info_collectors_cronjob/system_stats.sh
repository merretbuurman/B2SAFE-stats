#! /bin/sh

STAT_WORK_DIR="/var/lib/irods/msiExecCmd_bin"

# Collect stats and write to log
/var/lib/irods/msiExecCmd_bin/system_analyser.sh | jq '[to_entries | .[]] | {sysinfo: .}'  1>${STAT_WORK_DIR}/system_stats.json.tmp  2>>${STAT_WORK_DIR}/system_stats-error.log

# Write everything into one single line, which is better for reading the log by Filebeat
echo $(cat ${STAT_WORK_DIR}/system_stats.json.tmp) >> ${STAT_WORK_DIR}/system_stats.json
rm ${STAT_WORK_DIR}/system_stats.json.tmp
