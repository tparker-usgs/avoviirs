from avoviirsprocessor.processor.abstractprocessor import AbstractProcessor


class IR108Processor(AbstractProcessor):
    def is_familiar(topic):
        if topic.endswith("/ir108"):
            return True
        else:
            return False
