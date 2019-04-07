from avoviirsprocessor.processor.abstractprocessor import AbstractProcessor


class TrueColorProcessor(AbstractProcessor):
    def isFamiliar(self, topic):
        if topic.endswith("/truecolor"):
            return True
        else:
            return False
