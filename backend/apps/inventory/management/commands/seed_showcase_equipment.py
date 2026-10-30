"""Create or update 24 curated equipment listings in the local showcase."""
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.inventory.models import (
    Category,
    Equipment,
    EquipmentCategory,
    EquipmentRateHistory,
    Location,
)
from apps.organizations.models import Company


SHOWCASE_ITEMS = [
    {
        "slug": "excavator-cat-320",
        "name": "CAT 320 Hydraulic Excavator",
        "category": "Excavators",
        "description": "20-tonne tracked hydraulic excavator for site preparation, trenching and bulk earthmoving. Suitable for demanding construction projects.",
        "rate": "420.00", "deposit": "1500.00", "hours": 8,
    },
    {
        "slug": "mini-excavator-kubota",
        "name": "Kubota KX Mini Excavator",
        "category": "Mini excavators",
        "description": "Compact excavator for landscaping, utility trenches and confined urban construction sites. Easy to transport and manoeuvre.",
        "rate": "165.00", "deposit": "600.00", "hours": 4,
    },
    {
        "slug": "wheel-loader-volvo",
        "name": "Volvo L120 Wheel Loader",
        "category": "Wheel loaders",
        "description": "Heavy-duty wheel loader for loading aggregates, handling materials and maintaining busy construction yards.",
        "rate": "350.00", "deposit": "1200.00", "hours": 8,
    },
    {
        "slug": "telehandler",
        "name": "Rotating Telescopic Handler",
        "category": "Telehandlers",
        "description": "Telescopic handler for lifting and positioning palletised materials at height on construction and industrial sites.",
        "rate": "245.00", "deposit": "900.00", "hours": 4,
    },
    {
        "slug": "scissor-lift",
        "name": "Electric Scissor Lift 12 m",
        "category": "Scissor lifts",
        "description": "Electric indoor scissor lift for installation, maintenance and finishing work. Suitable for level industrial floors.",
        "rate": "95.00", "deposit": "350.00", "hours": 4,
    },
    {
        "slug": "boom-lift",
        "name": "Articulating Boom Lift 20 m",
        "category": "Boom lifts",
        "description": "Articulating boom platform for elevated access around obstacles on construction, maintenance and installation projects.",
        "rate": "185.00", "deposit": "700.00", "hours": 4,
    },
    {
        "slug": "forklift",
        "name": "Diesel Forklift 3.5 t",
        "category": "Forklifts",
        "description": "Industrial diesel forklift for loading, unloading and moving heavy pallets and construction materials.",
        "rate": "110.00", "deposit": "400.00", "hours": 4,
    },
    {
        "slug": "road-roller",
        "name": "Single Drum Soil Roller",
        "category": "Rollers",
        "description": "Vibratory single drum roller for compacting soil, sub-base and granular materials during road and site works.",
        "rate": "175.00", "deposit": "650.00", "hours": 4,
    },
    {
        "slug": "generator",
        "name": "Diesel Generator 100 kVA",
        "category": "Generators",
        "description": "Site power generator for temporary electricity supply to construction equipment, lighting and site facilities.",
        "rate": "125.00", "deposit": "500.00", "hours": 4,
    },
    {
        "slug": "air-compressor",
        "name": "Mobile Air Compressor",
        "category": "Compressors",
        "description": "Towable compressed-air unit for pneumatic tools, surface preparation and general construction applications.",
        "rate": "85.00", "deposit": "300.00", "hours": 4,
    },
    {
        "slug": "concrete-mixer",
        "name": "Professional Concrete Mixer",
        "category": "Concrete mixers",
        "description": "Site concrete mixer for preparing consistent batches of mortar and concrete for small and medium construction tasks.",
        "rate": "45.00", "deposit": "150.00", "hours": 4,
    },
    {
        "slug": "concrete-pump",
        "name": "Trailer Concrete Pump",
        "category": "Pumps",
        "description": "Concrete pumping equipment for transferring concrete to hard-to-reach sections of a construction site.",
        "rate": "210.00", "deposit": "800.00", "hours": 8,
    },
    {
        "slug": "dump-truck",
        "name": "Articulated Site Dump Truck",
        "category": "Dumpers",
        "description": "Site dumper for transporting soil, aggregates and construction materials across rough and uneven terrain.",
        "rate": "195.00", "deposit": "700.00", "hours": 4,
    },
    {
        "slug": "bulldozer",
        "name": "Tracked Bulldozer",
        "category": "Dozers",
        "description": "Tracked bulldozer for bulk earthmoving, site levelling and pushing material over demanding ground conditions.",
        "rate": "390.00", "deposit": "1400.00", "hours": 8,
    },
    {
        "slug": "mobile-crane",
        "name": "All-Terrain Mobile Crane",
        "category": "Cranes",
        "description": "Mobile crane for lifting and positioning heavy construction components. Lifting plan and operator requirements must be confirmed.",
        "rate": "650.00", "deposit": "2500.00", "hours": 8,
    },
    {
        "slug": "trencher",
        "name": "Compact Chain Trencher",
        "category": "Trenchers",
        "description": "Compact trenching machine for narrow utility trenches, irrigation lines and cable installation.",
        "rate": "145.00", "deposit": "500.00", "hours": 4,
    },
    {
        "slug": "skid-steer-loader",
        "name": "Skid Steer Loader",
        "category": "Skid steers",
        "description": "Agile skid steer loader for material handling, site cleanup and earthmoving in restricted working areas.",
        "rate": "135.00", "deposit": "500.00", "hours": 4,
    },
    {
        "slug": "scaffolding",
        "name": "Modular Construction Scaffolding",
        "category": "Scaffolding",
        "description": "Modular scaffolding system for temporary access and work platforms. Configuration and quantities must be agreed before rental.",
        "rate": "55.00", "deposit": "250.00", "hours": 24,
    },
    {
        "slug": "site-cabin",
        "name": "Portable Site Office Cabin",
        "category": "Site cabins",
        "description": "Portable site office cabin for temporary project administration and secure on-site workspace.",
        "rate": "75.00", "deposit": "300.00", "hours": 24,
    },
    {
        "slug": "site-fencing",
        "name": "Temporary Site Fencing",
        "category": "Fencing",
        "description": "Temporary fencing panels for defining work zones and restricting access to construction areas. Rental quantity is agreed separately.",
        "rate": "3.50", "deposit": "100.00", "hours": 24,
    },
    {
        "slug": "construction-heater",
        "name": "Indirect-Fired Construction Heater",
        "category": "Heaters",
        "description": "Indirect-fired heater for temporary heating of ventilated construction and industrial spaces.",
        "rate": "65.00", "deposit": "250.00", "hours": 4,
    },
    {
        "slug": "pressure-washer",
        "name": "Industrial Pressure Washer",
        "category": "Pressure washers",
        "description": "High-pressure cleaning unit for machinery, tools, paved surfaces and construction site maintenance.",
        "rate": "40.00", "deposit": "150.00", "hours": 4,
    },
    {
        "slug": "concrete-vibrator",
        "name": "Concrete Immersion Vibrator",
        "category": "Power tools",
        "description": "Concrete vibration equipment for compacting freshly poured concrete and reducing trapped air in structural pours.",
        "rate": "28.00", "deposit": "100.00", "hours": 4,
    },
    {
        "slug": "mobile-light-tower",
        "name": "Mobile LED Light Tower",
        "category": "Light towers",
        "description": "Mobile LED lighting tower for illuminating temporary work areas, access routes and night construction operations.",
        "rate": "58.00", "deposit": "220.00", "hours": 4,
    },
]


class Command(BaseCommand):
    help = "Create or update 24 curated showcase listings in a local sandbox."

    def add_arguments(self, parser):
        parser.add_argument(
            "--allow-sandbox",
            action="store_true",
            help="Confirm that this is a disposable local sandbox database.",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG or not options["allow_sandbox"]:
            raise CommandError(
                "Refusing to run without DEBUG=1 and the explicit --allow-sandbox flag."
            )

        database_host = settings.DATABASES["default"].get("HOST", "")
        if database_host not in {"", "localhost", "127.0.0.1", "postgres", "db"}:
            raise CommandError(
                f"Refusing to use non-local database host {database_host!r}."
            )

        if len(SHOWCASE_ITEMS) != 24:
            raise CommandError("The showcase definition must contain exactly 24 items.")

        with transaction.atomic():
            companies = list(
                Company.objects.filter(is_active=True).order_by("id")[:20]
            )
            if not companies:
                raise CommandError("No active companies found.")

            locations = {
                location.company_id: location
                for location in Location.objects.filter(
                    company__in=companies,
                    is_active=True,
                ).order_by("id")
            }

            categories = {
                category.name: category
                for category in Category.objects.filter(is_active=True)
            }

            missing_categories = sorted({
                item["category"] for item in SHOWCASE_ITEMS
                if item["category"] not in categories
            })
            if missing_categories:
                raise CommandError(
                    "Missing active categories: " + ", ".join(missing_categories)
                )

            missing_locations = [
                company.name for company in companies
                if company.id not in locations
            ]
            if missing_locations:
                raise CommandError(
                    "Companies without active locations: "
                    + ", ".join(missing_locations)
                )

            showcase_slugs = [item["slug"] for item in SHOWCASE_ITEMS]

            collisions = Equipment.objects.filter(
                slug__in=showcase_slugs,
                is_showcase=False,
            )

            if collisions.exists():
                collision_slugs = ", ".join(
                    collisions.values_list("slug", flat=True)
                )
                raise CommandError(
                    "These slugs already belong to non-showcase equipment: "
                    + collision_slugs
                )

            created_count = 0
            updated_count = 0

            for index, item in enumerate(SHOWCASE_ITEMS):
                company = companies[index % len(companies)]
                location = locations[company.id]
                category = categories[item["category"]]

                equipment, created = Equipment.objects.update_or_create(
                    slug=item["slug"],
                    defaults={
                        "company": company,
                        "location": location,
                        "name": item["name"],
                        "description": item["description"],
                        "base_rate": Decimal(item["rate"]),
                        "billing_unit": Equipment.BillingUnit.DAY,
                        "minimum_rental_hours": item["hours"],
                        "deposit_amount": Decimal(item["deposit"]),
                        "currency": "EUR",
                        "status": Equipment.Status.PUBLISHED,
                        "is_showcase": True,
                    },
                )

                EquipmentCategory.objects.get_or_create(
                    equipment=equipment,
                    category=category,
                )

                latest_rate = EquipmentRateHistory.objects.filter(
                    equipment=equipment
                ).first()

                rate_changed = (
                    latest_rate is None
                    or latest_rate.base_rate != equipment.base_rate
                    or latest_rate.deposit_amount != equipment.deposit_amount
                    or latest_rate.billing_unit != equipment.billing_unit
                )

                if rate_changed:
                    EquipmentRateHistory.objects.create(
                        equipment=equipment,
                        base_rate=equipment.base_rate,
                        deposit_amount=equipment.deposit_amount,
                        billing_unit=equipment.billing_unit,
                        effective_from=timezone.now(),
                        changed_by=None,
                    )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Showcase complete: {created_count} created, "
                f"{updated_count} updated. Total defined: 24."
            )
        )
