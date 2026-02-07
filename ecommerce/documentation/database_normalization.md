# Database Normalization Guidelines for E-Commerce Platform

## Overview

This document outlines the database normalization principles applied to the e-commerce platform, with a focus on achieving Third Normal Form (3NF) across all tables.

---

## Normalization Basics

### What is Database Normalization?

Database normalization is the process of organizing data to:
1. **Eliminate redundancy** - Avoid storing the same data in multiple places
2. **Ensure data integrity** - Maintain consistency across the database
3. **Improve query performance** - Optimize database operations
4. **Facilitate maintenance** - Make schema changes easier

### Normal Forms Hierarchy

```
UNF (Unnormalized Form)
    ↓
1NF (First Normal Form)
    ↓
2NF (Second Normal Form)
    ↓
3NF (Third Normal Form)
    ↓
BCNF (Boyce-Codd Normal Form)
    ↓
4NF (Fourth Normal Form)
    ↓
5NF (Fifth Normal Form)
```

**Target for this project:** 3NF (Third Normal Form)

---

## First Normal Form (1NF)

### Definition
A table is in 1NF if:
1. All attributes contain **atomic (indivisible) values**
2. Each column contains values of a **single type**
3. Each column has a **unique name**
4. The order of rows doesn't matter
5. No repeating groups or arrays

### Example: Violation of 1NF

**❌ Bad (Not in 1NF):**
```sql
CREATE TABLE users (
    id UUID,
    name VARCHAR(100),
    emails TEXT,  -- "user@example.com, user2@example.com" (multiple values)
    phone_numbers TEXT  -- "+1234567890, +9876543210" (multiple values)
);
```

**✅ Good (In 1NF):**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(255)
);

CREATE TABLE user_phone_numbers (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    phone_number VARCHAR(50)
);
```

### Platform Compliance

All tables in our e-commerce platform are in 1NF:
- ✅ User table: Single email per row
- ✅ Address table: Each address is a separate row
- ✅ Product table: Variants are in separate table
- ✅ Order table: Line items in separate table

---

## Second Normal Form (2NF)

### Definition
A table is in 2NF if:
1. It's in **1NF**
2. All non-key attributes are **fully functionally dependent** on the primary key
3. No **partial dependencies** exist (only applies to composite keys)

### Example: Violation of 2NF

**❌ Bad (Not in 2NF):**
```sql
CREATE TABLE order_items (
    order_id UUID,
    product_id UUID,
    product_name VARCHAR(255),  -- Depends only on product_id
    product_price DECIMAL,      -- Depends only on product_id
    quantity INTEGER,
    PRIMARY KEY (order_id, product_id)
);
```

**Problem:** `product_name` and `product_price` depend only on `product_id`, not the full composite key `(order_id, product_id)`.

**✅ Good (In 2NF):**
```sql
CREATE TABLE products (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    price DECIMAL
);

CREATE TABLE order_items (
    order_id UUID,
    product_id UUID,
    quantity INTEGER,
    PRIMARY KEY (order_id, product_id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);
```

### Platform Compliance

All tables with composite keys in our platform are in 2NF:
- ✅ Product attributes: Fully dependent on composite key
- ✅ Cart items: Quantity depends on both cart_id and product_id
- ✅ Category hierarchy: No partial dependencies

---

## Third Normal Form (3NF)

### Definition
A table is in 3NF if:
1. It's in **2NF**
2. All non-key attributes are **directly dependent** on the primary key
3. No **transitive dependencies** exist (A → B → C)

### What is a Transitive Dependency?

```
If: A → B and B → C
Then: A → C (transitive dependency)
```

This means attribute C depends on A through B, rather than directly on A.

### Example: Violation of 3NF

**❌ Bad (Not in 3NF):**
```sql
CREATE TABLE orders (
    id UUID PRIMARY KEY,
    customer_id UUID,
    customer_email VARCHAR(255),  -- Transitive: id → customer_id → customer_email
    customer_name VARCHAR(100),   -- Transitive: id → customer_id → customer_name
    order_date DATE,
    total_amount DECIMAL
);
```

**Problem:** `customer_email` and `customer_name` depend on `customer_id`, not directly on `order.id`.

**✅ Good (In 3NF):**
```sql
CREATE TABLE customers (
    id UUID PRIMARY KEY,
    email VARCHAR(255),
    name VARCHAR(100)
);

CREATE TABLE orders (
    id UUID PRIMARY KEY,
    customer_id UUID REFERENCES customers(id),
    order_date DATE,
    total_amount DECIMAL
);
```

### Platform Compliance

Our platform achieves 3NF across all major tables. See detailed analysis in:
- [Address 3NF Normalization Analysis](./address_3nf_normalization_analysis.md)

---

## Platform-Specific Normalization Examples

### 1. User and Address Relationship ✅

**Current Design (3NF Compliant):**
```python
class User(models.Model):
    id = UUIDField(primary_key=True)
    email = EmailField(unique=True)
    first_name = CharField()
    last_name = CharField()
    # No address fields here

class Country(models.Model):
    code = CharField(primary_key=True)
    name = CharField()
    phone_code = CharField()
    currency_code = CharField()

class Address(models.Model):
    id = UUIDField(primary_key=True)
    user = ForeignKey(User)
    country_code = ForeignKey(Country)
    street_line1 = CharField()
    city = CharField()
    # All fields directly depend on id
```

**Why this is 3NF:**
- No transitive dependencies
- `country_code` references Country table (not storing country name in Address)
- All address attributes directly depend on address.id

### 2. Product and Category Relationship ✅

**Current Design (3NF Compliant):**
```python
class Category(models.Model):
    id = UUIDField(primary_key=True)
    name = CharField()
    parent = ForeignKey('self', null=True)

class Product(models.Model):
    id = UUIDField(primary_key=True)
    name = CharField()
    category = ForeignKey(Category)
    # Category details retrieved via foreign key
```

**Why this is 3NF:**
- Product doesn't store category name (would be transitive)
- Category hierarchy properly modeled with self-reference

### 3. Order and Product Relationship ✅

**Current Design (3NF Compliant):**
```python
class Order(models.Model):
    id = UUIDField(primary_key=True)
    user = ForeignKey(User)
    order_date = DateTimeField()
    # No product details stored here

class OrderItem(models.Model):
    id = UUIDField(primary_key=True)
    order = ForeignKey(Order)
    product = ForeignKey(Product)
    quantity = IntegerField()
    price_at_purchase = DecimalField()  # Snapshot
```

**Note on price_at_purchase:**
This is an intentional denormalization for historical accuracy. Product prices change over time, so we capture the price at the moment of purchase. This is acceptable and common in e-commerce systems.

---

## When to Denormalize (Intentional Exceptions)

While our platform targets 3NF, there are legitimate reasons to denormalize:

### 1. Historical Data (Snapshots)
**Example:** Order item prices
```python
class OrderItem(models.Model):
    product = ForeignKey(Product)
    price_at_purchase = DecimalField()  # Snapshot of product.price
```
**Reason:** Product prices change; we need historical accuracy.

### 2. Performance Optimization
**Example:** Cached aggregates
```python
class Product(models.Model):
    # ... other fields ...
    review_count = IntegerField(default=0)  # Cached count
    average_rating = DecimalField(default=0)  # Cached average
```
**Reason:** Frequently accessed calculations cached for performance.

### 3. Computed Fields
**Example:** Full name
```python
class User(models.Model):
    first_name = CharField()
    last_name = CharField()
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
```
**Reason:** Computed in application layer, not stored in database.

---

## Normalization Checklist

Use this checklist when designing new tables:

### 1NF Checklist
- [ ] All columns contain atomic values
- [ ] No repeating groups or arrays
- [ ] Each column has a unique name
- [ ] Primary key defined

### 2NF Checklist
- [ ] Table is in 1NF
- [ ] If composite primary key exists, check for partial dependencies
- [ ] All non-key attributes depend on the entire key

### 3NF Checklist
- [ ] Table is in 2NF
- [ ] No transitive dependencies (A → B → C)
- [ ] All non-key attributes directly depend on primary key
- [ ] Foreign keys used instead of duplicating data

### Additional Checks
- [ ] Unique constraints where appropriate
- [ ] Indexes on foreign keys
- [ ] Appropriate data types
- [ ] NULL vs NOT NULL properly defined

---

## Common Anti-Patterns to Avoid

### ❌ Anti-Pattern 1: Storing Derived Data
```python
# BAD
class Order(models.Model):
    subtotal = DecimalField()  # Sum of line items
    tax = DecimalField()       # Calculated from subtotal
    total = DecimalField()     # subtotal + tax
```

**Solution:** Calculate these on-the-fly or cache them separately.

### ❌ Anti-Pattern 2: Redundant Foreign Keys
```python
# BAD
class Address(models.Model):
    user = ForeignKey(User)
    contact_info = ForeignKey(ContactInfo)

class ContactInfo(models.Model):
    user = ForeignKey(User)  # Redundant!
```

**Problem:** Creates transitive dependency (violates 3NF).

### ❌ Anti-Pattern 3: Storing Lists in Single Column
```python
# BAD
class Product(models.Model):
    tags = CharField()  # "electronics,sale,featured"
```

**Solution:** Create a many-to-many relationship with a Tag table.

---

## Tools and Validation

### Django ORM Best Practices

1. **Use select_related() for foreign keys:**
```python
# Good: Single query with JOIN
addresses = Address.objects.select_related('country_code', 'user').all()
```

2. **Use prefetch_related() for reverse foreign keys:**
```python
# Good: Optimized queries
users = User.objects.prefetch_related('addresses').all()
```

3. **Avoid N+1 query problems:**
```python
# Bad: N+1 queries
for address in Address.objects.all():
    print(address.country_code.name)  # Separate query each time

# Good: Use select_related
for address in Address.objects.select_related('country_code').all():
    print(address.country_code.name)  # Already loaded
```

### Validation Tools

1. **Django's check framework:**
```bash
python manage.py check --database default
```

2. **Schema inspection:**
```bash
python manage.py inspectdb
```

3. **Migration validation:**
```bash
python manage.py makemigrations --dry-run --verbosity 3
```

---

## Further Reading

- [Address 3NF Normalization Analysis](./address_3nf_normalization_analysis.md) - Detailed analysis of address model design options
- [Schema SQL Files](./schema.sql) - Complete database schema
- [Normalized Schema](./schema_normalized.sql) - 3NF-compliant schema design

---

## Summary

Our e-commerce platform database is designed to:
- ✅ Achieve Third Normal Form (3NF) across all core tables
- ✅ Eliminate redundant data and transitive dependencies
- ✅ Use foreign keys appropriately to maintain referential integrity
- ✅ Make intentional, documented exceptions for performance and historical data
- ✅ Follow Django ORM best practices for efficient queries

**Key Principle:** Normalize until it hurts, denormalize until it works, but always document why.

---

*Last updated: 2026-02-07*
