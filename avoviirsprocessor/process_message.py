import argparse
from pathlib import Path
from posttroll.message import Message
from avoviirsprocessor.processor import publish_products
from avoviirsprocessor.coreprocessors import *  # NOQA
from . import HEARTBEAT_FILE


def _arg_parse():
    description = "Reprocesses a serialized message in a file."
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("message", help="path to serialized message", nargs="*")

    return parser.parse_args()


def get_key(message):
    return "{}-{}-{}".format(
        message.subject, message.data["platform_name"], message.data["start_time"]
    )


def get_messages(file_list):
    messages = {}
    for message_file in file_list:
        print("reading {}".format(message_file))
        with open(message_file, "r") as file:
            message = Message.decode(file.read())
        messages[get_key(message)] = message
    return messages


def main():
    args = _arg_parse()
    for (key, message) in get_messages(args.message):
        print(key)
        publish_products(message)
        Path(HEARTBEAT_FILE).touch()


if __name__ == "__main__":
    main()
