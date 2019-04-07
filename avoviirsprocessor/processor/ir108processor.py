from avoviirsprocessor.processor import AbstractProcessor


class IR108Processor(AbstractProcessor):
    def isFamiliar(self, topic):
        if topic.endswith("/ir108"):
            return True
        else:
            return False
