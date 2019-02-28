#!/usr/bin/env python

import pika
import sys
import logging
import logging.handlers
import argparse
import os

# TODO: Good way to set these! Read from file?
SEND_TO_RABBIT = True
WRITE_TO_TOPIC_LOG = True
BASE_DIR = '/var/lib/irods/log/'
BASE_DIR = BASE_DIR.rstrip(os.sep)
STAT_LOGS_MAX_SIZE=6000000
STAT_LOGS_BACKUP_COUNT=9

logger = logging.getLogger('rabbitMQClient')

def pubMessage(args):

    msg = ' '.join(args.message)
    logger.info('Publishing the message [{}] to the echange (topic) {}'
                + ' with the routing key (queue): {}'.format(msg, 
                                                             args.exchange,
                                                             args.routingKey))
    credentials = pika.PlainCredentials('xxxxxx', 'yyyyy')
    connection = pika.BlockingConnection(pika.ConnectionParameters(
                                         host='130.186.13.176', port=5672, 
                                         credentials=credentials))
    channel = connection.channel()

    channel.basic_publish(exchange=args.exchange,
                          routing_key=args.routingKey,
                          body=msg)
    connection.close()

def make_topic_logger_and_write(msg, topic, base_dir):
    '''
    Rotation is fine with Filebeat, see this thread on the
    Filebeat forum:
    https://discuss.elastic.co/t/will-filebeat-handle-properly-the-underlying-log-file-rotation/56119
    "Filebeat will continue to read from the rotated log even
    after it is moved until the file reaches a certain age
    (base on modified time) or is deleted. It tracks the file
    by inode number which doesn't change when renamed. It will
    also periodically look for a new files matching the mysqld.log
    file name so that can start reading from the new log file
    when it is created."
    '''
    # TODO: Check that name is not ending with dot-integer!
    topic_logger = logging.getLogger(topic)
    topic_logger.propagate = False
    topic_logger.setLevel(logging.INFO)
    filepath = BASE_DIR + os.sep + topic + '.log'
    han = logging.handlers.RotatingFileHandler(filepath,
        maxBytes=STAT_LOGS_MAX_SIZE,
        backupCount=STAT_LOGS_BACKUP_COUNT
    )
    formatter = logging.Formatter('%(message)s')
    han.setFormatter(formatter)
    topic_logger.addHandler(han)
    topic_logger.info(msg)


def write_topic_log(args):
    """Note: Routing keys are: system_stats, user_op, user_login, accounting_stats, b2safe_op"""
    msg = ' '.join(args.message)

    # Remove newlines:
    # TODO TEST!
    if '\n' in msg:
      msg = msg.replace('\n', ' ')

    # Write to log
    make_topic_logger_and_write(msg, args.routingKey, BASE_DIR)

def _initializeLogger(args):
    """initialize the logger instance."""

    if (args.debug):
        logger.setLevel(logging.DEBUG)
    if (args.log):
        han = logging.handlers.RotatingFileHandler(args.log,
                                                   maxBytes=6000000,
                                                   backupCount=9)
        formatter = logging.Formatter('%(asctime)s %(levelname)s:%(message)s')
        han.setFormatter(formatter)
        logger.addHandler(han)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='EUDAT B2SAFE rabbitMQ client')

    parser.add_argument("-l", "--log", help="Path to the log file")
    parser.add_argument("-d", "--debug", help="Show debug output",
                        action="store_true")
    parser.add_argument("exchange", help='the message topic')
    parser.add_argument("routingKey", help='the message queue')
    parser.add_argument("message", nargs='+', help='the message content')
    parser.set_defaults(func=pubMessage)

    _args = parser.parse_args()
    _initializeLogger(_args)
    
    if SEND_TO_RABBIT:
      pubMessage(_args)

    if WRITE_TO_TOPIC_LOG:
      write_topic_log(_args)
