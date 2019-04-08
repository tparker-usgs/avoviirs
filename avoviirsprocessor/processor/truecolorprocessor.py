from avoviirsprocessor.processor.abstractprocessor import AbstractProcessor


class TrueColorProcessor(AbstractProcessor):
    def is_familiar(topic):
        if topic.endswith("/truecolor"):
            return True
        else:
            return False
