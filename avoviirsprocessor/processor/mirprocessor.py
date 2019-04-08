from avoviirsprocessor.processor.abstractprocessor import AbstractProcessor


class MIRProcessor(AbstractProcessor):
    def is_familiar(topic):
        if topic.endswith("/mir"):
            return True
        else:
            return False
