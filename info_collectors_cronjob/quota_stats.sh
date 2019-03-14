#! /bin/sh

STAT_WORK_DIR="/var/lib/irods/msiExecCmd_bin"
CATEGORY="quota_stats"
TOPIC="seadatacloud"

# Collect stats and write to log
# Only the last event is kept in the "quota.json"
# All events are kept in the "quota-error.log" (TODO: Rotation)
${STAT_WORK_DIR}/quota_stats_collector.py 1>${STAT_WORK_DIR}/quota.json 2>${STAT_WORK_DIR}/quota-error.log

# Also send to RabbitMQ -or- write to Filebeat-supervised log
message=`cat ${STAT_WORK_DIR}/quota.json`
${STAT_WORK_DIR}/rabbitclient.py ${TOPIC} ${CATEGORY} ${message}

# Note that error messages are not sent anywhere!
