B2SAFE Accounting (with APEL system)
============================================

This describes how to collect accounting info from B2SAFE
and send it to Logstash using Filebeat or RabbitMQ.


# Gathering B2SAFE accounting info about the system and quotas

Install the packages jq (https://stedolan.github.io/jq) and sysstat.

```
sudo yum install jq
sudo yum install sysstat           # for the command mpstat
```

Copy these files into `/var/lib/irods/msiExecCmd_bin`:

* quota_stats.sh
* quota_stats_collector.py
* system_stats.sh
* system_analyser.sh
* rabbitclient.py

Make sure they are owned by your irods user and executable:

```
sudo chown irods:irods ...
sudo chmod ug+x ...
```

As a test run, just collect the info and print it to stdout/
stderr:

```
[frieda@friedasserver ~]$ # Just run the collection and echo the info (no storing):
[frieda@friedasserver ~]$ DIR="/var/lib/irods/msiExecCmd_bin"
[frieda@friedasserver ~]$ sudo $DIR/quota_stats_collector.py 
[frieda@friedasserver ~]$ sudo $DIR/system_analyser.sh 
```

Then run the collection:

```
[frieda@friedasserver ~]$ DIR="/var/lib/irods/msiExecCmd_bin"
[frieda@friedasserver ~]$ sudo $DIR/quota_stats.sh 
[frieda@friedasserver ~]$ sudo $DIR/system_stats.sh 
```

You can now check the outputs:

```
[frieda@friedasserver ~]$ # Check the collected info:
[frieda@friedasserver ~]$ sudo cat $DIR/system_stats.json
[frieda@friedasserver ~]$ sudo cat $DIR/quota.json

[frieda@friedasserver ~]$ # Check the error logs:
[frieda@friedasserver ~]$ sudo cat $DIR/system_stats-error.log
[frieda@friedasserver ~]$ sudo cat $DIR/quota-error.log
```



Or create a cronjob to run them:

```
$ crontab -l
12 * * * * /var/lib/irods/msiExecCmd_bin/quota_stats.sh
*/10 * * * * /var/lib/irods/msiExecCmd_bin/system_stats.sh | /bin/jq '[to_entries | .[]] | {sysinfo: .}'
```



# RabbitMQ or Filebeat

Information is sent to RabbitMQ _and/or_ written to log files
by the *rabbitclient.py*.


## Client

### Hand-on 

Test the `rabbitclient.py` script:

```
python rabbitclient.py --help

# Write to /var/lib/irods/log/...
python rabbitclient.py -d -o mytopic mycategory mymessage
python rabbitclient.py -d -l mylog.log mytopic mycategory mymessage

# Write to ./
python rabbitclient.py -d -o -bd '.' mytopic mycategory mymessage
python rabbitclient.py -d -l mylog.log -bd '.' mytopic mycategory mymessage

# Write to RabbitMQ, *not* to file
# Make sure to adapt host, username, password etc. inside the script!
python rabbitclient.py -r -nf -d -o myexchange myroutingkey mymessage
python rabbitclient.py -r -nf -d -l mylog.log myexchange myroutingkey mymessage
```

Note: If errors occur during connection with RabbitMQ, the messages will
be written to file. However, some errors that can happen server-side which
lead to messages being lost, cannot be detected, so messages are not guaranteed
to arrive.

### What does it do?

`rabbitclient.py` is a client that is called by B2SAFE when specific
rules are executed, or by the cronjobs above.
B2SAFE calls the client andpasses some info to it.
The python script takes care of either sending it to a RabbitMQ instance,
or writing it to specific files. The latter is the default.

The topic and the category are defined by B2SAFE.

Text files:

* Messages are written into `/var/lib/irods/log/<topic>/<category>.log`
* These files are rotated

RabbitMQ:

* Sends messages to exchange `<topic>`, routing key `<category>`
* Host, virtual host, port, ssl setting, username and password need to be
  provided inside the script
* the exchange needs to exist, and the routing keys need to lead somewhere
  (i.e. bindings and queues need to be defined)! The client does not notice
  if the server drops messages.
* So, make sure to configure an alternate exchange for `<topic>` on the RabbitMQ server.

Note: If errors occur during connection with RabbitMQ, the messages will
be written to file. However, some errors that can happen server-side which
lead to messages being lost, cannot be detected, so messages are not guaranteed
to arrive.



## Run filebeat

In order to collect the info from the logs and send them to
Logstash, run a Filebeat instance, using the files 
`docker-compose.yml` and `filebeat.yml` from this repo.

Of course, `docker` and `docker-compose` need to be installed.

Make sure you adapt the paths inside the `docker-compose.yml`
according to your system.

```
mkdir FILEBEAT
cd FILEBEAT
vi docker-compose.yml       # add content
vi filebeat.yml             # add content
sudo chown 0 filebeat.yml
docker-compose up

```

## Configure Logstash

For each of the five types, the Logstash instance has to be
configured.

* input: Either a rabbitmq-input (where Logstash polls for messages)
 or a beat-input (where logstash listens for pushed messages)
* filters: Filters for all five types of messages
* output: Output to RabbitMQ or to ElasticSearch...




# Types of information collected

## quota_stats / accounting_stats / acc (cronjob, JSON)

* *Cronjob* runs quota_stats_collector.py, collected via quota_stats.sh
* `quota_stats_collector.py` collects info and writes it to stdout/stderr.
* `quota_stats.sh` writes it to the log `/var/lib/irods/msiExecCmd_bin/quota.json` (stdout)
  and `/var/lib/irods/msiExecCmd_bin/quota-error.json` (stderr) as json info on one line.
* This info is then sent to RabbitMQ queue `quota_stats` and/or written to `/var/lib/irods/logs/<topic>/quota_stats`.
* The whole thing has to be triggered by a cronjob
* Claudio's Logstash conf: "rabbitmq_b2safe_acc.conf" (exchange "b2safe", key "accounting_stats", queue "accounting", type "irods_accounting")

*WARNING:* The Logstash config for this contains the zone, so it is not generic!

Example:

```
[frieda@friedasserver ~]$ DIR="/var/lib/irods/msiExecCmd_bin"
[frieda@friedasserver ~]$ sudo $DIR/quota_stats_collector.py 
{"collections": {"/myzone/batches": {"objects": 52, "users": {"hilda": {"objects": 47, "size": 20201}, "vero": {"objects": 0, "size": null}, "nagiuser": {"objects": 0, "size": null}, "klaus": {"objects": 0, "size": null}, "foobar": {"objects": 0, "size": null}, "anon": {"objects": 0, "size": null}, "mira": {"objects": 0, "size": null}}, "groups": {"ralph": {"objects": 0, "size": null}, "public": {"objects": 0, "size": null}}, "size": 22711}, "/myzone/trash": {"objects": 1171, "users": {"hilda": {"objects": 58, "size": 16752}, "vero": {"objects": 0, "size": null}, "nagiuser": {"objects": 1094, "size": 32078}, "klaus": {"objects": 0, "size": null}, "foobar": {"objects": 0, "size": null}, "anon": {"objects": 0, "size": null}, "mira": {"objects": 4, "size": 62}}, "groups": {"ralph": {"objects": 0, "size": null}, "public": {"objects": 0, "size": null}}, "size": 49539}, "/myzone": {"objects": 1260, "users": {"hilda": {"objects": 130, "size": 40817}, "vero": {"objects": 0, "size": null}, "nagiuser": {"objects": 1094, "size": 32078}, "klaus": {"objects": 0, "size": null}, "foobar": {"objects": 0, "size": null}, "anon": {"objects": 0, "size": null}, "mira": {"objects": 15, "size": 146}}, "groups": {"ralph": {"objects": 0, "size": null}, "public": {"objects": 0, "size": null}}, "size": 76227}, "/myzone/sdc": {"objects": 0, "users": {"hilda": {"objects": 0, "size": null}, "vero": {"objects": 0, "size": null}, "nagiuser": {"objects": 0, "size": null}, "klaus": {"objects": 0, "size": null}, "foobar": {"objects": 0, "size": null}, "anon": {"objects": 0, "size": null}, "mira": {"objects": 0, "size": null}}, "groups": {"ralph": {"objects": 0, "size": null}, "public": {"objects": 0, "size": null}}, "size": null}, "/myzone/cloud": {"objects": 14, "users": {"hilda": {"objects": 14, "size": 189}, "vero": {"objects": 0, "size": null}, "nagiuser": {"objects": 0, "size": null}, "klaus": {"objects": 0, "size": null}, "foobar": {"objects": 0, "size": null}, "anon": {"objects": 0, "size": null}, "mira": {"objects": 0, "size": null}}, "groups": {"ralph": {"objects": 0, "size": null}, "public": {"objects": 0, "size": null}}, "size": 189}, "/myzone/orders": {"objects": 3, "users": {"hilda": {"objects": 3, "size": 507}, "vero": {"objects": 0, "size": null}, "nagiuser": {"objects": 0, "size": null}, "klaus": {"objects": 0, "size": null}, "foobar": {"objects": 0, "size": null}, "anon": {"objects": 0, "size": null}, "mira": {"objects": 0, "size": null}}, "groups": {"ralph": {"objects": 0, "size": null}, "public": {"objects": 0, "size": null}}, "size": 507}, "/myzone/json_inputs": {"objects": 8, "users": {"hilda": {"objects": 8, "size": 3168}, "vero": {"objects": 0, "size": null}, "nagiuser": {"objects": 0, "size": null}, "klaus": {"objects": 0, "size": null}, "foobar": {"objects": 0, "size": null}, "anon": {"objects": 0, "size": null}, "mira": {"objects": 0, "size": null}}, "groups": {"ralph": {"objects": 0, "size": null}, "public": {"objects": 0, "size": null}}, "size": 3168}, "/myzone/mystuff": {"objects": 0, "users": {"hilda": {"objects": 0, "size": null}, "vero": {"objects": 0, "size": null}, "nagiuser": {"objects": 0, "size": null}, "klaus": {"objects": 0, "size": null}, "foobar": {"objects": 0, "size": null}, "anon": {"objects": 0, "size": null}, "mira": {"objects": 0, "size": null}}, "groups": {"ralph": {"objects": 0, "size": null}, "public": {"objects": 0, "size": null}}, "size": null}, "/myzone/home": {"objects": 12, "users": {"hilda": {"objects": 0, "size": null}, "vero": {"objects": 0, "size": null}, "nagiuser": {"objects": 0, "size": null}, "klaus": {"objects": 0, "size": null}, "foobar": {"objects": 0, "size": null}, "anon": {"objects": 0, "size": null}, "mira": {"objects": 11, "size": 84}}, "groups": {"ralph": {"objects": 0, "size": null}, "public": {"objects": 0, "size": null}}, "size": 113}}, "groups": {"ralph": ["rods"], "public": ["foobar", "import", "vero", "hilda", "nagiuser", "rods", "klaus", "mira"]}}
```



## system_stats / sys (cronjob, JSON)

* *Cronjob* runs system_analyzer.sh, collected via system_stats.sh
* `system_analyser.sh` collects info and writes it to stdout/stderr
* `system_stats.sh` writes it to the log `/var/lib/irods/msiExecCmd_bin/system_stats.json` (stdout) or 
`/var/lib/irods/msiExecCmd_bin/system_stats-error.json` (stderr) as json info on one line.
* This info is then sent to RabbitMQ queue `system_stats` and/or written to `/var/lib/irods/logs/<topic>/system_stats`.
* The whole thing has to be triggered by a cronjob
* Claudio's logstash config: "rabbitmq_b2safe_sys.conf" (exchange "b2safe", key "system_stats", queue "system", type "system_stats")

Example log line (JSON)

```
{ "sysinfo": [ { "key": "sysinfo", "value": { "CPU%usr": 3.23, "CPU%sys": 5.15, "CPU%iowait": 0.01, "CPU%idle": 91.1, "Mem-unit": "MB", "Mem-total": 1811, "Mem-used": 809, "Mem-free": 212, "Mem-shared": 125, "Mem-buff/cache": 789, "Mem-available": 607, "Swap-unit": "MB", "Swap-total": 1023, "Swap-used": 55, "Swap-free": 968, "iRodsNumProcs": 2, "TotNumProcs": 199 } } ] }
```


Example run:

```
[frieda@friedasserver ~]$ sudo $DIR/system_analyser.sh 
{
    "sysinfo": { 
        "CPU%usr": 0.65,
        "CPU%sys": 1.33,
        "CPU%iowait": 0.00,
        "CPU%idle": 97.53,
        "Mem-unit": "MB",
        "Mem-total": 1811,
        "Mem-used": 174,
        "Mem-free": 240,
        "Mem-shared": 125,
        "Mem-buff/cache": 1396,
        "Mem-available": 1278,
        "Swap-unit": "MB",
        "Swap-total": 1023,
        "Swap-used": 1,
        "Swap-free": 1022,
        "iRodsNumProcs": 2,
        "TotNumProcs": 149
    }
}
```


## user_login / access / auth (by iRODS, KV-pairs)

* *Triggered by iRODS* in the PEP `pep_auth_agent_auth_response_pre` (this has to be configured in _core.re_).
* Logs are written to: /var/lib/irods/log/seadatacloud/user_login.log
* Claudio's logstash config: "rabbitmq_b2safe_auth.conf" (exchange "b2safe", key "user_login", queue "access", type "access")


Example log lines (kv-pairs):

```
auth_scheme=native, client_addr=999.172.12.12, proxy_rods_zone=sdcDKRZ, proxy_user_name=rods, user_rods_zone=sdcDKRZ, user_user_name=rods
auth_scheme=native, client_addr=999.212.98.101, proxy_rods_zone=sdcDKRZ, proxy_user_name=nagiosProbeUser, user_rods_zone=sdcDKRZ, user_user_name=nagiosProbeUser
```

## user_op / operation / op (by iRODS, KV-pairs)

* *Triggered by iRODS* during (this has to be configured in _core.re_):

  * `acPostProcForCollCreate`: imkdir, ireg, irsync collections (collection creation and registration)
  * `acPostProcForModifyDataObjMeta`: iput, imv, icp, irsync objects, irepl, ichksum
  * `acPostProcForOpen`: iput -f, irsync, iget, igetwild, icp
  * `acPostProcForRmColl`: irm -r collection
  * `acPostProcForDelete`: irm
* Claudio's logstash config: "rabbitmq_b2safe_op.conf" (exchange "b2safe", key "user_op", queue "operation", type "operation")

Example log lines (kv-pairs):

```
trigger=acPostProcForModifyDataObjMeta, chksum=, connectOption=iput, dataId=16506, dataSize=0, dataType=generic, destRescName=, filePath=/var/lib/irods/Vault2/home/rods/woof.txt, objPath=/sdcDKRZ/home/rods/woof.txt, replNum=0, replStatus=1, rescName=defaultRescDKRZ, rodsZoneClient=sdcDKRZ, rodsZoneProxy=sdcDKRZ, userNameClient=rods, userNameProxy=rods, writeFlag=1, clientAddr=127.0.0.1
trigger=acPostProcForModifyDataObjMeta, chksum=, connectOption=iput, dataId=16507, dataSize=29, dataType=generic, destRescName=, filePath=/var/lib/irods/Vault2/home/nagiosProbeUser/tmp.OEiyNqz2cY, objPath=/sdcDKRZ/home/nagiosProbeUser/tmp.OEiyNqz2cY, replNum=0, replStatus=1, rescName=defaultRescDKRZ, rodsZoneClient=sdcDKRZ, rodsZoneProxy=sdcDKRZ, userNameClient=nagiosProbeUser, userNameProxy=nagiosProbeUser, writeFlag=0, clientAddr=83.212.98.101
```


## b2safe_op / b2safe_operation / b2safe (by B2SAFE, KV-pairs with semicolon)

* *Triggered by B2SAFE* during *replication* and similar actions, I believe!
* See `/opt/eudat/b2safe/rulebase/eudat.re` : `EUDATMessage(*queue, *message) { ... }`
* Claudio's logstash config: "rabbitmq_b2safe_b2safe.conf"

No example messages yet...

Example message from Claudio:

```
user=claudio;zone=sdcCineca;rule=EUDATReplication;status=true;response=source=/sdcCineca/home/claudio/test_data.txt;;destination=/sdcCineca/home/claudio/test_data2.txt;;registered=true;;recursive=true
```


# Checklist

* Install `rabbitclient.py`to `/var/lib/irods/msiExecCmd_bin` and make executable by irods
* Install _system_stats.sh_, _quota_stats.sh_, _quota_stats_collector.py_, _system_analyser.sh_ to `/var/lib/irods/msiExecCmd_bin` and make executable by irods (for *system_stats* and *quota_stats*)
* Make cronjob for system_stats and quota_stats (for *system_stats* and *quota_stats*)
* Add rule to `/etc/irods/core.re` for `pep_auth_agent_auth_response_pre` (for *user_login*)
* Add rules to `/etc/irods/core.re` for `acPostProcForCollCreate`, `acPostProcForModifyDataObjMeta`, `acPostProcForOpen`, `acPostProcForRmColl`, `acPostProcForDelete` (for *user_op*)
* Add method to `/opt/eudat/b2safe/rulebase/eudat.re` for `EUDATMessage(*queue, *message)` (for *b2safe_op*)
* Configure Logstash for all five log categories
* Configure Logstash to output the parsed info (to
  RabbitMQ and/or Elasticsearch)

Using Filebeat

* Install Filebeat, to read the proper logs and send to Logstash
* Add Filebeat input to Logstash

Using RabbitMQ

* Install RabbitMQ
* Create exchange _seadatacloud_ (topic)
* Create queues for the five categories: _b2safe_op_, _user_op_, user_login_, _system_stats_, _quota_stats_
* Add RabbitMQ info (host, username, password, ...) to rabbitclient.py

How to test

```
# on b2safe machine:

sudo -i
cd /var/lib/irods/msiExecCmd_bin

### user login:
# should run automatically

### system_stats:
./system_stats.sh

### quota_stats:
./quota_stats.sh

### user_op:
echo "foo" > test.txt
iput -f test.txt

### b2safe_op:
# Dunno how!

### Check:
# Check if stuff has been written into the logs:
sudo ls -lpah /var/lib/irods/log/seadatacloud

# If not, check here:
vi /var/lib/irods/msiExecCmd_bin/quota.json
vi /var/lib/irods/msiExecCmd_bin/quota-error.log
vi /var/lib/irods/msiExecCmd_bin/system_stats.json
vi /var/lib/irods/msiExecCmd_bin/system_stats-error.log

### Check on RabbitMQ
# Check if messages in the queues

### Check on logstash:
# Check in log if messages were parsed, from Filebeat
# Check in log if messages were parsed, from RabbitMQ

### Check on Filebeat:
# Cannot see

### Check on ElasticSearch





```
