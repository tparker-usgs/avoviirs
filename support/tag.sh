#!/bin/sh

VERSION=`python -c "import avoviirsprocessor; print(avoviirsprocessor.__version__)"`
echo Tagging release $VERSION
git add avoviirsprocessor/__init__.py
git commit -m 'version bump'
git push \
&& git tag $VERSION \
&& git push --tags
