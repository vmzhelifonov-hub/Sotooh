#!/bin/sh
QID=ccabf9fd-5f60-4bb4-a0ec-f3863576b346
CSRF=$(grep csrftoken /tmp/c2.txt | awk '{print $7}')
curl -s -b /tmp/c2.txt -X POST http://127.0.0.1:8000/api/v1/quotes/$QID/pdf/ -H "X-CSRFToken: $CSRF" -o /dev/null -w "cold: %{time_total}s\n"
curl -s -b /tmp/c2.txt -X POST http://127.0.0.1:8000/api/v1/quotes/$QID/pdf/ -H "X-CSRFToken: $CSRF" -o /dev/null -w "warm: %{time_total}s\n"