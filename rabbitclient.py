#!/usr/bin/env python

import sys
import logging
import logging.handlers
import argparse
import os
# Note: pika is imported below in case RabbitMQ should be used!

# Where to send (will be overridden by command line args)
SEND_TO_RABBIT = False
WRITE_TO_CATEGORY_LOG = True

# Text file settings
BASE_DIR = '/var/lib/irods/log/'
BASE_DIR = BASE_DIR.rstrip(os.sep)
STAT_LOGS_MAX_SIZE=6000000
STAT_LOGS_BACKUP_COUNT=9

# RabbitMQ settings
RABBIT_USER = 'xxxxx'
RABBIT_PASSWORD = 'xxxxx'
RABBIT_HOST = 'dummy.rabbit.it'
RABBIT_PORT = 5672


# This is the logger for the script
logger = logging.getLogger('stat_info_distributor')

def pub_message_to_rabbit(message_list, topic, category):

    msg = ' '.join(message_list)
    logger.info('Publishing the message [{}] to the exchange (topic) {}'
                + ' with the routing key (category): {}'.format(msg, 
                                                             topic,
                                                             category))
    credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASSWORD)

    # TODO: Make sure to catch and handle all kinds of exceptions!
    connection = pika.BlockingConnection(pika.ConnectionParameters(
                                         host=RABBIT_HOST, port=RABBIT_PORT, 
                                         credentials=credentials))
    channel = connection.channel()

    channel.basic_publish(exchange=topic,
                          routing_key=category,
                          body=msg)
    connection.close()

def make_category_logger_and_write(msg, category, base_dir):
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

    # If "topic" ends by dot-integer, add an underscore,
    # otherwise this will lead to confusing filenames during
    # log-rotation.
    if '.' in category:
        tmp = category.split('.')
        if tmp[-1].isdigit():
            category += '_'

    # Create the logger
    category_logger = logging.getLogger(category)
    category_logger.propagate = False
    category_logger.setLevel(logging.INFO)
    filepath = BASE_DIR + os.sep + category + '.log'
    han = logging.handlers.RotatingFileHandler(filepath,
        maxBytes=STAT_LOGS_MAX_SIZE,
        backupCount=STAT_LOGS_BACKUP_COUNT
    )
    formatter = logging.Formatter('%(message)s')
    han.setFormatter(formatter)
    category_logger.addHandler(han)

    # Log the message
    category_logger.info(msg)


def write_category_log(message_list, topic, category):
    """Note: categories are: system_stats, user_op, user_login, accounting_stats, b2safe_op"""

    # Create directory:
    dir_name = os.path.join(BASE_DIR, topic)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

    # Format message
    msg = ' '.join(message_list)

    # Remove newlines:
    # TODO TEST!
    if '\n' in msg:
      msg = msg.replace('\n', ' ')

    # Write to log
    make_category_logger_and_write(msg, args.category, dir_name)

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

    parser = argparse.ArgumentParser(description='EUDAT B2SAFE info distributor. '+
        'This client can send messages to RabbitMQ or write to specific text files '+
        'for being picked up by Filebeat.')

    parser.add_argument("-l", "--log", help="Path to the log file (debug logs of this script)")
    parser.add_argument("-d", "--debug", help="Set log level to debug",
                        action="store_true")
    parser.add_argument("-r", "--rabbit", help="Send message to RabbitMQ, too",
                        action="store_true")
    parser.add_argument("-nf", "--not_to_file", help="Do not write messages to text files",
                        action="store_true")
    parser.add_argument("topic", help='the message topic (used as exchange name when sending to RabbitMQ, and dir name when writing to file)')
    parser.add_argument("category", help='the message category (used as routing key in RabbitMQ, as file name when writing to file)')
    parser.add_argument("message", nargs='+', help='the message content')


    _args = parser.parse_args()
    _initializeLogger(_args)

    # Args override defaults:
    if _args.rabbit:
        SEND_TO_RABBIT = True

    if _args.not_to_file:
        WRITE_TO_CATEGORY_LOG = False

    # Try to import pika    
    if SEND_TO_RABBIT:
        try:
            import pika
        except ImportError as e:
            logger.error('Could not import pika. Will not send logs to RabbitMQ. Will write logs to file.')
            SEND_TO_RABBIT = False
            WRITE_TO_CATEGORY_LOG = True

    # Send log msg to RabbitMQ
    if SEND_TO_RABBIT:
        pub_message_to_rabbit(_args.message, _args.topic, _args.category)

    # Send log msg to file
    if WRITE_TO_CATEGORY_LOG:
        write_category_log(_args.message, _args.topic, _args.category)
