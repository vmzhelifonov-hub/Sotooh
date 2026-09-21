"""ClickHouse client — analytics must NEVER break the request flow."""

import logging
import uuid
from datetime import datetime, timezone as dt_timezone

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

EVENTS_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS {db}.events (
    event_id UUID,
    timestamp DateTime64(3, 'UTC'),
    event_name String,
    organization_id String,
    user_id String,
    session_id String,
    entity_type String,
    entity_id String,
    properties String
) ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (event_name, organization_id, timestamp)
TTL toDateTime(timestamp) + INTERVAL 24 MONTH
"""


def _conf() -> dict:
    return {
        "url": settings.CLICKHOUSE_URL.rstrip("/"),
        "auth": (settings.CLICKHOUSE_USER, settings.CLICKHOUSE_PASSWORD),
        "db": settings.CLICKHOUSE_DB,
    }


def is_enabled() -> bool:
    return bool(settings.CLICKHOUSE_URL)


def ping() -> bool:
    if not is_enabled():
        return False
    try:
        conf = _conf()
        r = requests.get(f"{conf['url']}/ping", auth=conf["auth"], timeout=2)
        return r.status_code == 200 and b"Ok" in r.content
    except requests.RequestException:
        return False


def ensure_schema() -> None:
    """Create the events table if ClickHouse is reachable; log-only on failure."""
    if not is_enabled():
        return
    conf = _conf()
    try:
        r = requests.post(
            f"{conf['url']}/",
            params={"query": f"CREATE DATABASE IF NOT EXISTS {conf['db']}"},
            auth=conf["auth"],
            timeout=5,
        )
        r.raise_for_status()
        r = requests.post(
            f"{conf['url']}/",
            params={"query": EVENTS_TABLE_DDL.format(db=conf["db"])},
            auth=conf["auth"],
            timeout=5,
        )
        r.raise_for_status()
        logger.info("clickhouse schema ensured")
    except requests.RequestException as exc:
        logger.warning("clickhouse schema setup failed: %s", exc)


def insert_event(
    event_name: str,
    organization_id: str = "",
    user_id: str = "",
    session_id: str = "",
    entity_type: str = "",
    entity_id: str = "",
    properties: dict | None = None,
) -> bool:
    """Fire-and-forget event insert. Returns success bool; never raises."""
    if not is_enabled():
        return False
    conf = _conf()
    row = {
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.now(dt_timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f"),
        "event_name": event_name,
        "organization_id": str(organization_id or ""),
        "user_id": str(user_id or ""),
        "session_id": str(session_id or ""),
        "entity_type": str(entity_type or ""),
        "entity_id": str(entity_id or ""),
        "properties": json_dumps(properties or {}),
    }
    query = (
        f"INSERT INTO {conf['db']}.events "
        f"(event_id, timestamp, event_name, organization_id, user_id, session_id, entity_type, entity_id, properties) "
        f"VALUES"
    )
    try:
        payload = _format_row(row)
        r = requests.post(
            f"{conf['url']}/",
            params={"query": query, "input_format": "JSONEachRow"},
            data=payload,
            auth=conf["auth"],
            timeout=2,
        )
        return r.status_code in (200, 204)
    except requests.RequestException as exc:
        logger.warning("clickhouse insert failed: %s", exc)
        return False


def _format_row(row: dict) -> str:
    import json

    return json.dumps(row, ensure_ascii=False)


def json_dumps(d: dict) -> str:
    import json

    return json.dumps(d, ensure_ascii=False)


def query(sql: str) -> list[dict] | None:
    """Run a read-only analytics query; returns rows as dicts or None when CH is down."""
    if not is_enabled():
        return None
    conf = _conf()
    try:
        r = requests.post(
            f"{conf['url']}/",
            params={"query": f"{sql} FORMAT JSONEachRow"},
            auth=conf["auth"],
            timeout=10,
        )
        r.raise_for_status()
        import json

        return [json.loads(line) for line in r.text.splitlines() if line.strip()]
    except (requests.RequestException, json.JSONDecodeError) as exc:
        logger.warning("clickhouse query failed: %s", exc)
        return None
