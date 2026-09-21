"""Product analytics tracking service.

The SaaS must never fail because of analytics: all tracking is fire-and-forget,
wrapped in try/except at the call sites' service boundary.
"""

import logging

from . import clickhouse

logger = logging.getLogger(__name__)


def track_event(
    event_name: str,
    organization_id=None,
    user_id=None,
    session_id: str = "",
    entity_type: str = "",
    entity_id=None,
    properties: dict | None = None,
    request=None,
) -> None:
    """Record a product event. Analytics failures are logged, never raised."""
    try:
        clickhouse.insert_event(
            event_name=event_name,
            organization_id=str(organization_id or ""),
            user_id=str(user_id or ""),
            session_id=session_id,
            entity_type=entity_type,
            entity_id=str(entity_id or ""),
            properties=properties or {},
        )
    except Exception:  # noqa: BLE001 — analytics must never break requests
        logger.exception("track_event failed for %s", event_name)


def org_metrics_summary() -> dict:
    """Admin-facing product metrics from ClickHouse (or empty when CH is down)."""
    rows = clickhouse.query(
        "SELECT event_name, count() AS cnt FROM sotooh.events GROUP BY event_name ORDER BY cnt DESC"
    )
    if rows is None:
        return {"available": False, "events": []}
    return {"available": True, "events": rows}


def funnel(organization_id: str) -> dict:
    """Simple funnel: customer_created → quote_created → quote_won per org."""
    rows = clickhouse.query(
        "SELECT event_name, count(DISTINCT entity_id) AS cnt FROM sotooh.events "
        f"WHERE organization_id = '{organization_id}' "
        "AND event_name IN ('customer_created', 'quote_created', 'quote_won') "
        "GROUP BY event_name"
    )
    if rows is None:
        return {"available": False}
    out = {r["event_name"]: int(r["cnt"]) for r in rows}
    return {"available": True, **out}
