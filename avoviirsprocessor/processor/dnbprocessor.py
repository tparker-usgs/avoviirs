from avoviirsprocessor.processor import Processor


class DNBProcessor(Processor):
    def isFamiliar(self, topic):
        if topic.endswith("/dnb"):
            return True
        else:
            return False
