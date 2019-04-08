from avoviirsprocessor.processor.abstractprocessor import AbstractProcessor


class IR108HRProcessor(AbstractProcessor):
    def is_familiar(topic):
        if topic.endswith("/ir108hr"):
            return True
        else:
            return False
