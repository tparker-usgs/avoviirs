from avoviirsprocessor.processor import Processor


class Ir108Processor(Processor):
    def isFamiliar(self, topic):
        if topic.endswith("/ir108"):
            return True
        else:
            return False
