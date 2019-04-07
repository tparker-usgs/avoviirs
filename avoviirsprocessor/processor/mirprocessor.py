from avoviirsprocessor.processor import Processor


class MIRProcessor(Processor):
    def isFamiliar(self, topic):
        if topic.endswith("/mir"):
            return True
        else:
            return False
