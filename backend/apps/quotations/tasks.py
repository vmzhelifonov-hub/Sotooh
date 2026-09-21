"""Celery tasks for quotations (PDF generation etc.)."""

from celery import shared_task
from django.core.mail import EmailMessage

from . import services
from .models import Quote


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def generate_quote_pdf_task(self, quote_id: str):
    """Background PDF generation — used when PDF work moves off the request path."""
    try:
        quote = Quote.objects.get(pk=quote_id)
    except Quote.DoesNotExist:
        return
    try:
        services.generate_and_store_pdf(quote)
    except services.PDFGenerationError as exc:
        raise self.retry(exc=exc)


@shared_task
def send_quote_pdf_email_task(quote_id: str, recipient: str, message: str = ""):
    """Email the quote PDF to a customer. Fails silently at MVP if SMTP not configured."""
    try:
        quote = Quote.objects.get(pk=quote_id)
    except Quote.DoesNotExist:
        return
    try:
        pdf_bytes = services.render_quote_pdf(quote)
        email = EmailMessage(
            subject=f"Sotooh — Quote {quote.quote_number}",
            body=message or "Please find your quotation attached.",
            to=[recipient],
        )
        email.attach(f"{quote.quote_number}.pdf", pdf_bytes, "application/pdf")
        email.send(fail_silently=True)
    except Exception:  # noqa: BLE001 — email must never crash the worker
        pass
