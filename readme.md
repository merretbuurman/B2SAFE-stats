B2SAFE Accounting (with APEL system)
============================================

This describes how to collect accounting info from B2SAFE
and send it to Logstash using Filebeat.

Note: So far, only for the *system_stats* and *quota_stats*, 
triggered by cronjobs. The info collection triggered directly 
by the irods rules is not included here yet!

# Gathering B2SAFE accounting info

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


# What does it do?

## During rule execution: Store Stats Info

`store_stat_info.py` is a client that is called by B2SAFE when specific
rules are executed. B2SAFE calls the client and passes some info to it.
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

## Quota Stats

`quota_stats_collector.py` collects info and writes it to stdout/stderr:

```
[frieda@friedasserver ~]$ DIR="/var/lib/irods/msiExecCmd_bin"
[frieda@friedasserver ~]$ sudo $DIR/quota_stats_collector.py 
{"collections": {"/myzone/batches": {"objects": 52, "users": {"hilda": {"objects": 47, "size": 20201}, "vero": {"objects": 0, "size": null}, "nagiuser": {"objects": 0, "size": null}, "klaus": {"objects": 0, "size": null}, "foobar": {"objects": 0, "size": null}, "anon": {"objects": 0, "size": null}, "mira": {"objects": 0, "size": null}}, "groups": {"ralph": {"objects": 0, "size": null}, "public": {"objects": 0, "size": null}}, "size": 22711}, "/myzone/trash": {"objects": 1171, "users": {"hilda": {"objects": 58, "size": 16752}, "vero": {"objects": 0, "size": null}, "nagiuser": {"objects": 1094, "size": 32078}, "klaus": {"objects": 0, "size": null}, "foobar": {"objects": 0, "size": null}, "anon": {"objects": 0, "size": null}, "mira": {"objects": 4, "size": 62}}, "groups": {"ralph": {"objects": 0, "size": null}, "public": {"objects": 0, "size": null}}, "size": 49539}, "/myzone": {"objects": 1260, "users": {"hilda": {"objects": 130, "size": 40817}, "vero": {"objects": 0, "size": null}, "nagiuser": {"objects": 1094, "size": 32078}, "klaus": {"objects": 0, "size": null}, "foobar": {"objects": 0, "size": null}, "anon": {"objects": 0, "size": null}, "mira": {"objects": 15, "size": 146}}, "groups": {"ralph": {"objects": 0, "size": null}, "public": {"objects": 0, "size": null}}, "size": 76227}, "/myzone/sdc": {"objects": 0, "users": {"hilda": {"objects": 0, "size": null}, "vero": {"objects": 0, "size": null}, "nagiuser": {"objects": 0, "size": null}, "klaus": {"objects": 0, "size": null}, "foobar": {"objects": 0, "size": null}, "anon": {"objects": 0, "size": null}, "mira": {"objects": 0, "size": null}}, "groups": {"ralph": {"objects": 0, "size": null}, "public": {"objects": 0, "size": null}}, "size": null}, "/myzone/cloud": {"objects": 14, "users": {"hilda": {"objects": 14, "size": 189}, "vero": {"objects": 0, "size": null}, "nagiuser": {"objects": 0, "size": null}, "klaus": {"objects": 0, "size": null}, "foobar": {"objects": 0, "size": null}, "anon": {"objects": 0, "size": null}, "mira": {"objects": 0, "size": null}}, "groups": {"ralph": {"objects": 0, "size": null}, "public": {"objects": 0, "size": null}}, "size": 189}, "/myzone/orders": {"objects": 3, "users": {"hilda": {"objects": 3, "size": 507}, "vero": {"objects": 0, "size": null}, "nagiuser": {"objects": 0, "size": null}, "klaus": {"objects": 0, "size": null}, "foobar": {"objects": 0, "size": null}, "anon": {"objects": 0, "size": null}, "mira": {"objects": 0, "size": null}}, "groups": {"ralph": {"objects": 0, "size": null}, "public": {"objects": 0, "size": null}}, "size": 507}, "/myzone/json_inputs": {"objects": 8, "users": {"hilda": {"objects": 8, "size": 3168}, "vero": {"objects": 0, "size": null}, "nagiuser": {"objects": 0, "size": null}, "klaus": {"objects": 0, "size": null}, "foobar": {"objects": 0, "size": null}, "anon": {"objects": 0, "size": null}, "mira": {"objects": 0, "size": null}}, "groups": {"ralph": {"objects": 0, "size": null}, "public": {"objects": 0, "size": null}}, "size": 3168}, "/myzone/mystuff": {"objects": 0, "users": {"hilda": {"objects": 0, "size": null}, "vero": {"objects": 0, "size": null}, "nagiuser": {"objects": 0, "size": null}, "klaus": {"objects": 0, "size": null}, "foobar": {"objects": 0, "size": null}, "anon": {"objects": 0, "size": null}, "mira": {"objects": 0, "size": null}}, "groups": {"ralph": {"objects": 0, "size": null}, "public": {"objects": 0, "size": null}}, "size": null}, "/myzone/home": {"objects": 12, "users": {"hilda": {"objects": 0, "size": null}, "vero": {"objects": 0, "size": null}, "nagiuser": {"objects": 0, "size": null}, "klaus": {"objects": 0, "size": null}, "foobar": {"objects": 0, "size": null}, "anon": {"objects": 0, "size": null}, "mira": {"objects": 11, "size": 84}}, "groups": {"ralph": {"objects": 0, "size": null}, "public": {"objects": 0, "size": null}}, "size": 113}}, "groups": {"ralph": ["rods"], "public": ["foobar", "import", "vero", "hilda", "nagiuser", "rods", "klaus", "mira"]}}
```

`quota_stats.sh` appends it to the logs `/var/lib/irods/msiExecCmd_bin/quota.json`
  and `/var/lib/irods/msiExecCmd_bin/quota-error.json` as json info on one line.

## System stats

`system_analyser.sh` collects info and writes it to stdout/stderr:

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

`system_stats.sh` appends it to the logs `/var/lib/irods/msiExecCmd_bin/system_stats.json` and 
`/var/lib/irods/msiExecCmd_bin/system_stats-error.json` as json info on one line.


## Run Filebeat

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


# Summary


Categories:

    """Note: categories are: system_stats, user_op, user_login, accounting_stats, b2safe_op"""



* system_stats: Cronjob runs system_analyzer.sh, collected via system_stats.sh
* user_login: ?
* accounting_stats: Cronjob runs quota_stats_collector.py, collected via quota_stats.sh
* b2safe_op: ?
* user_op : Created by B2SAFE in certain rules:

```
[k204208@sdc-b2safe-test ~]$ grep -r user_op /etc/irods/*.re
/etc/irods/core.re:    msiExecCmd("rabbitclient.py", "seadatacloud user_op '*op_info'",
[k204208@sdc-b2safe-test ~]$ grep -r b2safe_op /etc/irods/*.re
[k204208@sdc-b2safe-test ~]$ grep -r accounting_stats /etc/irods/*.re
[k204208@sdc-b2safe-test ~]$ grep -r user_login /etc/irods/*.re
[k204208@sdc-b2safe-test ~]$ grep -r system_stats /etc/irods/*.re
```
