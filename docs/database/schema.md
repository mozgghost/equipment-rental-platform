# Database schema notes

## Core entities

- `accounts_user`: email-identity custom user, Django password hash, staff/active/suspended flags and display name. Email is unique. Passwords are never stored in plaintext.
- `organizations_company`: legal/business identity and active/archive state. Referenced rows use `PROTECT` unless an association/owned characteristic has explicit lifecycle semantics.
- `organizations_membership`: user↔company relation with `owner` or `manager`, unique `(company,user)`. Active status allows revocation without losing audit history.
- `inventory_location`: company-owned yard/address with paired nullable latitude/longitude.
- `inventory_category`: canonical category with unique slug/name; equipment/category is explicit M:N through `EquipmentCategory`.
- `inventory_attributedefinition` and `equipmentattributevalue`: typed characteristics with one value per `(equipment,attribute)`. Cross-field type/value validation is still required in services/serializers.
- `inventory_equipment`: owner, location, slug, description, unit rate, billing unit, minimum duration, deposit, currency and lifecycle status. Monetary fields use `NUMERIC` through Django DecimalField.
- `equipmentphoto`: object-storage key rather than arbitrary upload URL; malware scanning and image processing remain implementation tasks.
- `equipmentratehistory`: dated tariff snapshots for audit; booking copies agreed rate/unit/deposit/total so tariff changes do not alter past bookings.
- `booking`: renter, asset, timestamps, state, quote snapshot, idempotency key/fingerprint and pending-hold deadline.
- `maintenancewindow`: scheduled downtime; the related shared availability block prevents conflicting allocation.
- `availabilityblock`: `tstzrange`, equipment, exactly one booking/maintenance source, active/released state and GiST exclusion constraint. Requires PostgreSQL extension `btree_gist`.
- `payment`, `refund`, `webhookevent`: schema for provider IDs, immutable amounts, idempotency and event de-duplication; not yet connected to a provider.
- `review`, `complaint`, `outboxevent`, `auditevent`: moderation, durable event dispatch and operational trace.

## Delete/archive policy

Bookings, payments, refunds, audit events, memberships and tariff history are historical/financial evidence and should not be hard-deleted in normal application flows. Companies and equipment should be archived/unpublished. `CASCADE` is reserved for owned, non-financial dependent data such as a photo or characteristic value. External media object deletion must be an explicit asynchronous cleanup job after retention checks.

## Index strategy

- Unique constraints: email, company membership, globally unique equipment slug (the public detail route resolves by slug only), `(equipment,attribute)`, `(equipment,category)`, idempotency, provider webhook event.
- B-tree indexes: common status/time filters, company and location catalogue filters, renter booking history, and expiry queue.
- GiST range exclusion: authoritative booking/maintenance conflict protection.
- Search: MVP uses indexed field filters and DRF search; at a proven scale use PostgreSQL full-text search with a generated `tsvector`/GIN index. A distance/radius query requires PostGIS or a documented geospatial approximation; not claimed implemented in this scaffold.

## Money/time rules

All amounts are decimal with two fractional digits at this stage; currency is ISO-4217-like three-character code. Tax, add-on lines and discount campaigns are deferred; they must be separate quote components before commercial billing. Timestamps are aware and stored normalized by PostgreSQL; booking ranges are `[start,end)`.


Consistency note: the relational schema currently does not express `equipment.location.company_id = equipment.company_id` as a plain foreign-key constraint. Every future equipment write service must validate this relationship and be covered by a negative cross-company test; do not expose direct company/equipment writes until that check exists.
