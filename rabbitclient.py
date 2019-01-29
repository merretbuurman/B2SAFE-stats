#!/usr/bin/env python

import pika
import sys
import logging
import logging.handlers
import argparse

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
    _args.func(_args)

