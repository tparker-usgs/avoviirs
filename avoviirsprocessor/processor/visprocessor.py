from avoviirsprocessor.processor.abstractprocessor import AbstractProcessor


class VisProcessor(AbstractProcessor):
    def is_familiar(topic):
        if topic.endswith("/vis"):
            return True
        else:
            return False
