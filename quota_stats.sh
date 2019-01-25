#! /bin/sh

STAT_WORK_DIR="/var/lib/irods/msiExecCmd_bin"
${STAT_WORK_DIR}/quota_stats_collector.py 1>${STAT_WORK_DIR}/quota.json 2>${STAT_WORK_DIR}/quota-error.log
message=`cat ${STAT_WORK_DIR}/quota.json`
${STAT_WORK_DIR}/rabbitclient.py seadatacloud accounting_stats ${message}

