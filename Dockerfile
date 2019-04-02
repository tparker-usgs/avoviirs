FROM tparkerusgs/avorsprocessor:release-1.2.0

WORKDIR /app
COPY trollconfig trollconfig
COPY supervisord.conf /etc/supervisor/supervisord.conf

CMD ["/usr/local/bin/supervisord"]
