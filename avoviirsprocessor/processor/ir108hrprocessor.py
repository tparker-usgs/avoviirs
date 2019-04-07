from avoviirsprocessor.processor import Processor


class IR108HRProcessor(Processor):
    def isFamiliar(self, topic):
        if topic.endswith("/ir108hr"):
            return True
        else:
            return False
