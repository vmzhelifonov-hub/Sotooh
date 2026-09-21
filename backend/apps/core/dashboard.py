"""Dashboard: aggregate metrics for the authenticated organization."""

from django.db.models import Avg, Sum
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.crm.models import Customer, Stage
from apps.quotations.models import Quote, QuoteStatus


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard(request):
    org = request.user.organization
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    quotes = Quote.objects.filter(organization=org)
    quotes_month = quotes.filter(created_at__gte=month_start)

    leads_month = Customer.objects.filter(organization=org, created_at__gte=month_start).count()
    quotes_month_count = quotes_month.count()
    quote_value_month = quotes_month.aggregate(v=Sum("total"))["v"] or 0
    won_quotes = quotes.filter(status=QuoteStatus.WON)
    won_value = won_quotes.aggregate(v=Sum("total"))["v"] or 0
    won_count = won_quotes.count()
    sent_count = quotes.filter(
        status__in=[
            QuoteStatus.SENT,
            QuoteStatus.ACCEPTED,
            QuoteStatus.WON,
            QuoteStatus.LOST,
        ]
    ).count()
    conversion = round(100.0 * won_count / sent_count, 1) if sent_count else 0.0
    avg_quote = quotes.aggregate(a=Avg("total"))["a"] or 0

    # Follow-up attention queue
    attention = (
        Customer.objects.filter(
            organization=org,
            next_follow_up__isnull=False,
            next_follow_up__lte=now.replace(hour=23, minute=59, second=59),
        )
        .exclude(stage__in=[Stage.WON, Stage.LOST])
        .order_by("next_follow_up")[:10]
    )

    recent_quotes = quotes.select_related("customer").order_by("-created_at")[:8]

    return Response(
        {
            "leads_this_month": leads_month,
            "quotes_this_month": quotes_month_count,
            "quote_value_this_month": str(quote_value_month),
            "won_value": str(won_value),
            "won_deals": won_count,
            "conversion_rate": conversion,
            "average_quote_value": str(round(avg_quote, 2)),
            "overdue_follow_ups": Customer.objects.filter(organization=org, next_follow_up__lt=now)
            .exclude(stage__in=[Stage.WON, Stage.LOST])
            .count(),
            "funnel": {
                "new": Customer.objects.filter(organization=org, stage=Stage.NEW).count(),
                "quote_sent": Customer.objects.filter(
                    organization=org, stage__in=[Stage.QUOTE_SENT, Stage.FOLLOW_UP]
                ).count(),
                "won": Customer.objects.filter(organization=org, stage=Stage.WON).count(),
            },
            "needs_attention": [
                {
                    "id": str(c.id),
                    "name": c.name,
                    "phone": c.phone,
                    "next_follow_up": c.next_follow_up.isoformat(),
                }
                for c in attention
            ],
            "recent_quotes": [
                {
                    "id": str(q.id),
                    "quote_number": q.quote_number,
                    "customer_name": q.customer.name,
                    "status": q.status,
                    "total": str(q.total),
                    "currency": q.currency,
                    "created_at": q.created_at.isoformat(),
                }
                for q in recent_quotes
            ],
        }
    )
