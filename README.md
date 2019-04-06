avoviirsprocessor
============
[![Build Status](https://travis-ci.org/tparker-usgs/avoviirsprocessor.svg?branch=master)](https://travis-ci.org/tparker-usgs/avoviirsprocessor)
[![Code Climate](https://codeclimate.com/github/tparker-usgs/avoviirsprocessor/badges/gpa.svg)](https://codeclimate.com/github/tparker-usgs/avoviirsprocessor)

Docker container to process VIIRS data at AVO

Data directory
--------------
I expect to find a writable directory to work in to be mounted at /rsdata

Environment variables
---------------------
I look to the environment for my bootstrap config. I require three enironrment variables.
  * _RSPROCESSING_BASE_ local filesystem path of my working directory
  * _CU_CONFIG_URL_ URL to a configupdater configuration file.
  * _AVOVIIRS_CONFIG_ Local filesystem path of the configuration file.

If authentication is required to retrieve the configupdater configuration it must be specified in the environment.
  * _CU_USER_ Username, if required to retrieve configupdater config file.
  * _CU_PASSWORD_ Password, if required to retrieve configupdater config file.

I will email logged errors if desired.
  * _CU_CONTEXT_NAME_ Displayed in the subject of any email generated by configupdater.
  * _MAILHOST_ Who can forward mail for me?
  * _LOG_SENDER_ From: address
  * _LOG_RECIPIENT_ To: address

Optionally, I'll cleanup downloaded files after some number of days.
  * _DAYS_RETENTION_ Maximum file retention in $RSPROCESSING_BASE

docker-compose
--------------
Here is an example service stanza for use with docker-compose.

    collectors:
      image: "tparkerusgs/rscollectors:release-2.0.2"
      user: "2001"
      environment:
        - RSPROCESSING_BASE=/rsdata
        - MIRROR_GINA_CONFIG=/tmp/mirrorGina.yaml
        - DAYS_RETENTION=7 
        - PYTHONUNBUFFERED=1
        - MAILHOST=smtp.usgs.gov
        - LOG_SENDER=avoauto@usgs.gov
        - LOG_RECIPIENT=tparker@usgs.gov
        - CU_CONFIG_URL=https://avomon01.wr.usgs.gov/svn/docker/rsprocessing/configupdater-collectors.yaml
        - CU_CONTEXT_NAME=collectors
        - CU_USER=user
        - CU_PASSWORD=password
      restart: always
      logging:
        driver: json-file
        options:
          max-size: 10m
      volumes:
        - type: volume
          source: rsdata
          target: /rsdata
          volume:
            nocopy: true

mirror_gina Configuration
-------------
I use a single YAML configuration file, an annotated example is [provided](https://raw.githubusercontent.com/tparker-usgs/rscollectors/master/support/mirrorGina.yaml).
