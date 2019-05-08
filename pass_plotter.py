#!/usr/bin/env python


import argparse
from posttroll.message import Message
from avoviirsprocessor.processor import publish_products
from avoviirsprocessor.coreprocessors import * # NOQA
import threading
import zmq
import tomputils.util as tutil
from queue import Queue
from json.decoder import JSONDecodeError
import collections
from datetime import timedelta


DATA_PUBLISHER = "tcp://viirscollector:29092"
logger = tutil.setup_logging("pass_plotter errors")
ORBIT_SLACK = timedelta(minutes=30)


def _arg_parse():
    description = "Reprocesses a serialized message in a file."
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("message", help="path to serialized message")

    return parser.parse_args()


def queue_msg(msgs, new_msg):
    data = new_msg.data
    file_path = data['uri']
    key = "{}-{}-{}".format(data['platform_name'], data['orbit_number'],
                            data['segment'])
    with msgs_lock:
        if key not in msgs:
            logger.debug("Adding new key %s", key)
            msgs[key] = []

        new_data = new_msg.data
        for msg in msgs[key]:
            queued_data = msg.data
            time_diff = abs(queued_data['start_time'] - new_data['start_time'])
            if time_diff < ORBIT_SLACK:
                logger.debug("updating messge %s", key)
                queued_data['start_time'] = min(queued_data['start_time'],
                                                new_data['start_time'])
                queued_data['end_time'] = max(queued_data['end_time'],
                                              new_data['end_time'])
                new_msg = None
                break

        if new_msg:
            msgs[key].append(new_msg)


class DataSubscriber(threading.Thread):
    def __init__(self, context, msgs):
        threading.Thread.__init__(self)
        self.socket = context.socket(zmq.SUB)
        self.socket.setsockopt_string(zmq.SUBSCRIBE, 'pytroll://AVO/viirs/sdr')
        self.socket.connect(DATA_PUBLISHER)
        self.task_waiting = False
        self.msgs = msgs

    def run(self):
        while True:
            msg_bytes = self.socket.recv()
            message = Message.decode(msg_bytes)
            queue_msg(self.msgs, message)



def main():
    global msgs_lock
    msgs_lock = threading.Lock()

    message_q = collections.OrderedDict()
    context = zmq.Context()
    updater = DataSubscriber(context, message_q)
    updater.start()
    logger.info("updater started")

    while True:
        for message_list in message_q:




if __name__ == '__main__':
    main()
