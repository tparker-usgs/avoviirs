from avoviirsprocessor.processor import Processor


class IR108Processor(Processor):
    def isFamiliar(self, topic):
        if topic.endswith("/ir108"):
            return True
        else:
            return False
