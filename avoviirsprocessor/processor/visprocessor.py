from avoviirsprocessor.processor.abstractprocessor import AbstractProcessor


class VisProcessor(AbstractProcessor):
    def isFamiliar(self, topic):
        if topic.endswith("/vis"):
            return True
        else:
            return False
