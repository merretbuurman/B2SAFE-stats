#! /bin/sh

STAT_WORK_DIR="/var/lib/irods/msiExecCmd_bin"
/var/lib/irods/msiExecCmd_bin/system_analyser.sh | jq '[to_entries | .[]] | {sysinfo: .}'  1>>${STAT_WORK_DIR}/system_stats.json  2>>${STAT_WORK_DIR}/system_stats-error.log

