FROM tparkerusgs/avopytroll:release-1.8.5

WORKDIR /app
COPY trollconfig/* trollconfig/

WORKDIR avoviirsprocessor
COPY Cousine-Bold.ttf .

COPY setup.py .
COPY setup.cfg .
COPY avoviirsprocessor avoviirsprocessor
RUN python setup.py install

RUN pip freeze > requirements.txt

CMD ["watcher"]
