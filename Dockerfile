FROM tparkerusgs/avopytroll:release-1.7.0

WORKDIR /app
WORKDIR avoviirsprocessor
COPY Cousine-Bold.ttf .
COPY trollconfig trollconfig

COPY setup.py .
COPY setup.cfg .
COPY avoviirsprocessor avoviirsprocessor
RUN python setup.py install

RUN pip freeze > requirements.txt

ENV PPP_CONFIG_DIR=/app/avoviirsprocessor/trollconfig \
    GSHHS_DATA_ROOT=/app/gshhg

CMD ["watcher"]
