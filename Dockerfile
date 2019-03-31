FROM python:3.7


RUN apt-get update && apt-get -y install libhdf5-serial-dev libnetcdf-dev less unzip libfreetype6 libfreetype6-dev vim supervisor
#python-numpy python-scipy python-matplotlib libhdf5-serial-dev libnetcdf-dev

RUN ln -s /usr/include/freetype2 /usr/include/freetype  

RUN wget http://download.osgeo.org/gdal/2.2.0/gdal-2.2.0.tar.gz \
    && (gzip -dc gdal-2.2.0.tar.gz | tar xf -) \
    && cd gdal-2.2.0 \
    && ./configure; make; make install \
    && ldconfig \
    && cd .. && rm -rf gdal-2.2.0 gdal-2.2.0.tar.gz

WORKDIR /src
WORKDIR /src/avoviirs
ADD requirements.txt /src/avoviirs/
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app/gshhg
RUN wget http://www.soest.hawaii.edu/pwessel/gshhg/gshhg-shp-2.3.6.zip \
    && unzip gshhg-shp-2.3.6.zip && rm gshhg-shp-2.3.6.zip

WORKDIR /usr/src/
ADD installAggdraw.sh .
RUN ./installAggdraw.sh

COPY supervisord.conf /etc/supervisor/supervisord.conf

CMD ["/usr/bin/supervisord"]
