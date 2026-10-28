# Sitemap

```mermaid
flowchart TD
  Home[Landing / catalogue] --> Search[Search & filters]
  Search --> Detail[Equipment detail]
  Detail --> Dates[Select rental period / quote]
  Dates --> Login[Sign in / register]
  Login --> Checkout[Booking result / payment status]
  Login --> Renter[Rental dashboard]
  Renter --> History[Booking history / detail / cancellation]
  Renter --> Profile[Profile / security]
  Login --> Company[Company workspace]
  Company --> Inventory[Equipment / photos / rates]
  Company --> Calendar[Bookings / maintenance / handover]
  Company --> Reports[Operations reports]
  Admin[Platform admin] --> Moderation[Companies / equipment / reviews / complaints]
  Admin --> Audit[Audit / settings]
```

Pages are planned as routing destinations. Only the catalogue and initial login/booking API shell are part of this first source tranche. Pages not implemented in the frontend must not be represented as complete.
