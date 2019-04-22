FROM tparkerusgs/avopytroll:release-1.8.6

WORKDIR /app
COPY trollconfig/* trollconfig/

WORKDIR avoviirsprocessor
COPY Cousine-Bold.ttf .

COPY setup.py .
COPY setup.cfg .
COPY avoviirsprocessor avoviirsprocessor
RUN python setup.py install

RUN pip freeze > requirements.txt
ENV TLES=/viirs/elements/noaa.txt
CMD ["watcher"]
