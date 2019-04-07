from avoviirsprocessor.processor.abstractprocessor import AbstractProcessor


class MIRProcessor(AbstractProcessor):
    def isFamiliar(self, topic):
        if topic.endswith("/mir"):
            return True
        else:
            return False
