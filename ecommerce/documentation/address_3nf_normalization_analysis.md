# Address Model 3NF Normalization Analysis

## Question
**How does breaking up the address into 2 models affect the 3NF normalization of the Database?**

## Executive Summary

The current implementation uses a **single unified Address model** that already complies with Third Normal Form (3NF). Breaking it into two models could either **maintain** or **violate** 3NF depending on how the split is designed. This document analyzes various splitting approaches and their normalization implications.

---

## Current Design: Single Unified Address Model

### Current Structure
```python
class Address(models.Model):
    id = UUIDField (PK)
    user = ForeignKey(User)           # Who owns this address
    address_type = CharField          # home/work/billing/shipping
    contact_name = CharField          # Contact person
    phone = CharField                 # Contact phone
    street_line1 = CharField          # Street address line 1
    street_line2 = CharField          # Street address line 2
    city = CharField                  # City name
    state_province = CharField        # State/Province
    postal_code = CharField           # ZIP/Postal code
    country_code = ForeignKey(Country) # Reference to Country table
    is_default = BooleanField         # Default address flag
    created_at = DateTimeField
    updated_at = DateTimeField
```

### 3NF Compliance Analysis

**First Normal Form (1NF):** ✅ Compliant
- All attributes contain atomic values
- No repeating groups
- Each row is unique (primary key: id)

**Second Normal Form (2NF):** ✅ Compliant
- In 1NF
- No composite primary key, so no partial dependencies exist
- All non-key attributes depend on the entire primary key (id)

**Third Normal Form (3NF):** ✅ Compliant
- In 2NF
- No transitive dependencies exist:
  - All attributes directly depend on `id` (the primary key)
  - `country_code` references a separate Country table (proper foreign key)
  - No attribute depends on another non-key attribute

### Functional Dependencies
```
id → user_id
id → address_type
id → contact_name
id → phone
id → street_line1, street_line2
id → city
id → state_province
id → postal_code
id → country_code
id → is_default
id → created_at, updated_at
```

**Conclusion:** The current single-model design is **fully normalized to 3NF**.

---

## Option 1: Split into UserAddress + Location Models

### Proposed Structure

#### Model 1: UserAddress (User-specific metadata)
```python
class UserAddress(models.Model):
    id = UUIDField (PK)
    user = ForeignKey(User)
    location = ForeignKey(Location)   # Reference to Location
    address_type = CharField          # home/work/billing/shipping
    contact_name = CharField          # Contact person
    phone = CharField                 # Contact phone
    is_default = BooleanField
    created_at = DateTimeField
    updated_at = DateTimeField
```

#### Model 2: Location (Reusable location data)
```python
class Location(models.Model):
    id = UUIDField (PK)
    street_line1 = CharField
    street_line2 = CharField
    city = CharField
    state_province = CharField
    postal_code = CharField
    country_code = ForeignKey(Country)
    created_at = DateTimeField
```

### 3NF Compliance Analysis

**UserAddress:** ✅ Compliant with 3NF
- No transitive dependencies
- All attributes directly depend on the primary key

**Location:** ✅ Compliant with 3NF
- No transitive dependencies
- All location attributes directly depend on the primary key
- `country_code` is a proper foreign key reference

### Impact on 3NF

**Result:** ✅ **Maintains 3NF compliance**

**Benefits:**
1. **Deduplication:** Multiple users can reference the same physical location
2. **Storage efficiency:** Reduces redundancy for shared addresses (e.g., office buildings)
3. **Consistency:** Updates to a location reflect for all users at that location
4. **Still normalized:** Both tables remain in 3NF

**Drawbacks:**
1. **Increased complexity:** Requires JOIN operations for queries
2. **Performance overhead:** Additional table lookup needed
3. **Rare use case:** In e-commerce, addresses are typically user-specific
4. **Privacy concerns:** Shared location data could leak information

**Recommendation:** This approach maintains 3NF but is **NOT recommended** for typical e-commerce applications where addresses are personal and unique to each user.

---

## Option 2: Split into Address + AddressMetadata

### Proposed Structure

#### Model 1: Address (Core location data)
```python
class Address(models.Model):
    id = UUIDField (PK)
    street_line1 = CharField
    street_line2 = CharField
    city = CharField
    state_province = CharField
    postal_code = CharField
    country_code = ForeignKey(Country)
```

#### Model 2: AddressMetadata (User-specific data)
```python
class AddressMetadata(models.Model):
    id = UUIDField (PK)
    address = ForeignKey(Address)
    user = ForeignKey(User)
    address_type = CharField
    contact_name = CharField
    phone = CharField
    is_default = BooleanField
    created_at = DateTimeField
    updated_at = DateTimeField
```

### 3NF Compliance Analysis

**Address:** ✅ Compliant with 3NF
- Contains only location-related attributes
- No transitive dependencies

**AddressMetadata:** ✅ Compliant with 3NF
- Contains user-specific metadata
- All attributes depend on the primary key
- `address` and `user` are proper foreign keys

### Impact on 3NF

**Result:** ✅ **Maintains 3NF compliance**

This is essentially the same as Option 1 but with reversed naming. The analysis and implications are identical.

---

## Option 3: Split into Address + ContactInfo (VIOLATES 3NF)

### Proposed Structure (INCORRECT)

#### Model 1: Address
```python
class Address(models.Model):
    id = UUIDField (PK)
    user = ForeignKey(User)
    contact_info = ForeignKey(ContactInfo)  # WRONG: Creates transitive dependency
    street_line1 = CharField
    street_line2 = CharField
    city = CharField
    state_province = CharField
    postal_code = CharField
    country_code = ForeignKey(Country)
    address_type = CharField
    is_default = BooleanField
```

#### Model 2: ContactInfo
```python
class ContactInfo(models.Model):
    id = UUIDField (PK)
    user = ForeignKey(User)  # WRONG: Redundant with Address.user
    contact_name = CharField
    phone = CharField
```

### 3NF Violation Analysis

**❌ VIOLATES 3NF due to transitive dependency:**

```
Address.id → Address.contact_info_id
Address.contact_info_id → ContactInfo.user_id
Therefore: Address.id → ContactInfo.user_id

But we also have:
Address.id → Address.user_id

This creates a transitive dependency:
Address.id → Address.user_id → ContactInfo.user_id
```

**Problem:** `Address.user` and `ContactInfo.user` create redundancy and a transitive dependency, violating 3NF.

**Result:** ❌ **VIOLATES 3NF** - Not recommended

---

## Option 4: Vertical Split by Usage Pattern

### Proposed Structure

#### Model 1: ShippingAddress
```python
class ShippingAddress(models.Model):
    id = UUIDField (PK)
    user = ForeignKey(User)
    contact_name = CharField
    phone = CharField
    street_line1 = CharField
    street_line2 = CharField
    city = CharField
    state_province = CharField
    postal_code = CharField
    country_code = ForeignKey(Country)
    is_default = BooleanField
```

#### Model 2: BillingAddress
```python
class BillingAddress(models.Model):
    id = UUIDField (PK)
    user = ForeignKey(User)
    contact_name = CharField
    phone = CharField
    street_line1 = CharField
    street_line2 = CharField
    city = CharField
    state_province = CharField
    postal_code = CharField
    country_code = ForeignKey(Country)
    is_default = BooleanField
```

### 3NF Compliance Analysis

**Both models:** ✅ Individually compliant with 3NF
- Each table has no transitive dependencies
- All attributes depend only on their respective primary keys

### Impact on 3NF

**Result:** ✅ **Maintains 3NF compliance**

**However, this design has significant issues:**

**Problems:**
1. **Code duplication:** Identical structure in both models
2. **Maintenance burden:** Changes must be made in multiple places
3. **Inflexibility:** Cannot easily add new address types (home, work, etc.)
4. **Violates DRY principle:** Don't Repeat Yourself
5. **Query complexity:** Need UNION queries to get all user addresses

**Recommendation:** ❌ **Not recommended** despite maintaining 3NF. Poor design practice.

---

## Comparison Summary

| Approach | 3NF Compliant? | Storage Efficiency | Query Performance | Code Maintainability | Recommended? |
|----------|----------------|-------------------|-------------------|---------------------|--------------|
| **Current (Single Model)** | ✅ Yes | Good | Excellent | Excellent | ✅ **Yes** |
| **Option 1 (UserAddress + Location)** | ✅ Yes | Excellent | Good | Good | ⚠️ Situational |
| **Option 2 (Address + Metadata)** | ✅ Yes | Excellent | Good | Good | ⚠️ Situational |
| **Option 3 (Address + ContactInfo)** | ❌ No | Poor | Poor | Poor | ❌ No |
| **Option 4 (Shipping + Billing)** | ✅ Yes | Poor | Good | Poor | ❌ No |

---

## Functional Dependency Analysis

### Current Single Model
```
Functional Dependencies:
id → {user_id, address_type, contact_name, phone, street_line1, 
      street_line2, city, state_province, postal_code, country_code, 
      is_default, created_at, updated_at}

Candidate Key: {id}
Prime Attributes: {id}
Non-prime Attributes: {all others}

3NF Check:
- No partial dependencies (no composite key)
- No transitive dependencies (all attributes directly depend on id)
✅ In 3NF
```

### Option 1 (Recommended Split)
```
UserAddress:
id → {user_id, location_id, address_type, contact_name, phone, is_default}

Location:
id → {street_line1, street_line2, city, state_province, postal_code, country_code}

3NF Check:
- UserAddress: All attributes directly depend on id ✅
- Location: All attributes directly depend on id ✅
- No transitive dependencies in either table ✅
✅ Both in 3NF
```

---

## Real-World Considerations

### When to Use Single Model (Current Design) ✅
- **E-commerce applications** (most common)
- User addresses are typically unique and personal
- Simplicity is preferred over optimization
- Fast development and maintenance needed
- Address changes are user-specific

### When to Consider Two Models
- **Enterprise applications** with shared office locations
- **Real estate or property management systems**
- Multiple entities share the same physical address
- Address data is frequently reused across many users
- Need to track location metadata separately from user associations

### When NOT to Split
- Standard e-commerce platforms
- Small to medium-sized applications
- When duplication is minimal
- When performance isn't a critical concern
- When simplicity trumps optimization

---

## Recommendations

### ✅ Recommendation 1: Keep Single Model (Current Design)

**For typical e-commerce applications, maintain the current single Address model.**

**Reasons:**
1. Already in 3NF
2. Simple to understand and maintain
3. Excellent query performance (no JOINs needed)
4. Addresses are typically user-specific
5. Low risk of significant duplication
6. Follows common e-commerce patterns

### ⚠️ Recommendation 2: Consider Split Only If

**Only split into two models (UserAddress + Location) if:**
1. You have proven, measurable duplication (>30% of addresses are shared)
2. Storage costs are a genuine concern
3. Your application has shared locations (offices, warehouses)
4. You need location-based analytics separate from users
5. You can justify the added complexity

**If you do split:**
- Use Option 1 (UserAddress + Location)
- Add proper indexing on foreign keys
- Implement caching for frequent location lookups
- Document the design decision clearly

### ❌ Recommendation 3: Avoid These Approaches

**Never use:**
- Option 3 (transitive dependencies - violates 3NF)
- Option 4 (vertical split by type - code duplication)
- Any design that creates redundant foreign keys

---

## Migration Path (If Splitting)

If you decide to split the current model into two, here's the recommended approach:

### Step 1: Create Location Model
```python
class Location(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    street_line1 = models.CharField(max_length=255)
    street_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state_province = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country_code = models.ForeignKey(Country, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['city', 'postal_code']),
            models.Index(fields=['country_code']),
        ]
```

### Step 2: Add Location Reference to Address
```python
class Address(models.Model):
    # ... keep existing fields ...
    location = models.ForeignKey(Location, on_delete=models.CASCADE, null=True)
    # Keep old fields temporarily for migration
```

### Step 3: Data Migration
```python
def migrate_addresses_to_locations(apps, schema_editor):
    Address = apps.get_model('accounts', 'Address')
    Location = apps.get_model('accounts', 'Location')
    
    for address in Address.objects.all():
        # Check if location already exists (deduplication)
        location, created = Location.objects.get_or_create(
            street_line1=address.street_line1,
            street_line2=address.street_line2 or '',
            city=address.city,
            state_province=address.state_province,
            postal_code=address.postal_code,
            country_code=address.country_code,
        )
        address.location = location
        address.save()
```

### Step 4: Remove Redundant Fields
```python
class Address(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    address_type = models.CharField(max_length=20)
    contact_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

---

## Conclusion

**Answer to the Question:**

> "How does breaking up the address into 2 models affect the 3NF normalization of the Database?"

**Short Answer:** Breaking the address into two models **can maintain 3NF compliance** if done correctly (Option 1 or 2), but can also **violate 3NF** if done incorrectly (Option 3). The current single-model design is already in 3NF and is the recommended approach for most e-commerce applications.

**Key Takeaways:**

1. ✅ **Current single Address model is already in 3NF**
2. ✅ **Splitting into UserAddress + Location maintains 3NF** (but adds complexity)
3. ❌ **Splitting with redundant foreign keys violates 3NF** (Option 3)
4. 📊 **3NF compliance doesn't guarantee good design** (Option 4 shows this)
5. 🎯 **For e-commerce: Keep the single model** unless you have specific requirements

**Final Recommendation:** Unless you have a compelling reason with measurable benefits, **keep the current single Address model**. It's in 3NF, simple, performant, and follows industry standards for e-commerce applications.

---

## References

- **Third Normal Form (3NF):** A table is in 3NF if it is in 2NF and no non-prime attribute is transitively dependent on the primary key.
- **Transitive Dependency:** When A → B and B → C, then A → C is a transitive dependency.
- **Functional Dependency:** When the value of one attribute determines the value of another attribute.

---

*Document created: 2026-02-07*
*Last updated: 2026-02-07*
