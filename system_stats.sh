#! /bin/sh

message=`/var/lib/irods/msiExecCmd_bin/system_analyser.sh | jq '[to_entries | .[]] | {sysinfo: .}'`
/var/lib/irods/msiExecCmd_bin/rabbitclient.py seadatacloud system_stats ${message}

