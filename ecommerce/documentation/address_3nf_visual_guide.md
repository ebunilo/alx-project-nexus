# Visual Guide: Address Model 3NF Analysis

## Current Design (Single Model) - ✅ 3NF Compliant

```
┌─────────────────────────────────────────────────────────┐
│                     Address Table                        │
├─────────────────────────────────────────────────────────┤
│ PK  id (UUID)                                           │
│ FK  user_id          → Users.id                         │
│     address_type     (home/work/billing/shipping)       │
│     contact_name                                        │
│     phone                                               │
│     street_line1                                        │
│     street_line2                                        │
│     city                                                │
│     state_province                                      │
│     postal_code                                         │
│ FK  country_code     → Countries.code                   │
│     is_default                                          │
│     created_at                                          │
│     updated_at                                          │
└─────────────────────────────────────────────────────────┘

Functional Dependencies:
id → all other attributes (direct, no transitive dependencies)

✅ 1NF: All atomic values
✅ 2NF: All attributes depend on full primary key
✅ 3NF: No transitive dependencies
```

---

## Option 1: Split into UserAddress + Location - ✅ 3NF Compliant

```
┌──────────────────────────────────────┐
│       UserAddress Table              │
├──────────────────────────────────────┤
│ PK  id (UUID)                       │
│ FK  user_id      → Users.id         │
│ FK  location_id  → Location.id      │
│     address_type                    │
│     contact_name                    │
│     phone                           │
│     is_default                      │
│     created_at                      │
│     updated_at                      │
└──────────────────────────────────────┘
           │
           │ references
           ↓
┌──────────────────────────────────────┐
│        Location Table                │
├──────────────────────────────────────┤
│ PK  id (UUID)                       │
│     street_line1                    │
│     street_line2                    │
│     city                            │
│     state_province                  │
│     postal_code                     │
│ FK  country_code → Countries.code   │
│     created_at                      │
└──────────────────────────────────────┘

Functional Dependencies:
UserAddress: id → {user_id, location_id, address_type, ...}
Location: id → {street_line1, city, postal_code, ...}

✅ 3NF: Both tables independently normalized
✅ No transitive dependencies
```

### Diagram: Data Flow

```
┌──────┐     ┌──────────────┐     ┌──────────┐
│ User │────▶│ UserAddress  │────▶│ Location │
└──────┘     │  (metadata)  │     │ (shared) │
             └──────────────┘     └──────────┘
                    │                   │
                    │                   │
                    ↓                   ↓
            User-specific data    Reusable location
            - address_type        - street_line1
            - contact_name        - city
            - phone              - postal_code
            - is_default         - country_code
```

**Pros:**
- ✅ Deduplication of shared locations
- ✅ Both tables in 3NF
- ✅ Flexible for shared addresses

**Cons:**
- ⚠️ Requires JOIN for queries
- ⚠️ More complex
- ⚠️ Rare use case in e-commerce

---

## Option 3: Address + ContactInfo - ❌ VIOLATES 3NF

```
┌──────────────────────────────────────┐
│         Address Table                │
├──────────────────────────────────────┤
│ PK  id (UUID)                       │
│ FK  user_id                         │
│ FK  contact_info_id  ─────┐        │
│     street_line1           │        │
│     city                   │        │
│     postal_code            │        │
│ FK  country_code           │        │
│     address_type           │        │
│     is_default             │        │
└────────────────────────────┼────────┘
                             │
                             └────────▶ ┌────────────────────────┐
                                        │  ContactInfo Table     │
                                        ├────────────────────────┤
                                        │ PK  id (UUID)         │
                                        │ FK  user_id ◀─────┐   │
                                        │     contact_name   │   │
                                        │     phone         │   │
                                        └────────────────────┼───┘
                                                            │
                                        REDUNDANT!          │
                                        ═══════════════════════

Transitive Dependency Problem:
Address.id → Address.user_id
Address.id → Address.contact_info_id → ContactInfo.user_id

Result: Address.id ──→ Address.user_id ──→ ContactInfo.user_id
                     └──────────────────────→ ContactInfo.user_id

❌ VIOLATES 3NF: Transitive dependency exists
❌ Data redundancy: user_id stored in two places
❌ Update anomalies possible
```

---

## Option 4: Vertical Split - ✅ 3NF but Poor Design

```
┌──────────────────────────────────┐   ┌──────────────────────────────────┐
│    ShippingAddress Table         │   │    BillingAddress Table          │
├──────────────────────────────────┤   ├──────────────────────────────────┤
│ PK  id                          │   │ PK  id                          │
│ FK  user_id                     │   │ FK  user_id                     │
│     contact_name                │   │     contact_name                │
│     phone                       │   │     phone                       │
│     street_line1                │   │     street_line1                │
│     street_line2                │   │     street_line2                │
│     city                        │   │     city                        │
│     state_province              │   │     state_province              │
│     postal_code                 │   │     postal_code                 │
│ FK  country_code                │   │ FK  country_code                │
│     is_default                  │   │     is_default                  │
└──────────────────────────────────┘   └──────────────────────────────────┘

✅ Each table in 3NF
❌ Massive code duplication
❌ Violates DRY principle
❌ Hard to maintain
❌ Inflexible (can't add "home" or "work" types)
```

---

## Comparison: Query Patterns

### Single Model Query (Simple)
```sql
-- Get all user addresses
SELECT * FROM addresses 
WHERE user_id = '...' 
ORDER BY is_default DESC;

-- Single table, fast query
```

### Two Model Query (Complex)
```sql
-- Get all user addresses with location details
SELECT 
    ua.*,
    l.street_line1,
    l.city,
    l.postal_code,
    c.name as country_name
FROM user_addresses ua
JOIN locations l ON ua.location_id = l.id
JOIN countries c ON l.country_code = c.code
WHERE ua.user_id = '...'
ORDER BY ua.is_default DESC;

-- Requires JOINs, slightly slower
```

---

## Decision Tree

```
                    Should I split the Address model?
                                 │
                                 ▼
                    Do I have significant duplication?
                    (>30% of addresses are identical)
                         │              │
                        YES            NO
                         │              │
                         ▼              ▼
              Are multiple users      Keep single model
              sharing addresses?      ✅ RECOMMENDED
                         │
                         ▼
              Use UserAddress + Location
              (Option 1 - maintains 3NF)
```

---

## 3NF Visual Checklist

```
Third Normal Form Requirements:
┌────────────────────────────────────────────────────────┐
│ ✓ Table is in Second Normal Form (2NF)               │
│ ✓ No transitive dependencies                         │
│ ✓ All non-key attributes directly depend on PK       │
│ ✓ No attribute depends on another non-key attribute  │
└────────────────────────────────────────────────────────┘

Example of Transitive Dependency (VIOLATES 3NF):
┌────────┐     ┌──────────┐     ┌──────────────┐
│   PK   │────▶│ Attr A   │────▶│   Attr B     │
└────────┘     └──────────┘     └──────────────┘
    │               ╲                   ▲
    │                ╲                  │
    └─────────────────╲────────────────┘
                  Transitive dependency!

Solution: Split into two tables:
┌────────┐     ┌──────────┐
│ Table1 │────▶│ Table2   │
│   PK   │     │ Attr A   │
│ FK→A   │     │ Attr B   │
└────────┘     └──────────┘
```

---

## Summary Matrix

| Approach | 3NF? | Complexity | Performance | Recommended? |
|----------|------|------------|-------------|--------------|
| Single Address | ✅ | Low | Excellent | ✅ **YES** |
| UserAddress + Location | ✅ | Medium | Good | ⚠️ Situational |
| Address + ContactInfo | ❌ | Medium | Poor | ❌ NO |
| Shipping + Billing Split | ✅ | High | Good | ❌ NO |

---

## Real-World Example

### E-Commerce Platform (Current Design)
```
John Doe's Addresses:
┌─────────────────────────────────────────┐
│ Home Address (Default)                  │
│ 123 Main St, Apt 4B                    │
│ New York, NY 10001                     │
│ Contact: John Doe, +1234567890         │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Office Address                          │
│ 456 Business Ave, Suite 100            │
│ New York, NY 10002                     │
│ Contact: Reception, +1234567899        │
└─────────────────────────────────────────┘

Each stored as separate row in Address table.
No duplication, no transitive dependencies.
✅ Perfect for e-commerce!
```

### Enterprise with Shared Locations
```
If 100 employees work at:
"456 Business Ave, Suite 100, New York, NY 10002"

Option 1 saves this location once:
┌──────────────────────┐
│ Location: Office     │
│ 456 Business Ave...  │
└──────────────────────┘
         ▲
         │ Referenced by 100 UserAddress records
         │
    ┌────┴────┬────┬────┬─────┐
    │         │    │    │     │
 Alice     Bob  ...  ...  Zoe

This makes sense for enterprise, not e-commerce.
```

---

*See [address_3nf_normalization_analysis.md](./address_3nf_normalization_analysis.md) for detailed analysis.*
