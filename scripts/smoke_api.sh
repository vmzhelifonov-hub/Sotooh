#!/bin/sh
# Quick API smoke test inside the backend container
set -e
BASE=http://127.0.0.1:8000/api/v1
JAR=/tmp/cookies.txt

echo "== login =="
curl -s -c $JAR -X POST $BASE/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@sotooh.local","password":"Demo12345!"}' | head -c 300
echo

echo "== me =="
curl -s -b $JAR $BASE/me/ | head -c 300
echo

echo "== dashboard =="
curl -s -b $JAR http://127.0.0.1:8000/api/v1/dashboard/ | head -c 400
echo

echo "== products =="
curl -s -b $JAR "$BASE/products/?page_size=2" | head -c 300
echo

echo "== customers followup queue =="
curl -s -b $JAR $BASE/customers/followup_queue/ | head -c 200
echo

echo "== quotes list =="
curl -s -b $JAR "$BASE/quotes/" | head -c 300
echo
