FROM tparkerusgs/avopytroll:release-1.4.0

WORKDIR /app
WORKDIR /app/avoviirsprocessor
COPY setup.py .
COPY setup.cfg .
COPY avoviirsprocessor avoviirsprocessor
RUN python setup.py install

CMD ["watcher"]
