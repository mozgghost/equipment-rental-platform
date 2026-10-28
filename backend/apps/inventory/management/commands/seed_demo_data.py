"""Deterministic, idempotent demo seed. Refuses to run with DEBUG disabled."""
import random
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from psycopg.types.range import Range

from apps.bookings.models import AvailabilityBlock, Booking, MaintenanceWindow
from apps.inventory.models import (
    AttributeDefinition,
    Category,
    Equipment,
    EquipmentAttributeValue,
    EquipmentCategory,
    EquipmentRateHistory,
    Location,
)
from apps.operations.models import Review
from apps.organizations.models import Company, Membership
from apps.payments.models import Payment


class Command(BaseCommand):
    help = "Create deterministic sandbox data (never use for production or real payment records)."

    def add_arguments(self, parser):
        parser.add_argument("--seed", type=int, default=20261026)
        parser.add_argument(
            "--allow-sandbox", action="store_true",
            help="Explicitly confirm that this is a disposable local sandbox database.",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG or not options["allow_sandbox"]:
            raise CommandError(
                "Refusing to seed without DJANGO_DEBUG=1 and the explicit --allow-sandbox flag."
            )
        database_host = settings.DATABASES["default"].get("HOST", "")
        if database_host not in {"", "localhost", "127.0.0.1", "postgres", "db"}:
            raise CommandError(
                f"Refusing to seed non-local database host {database_host!r}; use a disposable local database."
            )
        seed = options["seed"]
        rng = random.Random(seed)
        User = get_user_model()
        self.stdout.write(f"Creating sandbox dataset using seed={seed} ...")

        companies = []
        for i in range(20):
            company, _ = Company.objects.get_or_create(
                name=f"Demo Supplier {i + 1:02d}",
                defaults={"legal_name": f"Demo Supplier {i + 1:02d} B.V.", "country_code": "NL"},
            )
            companies.append(company)

        users = []
        for i in range(300):
            user, created = User.objects.get_or_create(
                email=f"seed-user-{i + 1:03d}@example.test",
                defaults={"display_name": f"Demo User {i + 1:03d}", "is_active": True},
            )
            if created:
                # Sandbox identities are not usable for login until an operator sets a local password.
                user.set_unusable_password()
                user.save(update_fields=["password"])
            users.append(user)

        for i, company in enumerate(companies):
            Membership.objects.get_or_create(company=company, user=users[i], defaults={"role": Membership.Role.OWNER})
        for i in range(40):
            Membership.objects.get_or_create(
                company=companies[i // 2], user=users[20 + i], defaults={"role": Membership.Role.MANAGER}
            )

        locations = []
        cities = ["Rotterdam", "Amsterdam", "Utrecht", "Eindhoven", "The Hague"]
        for i, company in enumerate(companies):
            loc, _ = Location.objects.get_or_create(
                company=company,
                name="Main yard",
                defaults={"city": cities[i % len(cities)], "country_code": "NL"},
            )
            locations.append(loc)

        category_names = [
            "Excavators", "Mini excavators", "Wheel loaders", "Telehandlers", "Scissor lifts",
            "Boom lifts", "Forklifts", "Dumpers", "Rollers", "Compactors", "Generators",
            "Compressors", "Concrete mixers", "Pumps", "Light towers", "Welders", "Drills",
            "Breakers", "Cutters", "Lifting gear", "Cranes", "Trenchers", "Skid steers",
            "Dozers", "Graders", "Water bowsers", "Road saws", "Scaffolding", "Formwork",
            "Site cabins", "Fencing", "Heaters", "Dehumidifiers", "Vacuum units", "Pressure washers",
            "Power tools", "Survey equipment", "Safety systems", "Trailers", "Trucks", "Attachments",
            "Landscaping", "Forestry", "Agriculture", "Material handling", "Access equipment",
            "Earthmoving", "Roadwork", "Site utilities", "Specialist equipment",
        ]
        categories = []
        for i, name in enumerate(category_names):
            category, _ = Category.objects.get_or_create(
                slug=f"demo-category-{i + 1:03d}",
                defaults={"name": name, "description": f"Sandbox category: {name}"},
            )
            categories.append(category)

        attribute_names = [
            ("Operating weight", "kg", AttributeDefinition.ValueType.NUMBER),
            ("Working height", "m", AttributeDefinition.ValueType.NUMBER),
            ("Rated capacity", "kg", AttributeDefinition.ValueType.NUMBER),
            ("Power output", "kW", AttributeDefinition.ValueType.NUMBER),
            ("Fuel type", "", AttributeDefinition.ValueType.TEXT),
            ("Electric drive", "", AttributeDefinition.ValueType.BOOLEAN),
            ("Transport width", "m", AttributeDefinition.ValueType.NUMBER),
            ("Noise rating", "dB", AttributeDefinition.ValueType.NUMBER),
            ("Emission class", "", AttributeDefinition.ValueType.TEXT),
            ("Remote control", "", AttributeDefinition.ValueType.BOOLEAN),
        ]
        attributes = []
        for i in range(200):
            label, unit, value_type = attribute_names[i % len(attribute_names)]
            name = f"{label} {i + 1:03d}"
            attribute, _ = AttributeDefinition.objects.get_or_create(
                slug=f"demo-attribute-{i + 1:03d}",
                defaults={"name": name, "unit": unit, "value_type": value_type, "filterable": True},
            )
            attributes.append(attribute)

        equipment_items = []
        for i in range(500):
            company = companies[i % 20]
            loc = locations[i % 20]
            unit_rate = Decimal(45 + (i * 37 % 455)).quantize(Decimal("0.01"))
            deposit = Decimal(100 + (i % 5) * 50).quantize(Decimal("0.01"))
            slug = f"demo-equipment-{i + 1:03d}"
            equipment, created = Equipment.objects.get_or_create(
                company=company,
                slug=slug,
                defaults={
                    "location": loc,
                    "name": f"Demo {category_names[i % len(category_names)][:-1] if category_names[i % len(category_names)].endswith('s') else category_names[i % len(category_names)]} {i + 1:03d}",
                    "description": "Sandbox listing for exercising catalogue search and booking workflows. Verify all details with the supplier before real use.",
                    "base_rate": unit_rate,
                    "billing_unit": Equipment.BillingUnit.DAY,
                    "minimum_rental_hours": 1,
                    "deposit_amount": deposit,
                    "currency": "EUR",
                    "status": Equipment.Status.PUBLISHED,
                },
            )
            if created:
                EquipmentRateHistory.objects.create(
                    equipment=equipment,
                    base_rate=unit_rate,
                    deposit_amount=deposit,
                    billing_unit=Equipment.BillingUnit.DAY,
                    effective_from=timezone.now() - timedelta(days=30),
                    changed_by=users[i % 20],
                )
            EquipmentCategory.objects.get_or_create(equipment=equipment, category=categories[i % 50])
            EquipmentCategory.objects.get_or_create(equipment=equipment, category=categories[(i * 7 + 3) % 50])
            attr = attributes[i % 200]
            value_defaults = {}
            if attr.value_type == AttributeDefinition.ValueType.NUMBER:
                value_defaults["number_value"] = Decimal(rng.randint(1, 3000))
            elif attr.value_type == AttributeDefinition.ValueType.BOOLEAN:
                value_defaults["boolean_value"] = bool(i % 2)
            else:
                value_defaults["text_value"] = ["diesel", "electric", "hybrid"][i % 3]
            EquipmentAttributeValue.objects.get_or_create(equipment=equipment, attribute=attr, defaults=value_defaults)
            equipment_items.append(equipment)

        renters = users[60:]
        today = timezone.localdate()
        now = timezone.now()
        completed_bookings = []
        operational_bookings = []
        for i, equipment in enumerate(equipment_items):
            renter = renters[i % len(renters)]
            day = today - timedelta(days=10 + i % 120)
            start = timezone.make_aware(datetime.combine(day, time(8, 0)))
            end = start + timedelta(hours=8)
            booking, _ = Booking.objects.get_or_create(
                renter=renter,
                idempotency_key=f"demo-booking-complete-{i + 1:03d}",
                defaults={
                    "equipment": equipment, "starts_at": start, "ends_at": end,
                    "status": Booking.Status.COMPLETED, "currency": equipment.currency,
                    "quoted_rental_amount": equipment.base_rate, "quoted_deposit_amount": equipment.deposit_amount,
                    "quoted_unit_rate": equipment.base_rate, "quoted_billing_unit": equipment.billing_unit,
                    "quoted_billable_units": 1, "request_fingerprint": f"seed-{seed}-completed-{i + 1:03d}",
                    "hold_expires_at": None,
                },
            )
            AvailabilityBlock.objects.get_or_create(
                booking=booking,
                defaults={"equipment": equipment, "period": Range(start, end, "[)"), "status": AvailabilityBlock.Status.RELEASED},
            )
            Review.objects.get_or_create(
                booking=booking,
                defaults={
                    "author": renter, "equipment": equipment, "rating": 3 + (i % 3),
                    "text": f"Sandbox review {i + 1:03d}: demonstration content only.", "is_published": True,
                },
            )
            completed_bookings.append(booking)

        operational_statuses = [Booking.Status.CONFIRMED, Booking.Status.ACTIVE,
                                Booking.Status.PENDING_PAYMENT, Booking.Status.CANCELLED, Booking.Status.EXPIRED]
        for i, equipment in enumerate(equipment_items):
            renter = renters[(i + 17) % len(renters)]
            group = i // 100
            state = operational_statuses[group]
            if state == Booking.Status.ACTIVE:
                start, end = now - timedelta(hours=2), now + timedelta(hours=6)
            else:
                future_day = now + timedelta(days=3 + i % 25)
                start, end = future_day, future_day + timedelta(hours=8)
            hold_expiry = now + timedelta(minutes=15) if state == Booking.Status.PENDING_PAYMENT else None
            booking, _ = Booking.objects.get_or_create(
                renter=renter,
                idempotency_key=f"demo-booking-{state}-{i + 1:03d}",
                defaults={
                    "equipment": equipment, "starts_at": start, "ends_at": end, "status": state,
                    "currency": equipment.currency, "quoted_rental_amount": equipment.base_rate,
                    "quoted_deposit_amount": equipment.deposit_amount, "quoted_unit_rate": equipment.base_rate,
                    "quoted_billing_unit": equipment.billing_unit, "quoted_billable_units": 1,
                    "request_fingerprint": f"seed-{seed}-{state}-{i + 1:03d}", "hold_expires_at": hold_expiry,
                },
            )
            block_status = AvailabilityBlock.Status.ACTIVE if state in {
                Booking.Status.CONFIRMED, Booking.Status.ACTIVE, Booking.Status.PENDING_PAYMENT
            } else AvailabilityBlock.Status.RELEASED
            AvailabilityBlock.objects.get_or_create(
                booking=booking,
                defaults={"equipment": equipment, "period": Range(start, end, "[)"), "status": block_status},
            )
            operational_bookings.append((booking, state))

        for i in range(20):
            equipment = equipment_items[300 + i]  # these sample bookings are cancelled, so no active reservation conflicts
            maintenance_start = now + timedelta(days=60 + i * 2)
            maintenance_end = maintenance_start + timedelta(hours=10)
            maintenance, _ = MaintenanceWindow.objects.get_or_create(
                equipment=equipment,
                description=f"Demo planned maintenance {i + 1:02d}",
                defaults={"starts_at": maintenance_start, "ends_at": maintenance_end, "created_by": users[0]},
            )
            AvailabilityBlock.objects.get_or_create(
                maintenance=maintenance,
                defaults={"equipment": equipment, "period": Range(maintenance.starts_at, maintenance.ends_at, "[)"), "status": AvailabilityBlock.Status.ACTIVE},
            )

        paid_bookings = list(completed_bookings) + [b for b, state in operational_bookings if state in {
            Booking.Status.CONFIRMED, Booking.Status.ACTIVE
        }]
        for booking in paid_bookings:
            Payment.objects.get_or_create(
                idempotency_key=f"demo-rental-payment-{booking.id}",
                defaults={
                    "booking": booking, "purpose": Payment.Purpose.RENTAL,
                    "amount": booking.quoted_rental_amount, "currency": booking.currency,
                    "status": Payment.Status.SUCCEEDED, "provider": "demo-seed",
                    "provider_payment_id": f"sandbox-payment-{booking.id}",
                },
            )
        for booking in completed_bookings[:100]:
            Payment.objects.get_or_create(
                idempotency_key=f"demo-deposit-payment-{booking.id}",
                defaults={
                    "booking": booking, "purpose": Payment.Purpose.DEPOSIT,
                    "amount": booking.quoted_deposit_amount, "currency": booking.currency,
                    "status": Payment.Status.SUCCEEDED, "provider": "demo-seed",
                    "provider_payment_id": f"sandbox-deposit-{booking.id}",
                },
            )

        self.stdout.write(self.style.SUCCESS(
            "Sandbox seed complete: companies=20 users=300 equipment=500 categories=50 "
            "attributes=200 bookings=1000 payments=800 reviews=500. "
            "Payment rows are synthetic local fixtures, not real transactions."
        ))
