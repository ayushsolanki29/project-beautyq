#!/usr/bin/env bash
cd "$(dirname "$0")"

PORT=8000
for p in $(seq 8000 8010); do
  if ! ss -tln 2>/dev/null | grep -q ":$p " && ! netstat -tln 2>/dev/null | grep -q ":$p "; then
    PORT=$p
    break
  fi
  echo "Port $p busy, trying next..."
  PORT=$((p + 1))
done

if [ ! -d "venv" ]; then
  echo "Run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

source venv/bin/activate
echo "BeautyQ: http://127.0.0.1:$PORT/"
xdg-open "http://127.0.0.1:$PORT/" 2>/dev/null &
./venv/bin/python manage.py runserver "127.0.0.1:$PORT"
