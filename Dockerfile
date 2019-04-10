FROM tparkerusgs/avopytroll:release-1.5.0

WORKDIR /app
WORKDIR avoviirsprocessor
COPY Cousine-Bold.ttf .
COPY trollconfig trollconfig

COPY setup.py .
COPY setup.cfg .
COPY avoviirsprocessor avoviirsprocessor
RUN python setup.py install

RUN pip freeze > requirements.txt
CMD ["watcher"]
