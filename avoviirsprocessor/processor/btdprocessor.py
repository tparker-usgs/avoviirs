from avoviirsprocessor.processor.abstractprocessor import AbstractProcessor


class BTDProcessor(AbstractProcessor):
    def isFamiliar(self, topic):
        if topic.endswith("/btd"):
            return True
        else:
            return False
