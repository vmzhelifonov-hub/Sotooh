#!/bin/sh
BASE=http://127.0.0.1:8000/api/v1
JAR=/tmp/c3.txt
rm -f $JAR
cat > /tmp/l.json <<'EOF'
{"email":"demo@sotooh.local","password":"Demo12345!"}
EOF
curl -s -c $JAR -X POST $BASE/auth/login/ -H "Content-Type: application/json" --data @/tmp/l.json > /dev/null
QID=$(curl -s -b $JAR "$BASE/quotes/?page_size=1" | python3 -c "import sys,json; print(json.load(sys.stdin)['results'][0]['id'])")
echo "quote: $QID"
CSRF=$(grep csrftoken $JAR | awk '{print $7}')
curl -s -b $JAR -X POST $BASE/quotes/$QID/pdf/ -H "X-CSRFToken: $CSRF" -o /dev/null -w "cold: %{time_total}s\n"
curl -s -b $JAR -X POST $BASE/quotes/$QID/pdf/ -H "X-CSRFToken: $CSRF" -o /dev/null -w "warm: %{time_total}s\n"