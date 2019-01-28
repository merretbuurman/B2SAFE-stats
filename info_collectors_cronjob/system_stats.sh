#! /bin/sh

STAT_WORK_DIR="/var/lib/irods/msiExecCmd_bin"
/var/lib/irods/msiExecCmd_bin/system_analyser.sh | jq '[to_entries | .[]] | {sysinfo: .}'  1>${STAT_WORK_DIR}/system_stats.json.tmp  2>>${STAT_WORK_DIR}/system_stats-error.log
echo $(cat ${STAT_WORK_DIR}/system_stats.json.tmp) >> ${STAT_WORK_DIR}/system_stats.json
# The last line writes everything into one single line, which is better for reading the log by Filebeat

rm ${STAT_WORK_DIR}/system_stats.json.tmp
