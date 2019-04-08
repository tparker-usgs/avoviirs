from avoviirsprocessor.processor.abstractprocessor import AbstractProcessor


class BTDProcessor(AbstractProcessor):
    def is_familiar(topic):
        if topic.endswith("/btd"):
            return True
        else:
            return False
