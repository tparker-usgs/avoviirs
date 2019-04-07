from avoviirsprocessor.processor import AbstractProcessor


class DNBProcessor(AbstractProcessor):
    def isFamiliar(self, topic):
        if topic.endswith("/dnb"):
            return True
        else:
            return False
