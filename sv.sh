#!/bin/bash
# helper: manage the local static+mock server without self-matching pgrep patterns
cd /root/simdrive-3d || exit 1
PIDFILE=/tmp/sd_serve.pid
case "$1" in
  start)
    if [ -f "$PIDFILE" ] && kill -0 "$(cat $PIDFILE)" 2>/dev/null; then echo "already running $(cat $PIDFILE)"; exit 0; fi
    setsid nohup python3 s$(echo)erve.py > /tmp/sd_serve.log 2>&1 &
    echo $! > "$PIDFILE"
    sleep 1.5
    echo "started $(cat $PIDFILE)"; cat /tmp/sd_serve.log
    ;;
  stop)
    if [ -f "$PIDFILE" ]; then kill "$(cat $PIDFILE)" 2>/dev/null; rm -f "$PIDFILE"; echo stopped; else echo "no pidfile"; fi
    ;;
  status)
    if [ -f "$PIDFILE" ] && kill -0 "$(cat $PIDFILE)" 2>/dev/null; then echo "up $(cat $PIDFILE)"; else echo down; fi
    ;;
esac
