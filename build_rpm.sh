#!/bin/sh
set -e
PACKAGE_NAME="gsni-authenticator"
version=$(grep "%define version" ${PACKAGE_NAME}.spec | cut -d" " -f3)
cp -a . /tmp/${PACKAGE_NAME}-$version
cd /tmp && tar cvf ${PACKAGE_NAME}-$version.tar.gz ${PACKAGE_NAME}-$version
mv ${PACKAGE_NAME}-$version.tar.gz $HOME/rpmbuild/SOURCES
cd -
rpmbuild -ba ${PACKAGE_NAME}.spec 
