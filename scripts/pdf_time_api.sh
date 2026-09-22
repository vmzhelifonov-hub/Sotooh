#!/bin/sh
# Measure live PDF endpoint time (warm server)
set -e
BASE=http://127.0.0.1:8000/api/v1
JAR=/tmp/c2.txt
rm -f $JAR
cat > /tmp/l.json <<'EOF'
{"email":"demo@sotooh.local","password":"Demo12345!"}
EOF
curl -s -c $JAR -X POST $BASE/auth/login/ -H "Content-Type: application/json" --data @/tmp/l.json > /dev/null
QID=$(curl -s -b $JAR "$BASE/quotes/" | grep -o '"id": "[a-f0-9-]*"' | head -1 | cut -d'"' -f4)
echo "quote: $QID"
CSRF=$(grep csrftoken $JAR | awk '{print $7}')
echo "--- 1st call (cold) ---"
curl -s -b $JAR -X POST $BASE/quotes/$QID/pdf/ -H "X-CSRFToken: $CSRF" -o /dev/null -w "time: %{time_total}s\n"
echo "--- 2nd call (warm) ---"
curl -s -b $JAR -X POST $BASE/quotes/$QID/pdf/ -H "X-CSRFToken: $CSRF" -o /dev/null -w "time: %{time_total}s\n"
