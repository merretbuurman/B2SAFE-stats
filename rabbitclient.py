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
STAT_LOGS_MAX_SIZE=6000000
STAT_LOGS_BACKUP_COUNT=9

# RabbitMQ settings
RABBIT_USER = 'foobar'
RABBIT_PASSWORD = 'foobar'
RABBIT_HOST = 'sdc-b2host-test.dkrz.de'
RABBIT_VHOST = 'b2safe_log_test'
RABBIT_PORT = 5672
RABBIT_SSL_ENABLED = False 

# This is the logger for the script
logger = logging.getLogger('stat_info_distributor')

# This script's logs are written to /var/lib/irods/log/stat_info_distributor.log
root = logging.getLogger()
root.setLevel(logging.DEBUG)
#handler = logging.StreamHandler(sys.stdout)
filepath = BASE_DIR + os.sep + 'stat_info_distributor.log'
handler = logging.handlers.RotatingFileHandler(filename,
    maxBytes=STAT_LOGS_MAX_SIZE,
    backupCount=STAT_LOGS_BACKUP_COUNT
)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)


def pub_message_to_rabbit(message_list, topic, category):

    msg = ' '.join(message_list)
    logger.info(('Publishing the message "{}" to the exchange (topic) "{}"'
                + ' with the routing key (category): "{}"').format(msg, 
                                                             topic,
                                                             category))

    credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASSWORD)
    params = pika.ConnectionParameters(
        host = RABBIT_HOST,
        virtual_host = RABBIT_VHOST,
        port = RABBIT_PORT, 
        credentials = credentials,
        ssl = RABBIT_SSL_ENABLED
    )

    try:
        logger.debug('Connecting to RabbitMQ at %s:%s/%s (user %s)...', RABBIT_HOST, RABBIT_VHOST, RABBIT_PORT, RABBIT_USER)
        connection = pika.BlockingConnection(params)
        logger.debug('Connecting to RabbitMQ... done.')
        logger.debug('Creating channel...')
        channel = connection.channel()
        logger.debug('Creating channel... done.')
        logger.debug('Publishing message (exchange %s, routing key %s)...', topic, category)
        props = pika.BasicProperties(
            delivery_mode = 2 # persistent! otherwise, they may be dropped if RabbitMQ crashes
        )
        channel.basic_publish(
            properties=props,
            exchange=topic,
            routing_key=category,
            body=msg
            #mandatory=True # otherwise server will drop the message if it cannot route it! May raise some Unroutable error. Does not work well with BlockingConnections, rather in asynchronous mode.
        )
        logger.debug('Publishing message... done.')
        logger.debug('Closing connection...')
        connection.close()
        logger.debug('Closing connection... done')
        return True

    except pika.exceptions.ConnectionClosed as e1:
        logger.info('Caught exception (connection closed):')
        logger.error(e1)
    except socket.gaierror as e2:
        logger.info('Caught socket error (maybe typo in host "%s"?):', RABBIT_HOST)
        logger.error(e2)
    except pika.exceptions.ProbableAuthenticationError as e3:
        logger.info('Caught exception (wrong username and password?):')
        logger.error(e3)
    except pika.exceptions.AMQPConnectionError as e4:
        logger.info('Caught exception:')
        logger.error(e4)
    return False


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

    # Create the logger
    logger.debug('Create logger for category %s', category)
    category_logger = logging.getLogger(category)
    category_logger.propagate = False
    category_logger.setLevel(logging.INFO)
    filepath = base_dir + os.sep + category + '.log'
    han = logging.handlers.RotatingFileHandler(filepath,
        maxBytes=STAT_LOGS_MAX_SIZE,
        backupCount=STAT_LOGS_BACKUP_COUNT
    )
    formatter = logging.Formatter('%(message)s')
    han.setFormatter(formatter)
    category_logger.addHandler(han)

    # Log the message
    logger.debug('Writing message %s', msg)
    category_logger.info(msg)


def write_category_log(message_list, topic, category, base_dir):
    """Note: categories are: system_stats, user_op, user_login, accounting_stats, b2safe_op"""

    # Create directory:
    dir_name = os.path.join(base_dir, topic)
    if not os.path.exists(dir_name):
        try:
            logger.info('Creating directory %s', dir_name)
            os.makedirs(dir_name)
        except OSError as e:
            logger.error(e)
            raise e

    # Format message
    msg = ' '.join(message_list)

    # Remove newlines:
    # TODO TEST!
    if '\n' in msg:
      msg = msg.replace('\n', ' ')

    # Write to log
    make_category_logger_and_write(msg, category, dir_name)

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

    if (args.output):
        han = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s %(levelname)s:%(message)s')
        han.setFormatter(formatter)
        logger.addHandler(han)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description=('EUDAT B2SAFE info distributor. '+
        'This client can send messages to RabbitMQ and/or write to specific text files '+
        'for being picked up by Filebeat. The latter is the default.\n'+
        'The text files are by default added into a subdirectory of base_dir.'+
        'If RabbitMQ should be used, connection details have to be '+
        'hard-coded into this script. '))

    parser.add_argument("-l", "--log", help="Path to the log file (debug logs of this script)")
    parser.add_argument("-o", "--output", help="Write log messages to stdout",
                        action="store_true")
    parser.add_argument("-d", "--debug", help="Set log level to debug",
                        action="store_true")
    parser.add_argument("-r", "--rabbit", help="Send message to RabbitMQ, too",
                        action="store_true")
    parser.add_argument("-nf", "--not_to_file", help="Do not write messages to text files",
                        action="store_true")
    parser.add_argument("-bd", "--base_dir", help=("Path to the directory where to write files (defaults to %s)" % BASE_DIR),
                        nargs='?', default=BASE_DIR)

    parser.add_argument("topic", help='Message topic (used as exchange name when sending to RabbitMQ, and dir name when writing to file)')
    parser.add_argument("category", help='Message category (used as routing key in RabbitMQ, as file name when writing to file)')
    parser.add_argument("message", nargs='+', help='Message content')


    _args = parser.parse_args()
    _args.base_dir = _args.base_dir.rstrip(os.sep)  
    _initializeLogger(_args)

    # Args override defaults:
    if _args.rabbit:
        logger.info('Caller asks to send to RabbitMQ.')
        SEND_TO_RABBIT = True

    if _args.not_to_file:
        logger.info('Caller asks not to write to text file.')
        WRITE_TO_CATEGORY_LOG = False

    # Try to import pika    
    if SEND_TO_RABBIT:
        import socket
        try:
            import pika
        except ImportError as e:
            logger.error('Could not import pika. Will not send logs to RabbitMQ. Will write logs to file.')
            SEND_TO_RABBIT = False
            WRITE_TO_CATEGORY_LOG = True

    # Send log msg to RabbitMQ
    rabbit_success = False
    if SEND_TO_RABBIT:
        logger.info('Will send to RabbitMQ.')
        rabbit_success = pub_message_to_rabbit(_args.message, _args.topic, _args.category)

    # Send log msg to file
    if WRITE_TO_CATEGORY_LOG or not rabbit_success:
        logger.info('Will send to text file.')
        write_category_log(_args.message, _args.topic, _args.category, _args.base_dir)
