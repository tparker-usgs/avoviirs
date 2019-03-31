#!/bin/sh

VERSION=`python -c "import avoviirs; print(avoviirs.__version__)"`
echo Tagging release $VERSION
git add avoviirs/__init__.py
git commit -m 'version bump'
git push \
&& git tag $VERSION \
&& git push --tags
