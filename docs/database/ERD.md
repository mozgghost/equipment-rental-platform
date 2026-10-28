# ER diagram (conceptual)

```mermaid
erDiagram
 USER ||--o{ MEMBERSHIP : joins
 COMPANY ||--o{ MEMBERSHIP : has
 COMPANY ||--o{ LOCATION : operates
 COMPANY ||--o{ EQUIPMENT : owns
 LOCATION ||--o{ EQUIPMENT : stores
 EQUIPMENT ||--o{ EQUIPMENT_CATEGORY : classified
 CATEGORY ||--o{ EQUIPMENT_CATEGORY : groups
 EQUIPMENT ||--o{ EQUIPMENT_ATTRIBUTE_VALUE : has
 ATTRIBUTE_DEFINITION ||--o{ EQUIPMENT_ATTRIBUTE_VALUE : defines
 USER ||--o{ BOOKING : requests
 EQUIPMENT ||--o{ BOOKING : reserved_for
 BOOKING ||--o| AVAILABILITY_BLOCK : allocates
 EQUIPMENT ||--o{ AVAILABILITY_BLOCK : capacity
 MAINTENANCE_WINDOW ||--o| AVAILABILITY_BLOCK : blocks
 BOOKING ||--o{ PAYMENT : payment_history
 PAYMENT ||--o{ REFUND : refunds
 PAYMENT ||--o{ WEBHOOK_EVENT : provider_events
 BOOKING ||--o| REVIEW : eligible_review
 USER ||--o{ COMPLAINT : reports
 USER ||--o{ AUDIT_EVENT : performs
```

`AvailabilityBlock` is intentionally the enforcement layer for time allocation. Payment records are planned schema only; actual gateway processing is disabled. SaaS subscription models are deferred until the first pricing hypothesis is validated.
