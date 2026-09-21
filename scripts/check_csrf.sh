#!/bin/sh
set -e
BASE=http://127.0.0.1:8000/api/v1
JAR=/tmp/cookies.txt
rm -f $JAR /tmp/login.json /tmp/org.json

echo "== login (check cookies) =="
cat > /tmp/login.json <<'EOF'
{"email":"demo@sotooh.local","password":"Demo12345!"}
EOF
curl -si -c $JAR -X POST $BASE/auth/login/ -H "Content-Type: application/json" --data @/tmp/login.json | grep -i "set-cookie" | head -4

echo "== CSRF cookie present? =="
grep -i csrf $JAR || echo "NO CSRF COOKIE"

echo "== PATCH organization WITH CSRF header =="
CSRF=$(grep csrftoken $JAR | awk '{print $7}')
cat > /tmp/org.json <<'EOF'
{"city": "Baghdad-Test"}
EOF
curl -s -b $JAR -X PATCH $BASE/organization/ -H "Content-Type: application/json" -H "X-CSRFToken: $CSRF" --data @/tmp/org.json | head -c 200
echo

echo "== PATCH organization WITHOUT CSRF header (must fail) =="
curl -s -b $JAR -X PATCH $BASE/organization/ -H "Content-Type: application/json" --data @/tmp/org.json | head -c 200
echo
