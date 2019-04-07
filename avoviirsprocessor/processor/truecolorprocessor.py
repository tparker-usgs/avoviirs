from avoviirsprocessor.processor import Processor


class TrueColorProcessor(Processor):
    def isFamiliar(self, topic):
        if topic.endswith("/truecolor"):
            return True
        else:
            return False
