#!/bin/sh
# stop
nginx -s stop
killall -QUIT uwsgi

# git
# git pull
# python manage.py collectstatic

sleep 1

# start
uwsgi -x /home/dingqi/production_uwsgi.xml
nginx -c /home/dingqi/production_nginx.conf