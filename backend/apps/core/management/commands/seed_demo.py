"""Development seed command — demo org/user/products/customers/quotes.

Never runs automatically; never use in production.
"""
import random
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import Membership, Organization, User
from apps.billing.services import start_trial
from apps.catalog.models import Category, Product
from apps.crm.models import Customer, FollowUp, LeadSource, Stage
from apps.quotations.models import Quote, QuoteItem, QuoteStatus
from apps.quotations.services import generate_quote_number


class Command(BaseCommand):
    help = "Seed demo data for local development (dev only!)."

    def add_arguments(self, parser):
        parser.add_argument("--email", default="demo@sotooh.local")
        parser.add_argument("--password", default="Demo12345!")
        parser.add_argument("--force", action="store_true", help="Recreate even if the user exists")

    def handle(self, *args, **options):
        email = options["email"]
        if User.objects.filter(email=email).exists() and not options["force"]:
            self.stdout.write(self.style.WARNING(f"User {email} already exists — use --force to recreate."))
            return
        if User.objects.filter(email=email).exists():
            User.objects.filter(email=email).delete()

        user = User.objects.create_user(email=email, password=options["password"], first_name="Demo")
        user.username = email
        user.save(update_fields=["username"])

        org = Organization.objects.create(
            company_name="Baghdad Solar Energy",
            company_name_ar="شركة بغداد للطاقة الشمسية",
            phone="+9647701234567",
            email="info@baghdadsolar.iq",
            city="Baghdad",
            onboarding_completed=True,
        )
        Membership.objects.create(user=user, organization=org, role=Membership.ROLE_OWNER)
        user.organization = org
        User.objects.filter(pk=user.pk).update(organization=org)
        start_trial(org)

        products_data = [
            (Category.SOLAR_PANEL, "LONGi", "Hi-MO 6", "ألواح شمسية لونغي 550 واط", "LONGi 550W Panel", "550W", 25, 210000, 265000),
            (Category.INVERTER, "Huawei", "SUN2000-5KTL", "انفرتر هواوي 5 كيلوواط", "Huawei 5kW Inverter", "5kW", 60, 850000, 1100000),
            (Category.BATTERY, "Pylontech", "US5000", "بطارية بيلون تيك 4.8 كيلوواط ساعة", "Pylontech 4.8kWh Battery", "4.8kWh", 84, 950000, 1250000),
            (Category.MOUNTING, "Generic", "Rail-Set", "منظومة تثبيت ألواح", "Mounting Rail Set", "set", 120, 45000, 75000),
            (Category.CABLE, "Generic", "PV-Cable-6mm", "كابل شمسي 6 مم", "Solar Cable 6mm", "meter", 0, 1500, 2500),
            (Category.INSTALLATION, "", "", "تركيب وتشغيل المنظومة", "Installation & Commissioning", "job", 12, 0, 400000),
        ]
        products = []
        for cat, brand, model, name_ar, name_en, unit, warranty, cost, sell in products_data:
            p = Product.objects.create(
                organization=org, category=cat, brand=brand, model=model, sku=f"DEMO-{len(products):03d}",
                name_ar=name_ar, name_en=name_en, cost_price=cost, selling_price=sell,
                warranty_months=warranty, unit=unit, type=Product.Service if cat == Category.INSTALLATION else Product.Product,
            )
            products.append(p)

        customers_data = [
            ("أحمد الكرخي", "+9647701111111", "Baghdad", LeadSource.WHATSAPP, Stage.QUOTE_SENT),
            ("سارة عبد الرحمن", "+9647802222222", "Basra", LeadSource.FACEBOOK, Stage.FOLLOW_UP),
            ("مصطفى الجبوري", "+9647503333333", "Erbil", LeadSource.REFERRAL, Stage.WON),
            ("ليلى حسن", "+9647714444444", "Mosul", LeadSource.INSTAGRAM, Stage.NEW),
            ("عمر التكريتي", "+9647705555555", "Tikrit", LeadSource.WALKIN, Stage.CONTACTED),
        ]
        customers = []
        for name, phone, city, source, stage in customers_data:
            c = Customer.objects.create(
                organization=org, name=name, phone=phone, city=city, source=source, stage=stage,
                assigned_user=user,
                next_follow_up=timezone.now() + timezone.timedelta(days=random.choice([-2, 0, 1, 3])) if stage == Stage.FOLLOW_UP else None,
            )
            customers.append(c)

        for idx, customer in enumerate(customers[:3]):
            quote = Quote.objects.create(
                organization=org, customer=customer, created_by=user,
                quote_number=generate_quote_number(org),
                status=QuoteStatus.SENT if idx == 0 else QuoteStatus.DRAFT,
                valid_until=timezone.localdate() + timezone.timedelta(days=14),
                notes_ar="الأسعار تشمل التركيب والتوصيل داخل المدينة.",
                payment_terms="دفعة مقدمة 50%، والباقي عند التسليم.",
            )
            total = Decimal("0")
            for order, p in enumerate(random.sample(products, k=3)):
                qty = Decimal(random.choice([1, 2, 4, 6, 20]))
                item = QuoteItem(
                    organization=org, quote=quote, product=p, description=p.name_ar,
                    brand_model=f"{p.brand} {p.model}".strip(), quantity=qty, unit=p.unit,
                    unit_price=p.selling_price, display_order=order,
                )
                item.line_total = item.compute_line_total()
                item.save()
                total += item.line_total
            quote.subtotal = total
            quote.total = total
            quote.save(update_fields=["subtotal", "total"])
            if idx == 0:
                quote.ensure_share_token()
                quote.share_enabled = True
                quote.save(update_fields=["share_token", "share_enabled"])

        FollowUp.objects.create(
            organization=org, customer=customers[1], user=user,
            note="متابعة عرض السعر المرسل الأسبوع الماضي",
            scheduled_for=timezone.now() + timezone.timedelta(days=1),
        )

        self.stdout.write(self.style.SUCCESS(f"Demo data created. Login: {email} / {options['password']}"))
