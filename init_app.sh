#!/usr/bin/env bash

# just stop/start application
WD="/Users/mlo/PycharmProjects/ping-mon"

source $WD/venv/bin/activate

case "$1" in
  start)
    cd $WD
    source "${WD}/venv/bin/activate"
    #python -m Flask app
    FLASK_APP=app.py nohup flask run &
    ;;
  stop)
    ps -ef|grep -i python|grep  -i flask
    ps -ef|grep -i python|grep  -i flask|perl -ane 'kill 15,$F[1] '
    ps -ef|grep -i python|grep  -i flask
    ;;
  *)
    echo "$0 <start|stop>"
    ;;
esac

