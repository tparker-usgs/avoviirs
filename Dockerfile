FROM tparkerusgs/avopytroll:release-1.4.0

WORKDIR /app
WORKDIR /app/avoviirsprocessor
COPY Cousine-Bold.ttf .
COPY setup.py .
COPY setup.cfg .
COPY trollconfig trollconfig
COPY avoviirsprocessor avoviirsprocessor
RUN python setup.py install && rm -r avoviirsprocessor

CMD ["watcher"]
