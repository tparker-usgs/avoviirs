from avoviirsprocessor.processor import Processor


class BTDProcessor(Processor):
    def isFamiliar(self, topic):
        if topic.endswith("/btd"):
            return True
        else:
            return False
