from avoviirsprocessor.processor import AbstractProcessor


class IR108HRProcessor(AbstractProcessor):
    def isFamiliar(self, topic):
        if topic.endswith("/ir108hr"):
            return True
        else:
            return False
