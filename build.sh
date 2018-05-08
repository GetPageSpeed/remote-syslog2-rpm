#!/bin/bash

rm -rf *.rpm

spectool -g remote_syslog2.spec
mock -r epel-7-x86_64 --spec=remote_syslog2.spec --sources=. --resultdir=. --buildsrpm

mock -r epel-7-x86_64 --rebuild --resultdir=. *.src.rpm
mock -r epel-6-x86_64 --rebuild --resultdir=. *.src.rpm

~/rpm-sign.exp *.rpm
