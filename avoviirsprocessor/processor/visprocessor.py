from avoviirsprocessor.processor import Processor


class VisProcessor(Processor):
    def isFamiliar(self, topic):
        if topic.endswith("/vis"):
            return True
        else:
            return False
