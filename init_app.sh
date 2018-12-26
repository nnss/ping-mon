#!/usr/bin/env bash

# just stop/start application
WD="/Users/mlo/PycharmProjects/ping-mon"

source $WD/venv/bin/activate

case "$1" in
  start)
    cd $WD
    python -m Flask app
    ;;
  stop)
    PID=$((ps -ef|grep -i Flask|grep -i python|grep app|perl -ane 'print $F[1]'))
    for p in PIDS; do
        kill -15 $p
    done
    ;;
  *)
    echo $0 <start|stop>
    ;;
esac

