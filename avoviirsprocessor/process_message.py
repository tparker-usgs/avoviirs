import argparse
from posttroll.message import Message
from avoviirsprocessor.processor import publish_products


def _arg_parse():
    description = "Reprocesses a serialized message in a faile."
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("message", help="path to serialized message")

    return parser.parse_args()


def main():
    args = _arg_parse()
    with open(args.message, 'r') as file:
        message = Message.decode(file.read())

    publish_products(message)


if __name__ == '__main__':
    main()
