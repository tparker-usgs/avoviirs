from avoviirsprocessor.processor.abstractprocessor import AbstractProcessor


class DNBProcessor(AbstractProcessor):
    def is_familiar(topic):
        if topic.endswith("/dnb"):
            return True
        else:
            return False
