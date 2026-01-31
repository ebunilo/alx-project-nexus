-- Complete SQL CREATE TABLE Statements with Optimization

-- 1. Core User Management Tables**


-- ============================================
-- USER MANAGEMENT TABLES
-- ============================================

-- Countries reference table
CREATE TABLE countries (
    code CHAR(2) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone_code VARCHAR(10),
    currency_code CHAR(3),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_country_name UNIQUE (name),
    CONSTRAINT chk_country_code CHECK (code ~ '^[A-Z]{2}$')
);

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    is_staff BOOLEAN DEFAULT false,
    is_superuser BOOLEAN DEFAULT false,
    email_verified_at TIMESTAMP WITH TIME ZONE,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_user_email UNIQUE (email),
    CONSTRAINT chk_user_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'),
    CONSTRAINT chk_user_names CHECK (
        first_name ~ '^[A-Za-z\\s''-]+$' AND
        last_name ~ '^[A-Za-z\\s''-]+$'
    )
);

-- Indexes for users
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_is_active ON users(is_active) WHERE is_active = true;
CREATE INDEX idx_users_created_at ON users(created_at DESC);
CREATE INDEX idx_users_last_login ON users(last_login DESC) WHERE last_login IS NOT NULL;

-- Addresses table
CREATE TABLE addresses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    address_type VARCHAR(20) NOT NULL,
    contact_name VARCHAR(255),
    phone VARCHAR(50),
    street_line1 VARCHAR(255) NOT NULL,
    street_line2 VARCHAR(255),
    city VARCHAR(100) NOT NULL,
    state_province VARCHAR(100),
    postal_code VARCHAR(20) NOT NULL,
    country_code CHAR(2) NOT NULL,
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_addresses_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_addresses_country FOREIGN KEY (country_code)
        REFERENCES countries(code),
    CONSTRAINT chk_address_type CHECK (
        address_type IN ('home', 'work', 'billing', 'shipping')
    ),
    CONSTRAINT chk_address_phone CHECK (
        phone IS NULL OR phone ~ '^\\+?[1-9]\\d{1,14}$'
    )
);

-- Indexes for addresses
CREATE INDEX idx_addresses_user_id ON addresses(user_id);
CREATE INDEX idx_addresses_user_type ON addresses(user_id, address_type);
CREATE INDEX idx_addresses_country ON addresses(country_code);
CREATE INDEX idx_addresses_city ON addresses(city);
CREATE INDEX idx_addresses_default ON addresses(user_id, is_default) WHERE is_default = true;



## **2. Product Catalog Tables**


-- ============================================
-- PRODUCT CATALOG TABLES
-- ============================================

-- Brands table
CREATE TABLE brands (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL,
    description TEXT,
    logo_url VARCHAR(500),
    website_url VARCHAR(500),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_brand_name UNIQUE (name),
    CONSTRAINT uq_brand_slug UNIQUE (slug),
    CONSTRAINT chk_brand_slug CHECK (slug ~ '^[a-z0-9]+(?:-[a-z0-9]+)*$')
);

-- Categories table with closure table pattern for hierarchies
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL,
    description TEXT,
    parent_id UUID,
    depth_level INTEGER DEFAULT 0,
    path VARCHAR(1000), -- Materialized path for fast queries
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_category_slug UNIQUE (slug),
    CONSTRAINT fk_categories_parent FOREIGN KEY (parent_id)
        REFERENCES categories(id) ON DELETE SET NULL,
    CONSTRAINT chk_category_slug CHECK (slug ~ '^[a-z0-9]+(?:-[a-z0-9]+)*$'),
    CONSTRAINT chk_depth_level CHECK (depth_level >= 0)
);

-- Category closure table for efficient hierarchy queries
CREATE TABLE category_hierarchy (
    ancestor_id UUID NOT NULL,
    descendant_id UUID NOT NULL,
    depth INTEGER NOT NULL,

    PRIMARY KEY (ancestor_id, descendant_id),
    CONSTRAINT fk_hierarchy_ancestor FOREIGN KEY (ancestor_id)
        REFERENCES categories(id) ON DELETE CASCADE,
    CONSTRAINT fk_hierarchy_descendant FOREIGN KEY (descendant_id)
        REFERENCES categories(id) ON DELETE CASCADE,
    CONSTRAINT chk_hierarchy_depth CHECK (depth >= 0)
);

-- Products table
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL,
    short_description TEXT,
    long_description TEXT,
    sku VARCHAR(100) NOT NULL,
    category_id UUID NOT NULL,
    brand_id UUID,
    weight_grams DECIMAL(10,2),
    is_published BOOLEAN DEFAULT false,
    is_featured BOOLEAN DEFAULT false,
    is_digital BOOLEAN DEFAULT false,
    requires_shipping BOOLEAN DEFAULT true,
    has_variants BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT uq_product_slug UNIQUE (slug),
    CONSTRAINT uq_product_sku UNIQUE (sku),
    CONSTRAINT fk_products_category FOREIGN KEY (category_id)
        REFERENCES categories(id),
    CONSTRAINT fk_products_brand FOREIGN KEY (brand_id)
        REFERENCES brands(id) ON DELETE SET NULL,
    CONSTRAINT chk_product_slug CHECK (slug ~ '^[a-z0-9]+(?:-[a-z0-9]+)*$'),
    CONSTRAINT chk_product_weight CHECK (weight_grams >= 0),
    CONSTRAINT chk_published_dates CHECK (
        (is_published = false AND published_at IS NULL) OR
        (is_published = true AND published_at IS NOT NULL)
    )
);

-- Product dimensions table
CREATE TABLE product_dimensions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL,
    length_cm DECIMAL(10,2),
    width_cm DECIMAL(10,2),
    height_cm DECIMAL(10,2),
    dimension_unit VARCHAR(10) DEFAULT 'cm',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_dimensions_product FOREIGN KEY (product_id)
        REFERENCES products(id) ON DELETE CASCADE,
    CONSTRAINT chk_positive_dimensions CHECK (
        (length_cm IS NULL OR length_cm > 0) AND
        (width_cm IS NULL OR width_cm > 0) AND
        (height_cm IS NULL OR height_cm > 0)
    )
);

-- Indexes for products
CREATE INDEX idx_products_slug ON products(slug);
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_brand ON products(brand_id);
CREATE INDEX idx_products_published ON products(is_published, published_at DESC)
    WHERE is_published = true;
CREATE INDEX idx_products_featured ON products(is_featured, published_at DESC)
    WHERE is_featured = true AND is_published = true;
CREATE INDEX idx_products_created ON products(created_at DESC);
CREATE INDEX idx_products_search ON products USING gin(
    to_tsvector('english',
        coalesce(name, '') || ' ' ||
        coalesce(short_description, '') || ' ' ||
        coalesce(sku, '')
    )
);



## **3. Attribute Management Tables (EAV Pattern)**


-- ============================================
-- ATTRIBUTE MANAGEMENT TABLES
-- ============================================

-- Attribute definitions
CREATE TABLE attribute_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    display_name VARCHAR(100),
    data_type VARCHAR(20) NOT NULL,
    input_type VARCHAR(20) NOT NULL,
    is_filterable BOOLEAN DEFAULT false,
    is_required BOOLEAN DEFAULT false,
    is_variant_attribute BOOLEAN DEFAULT false,
    is_searchable BOOLEAN DEFAULT false,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_attribute_slug UNIQUE (slug),
    CONSTRAINT chk_attribute_data_type CHECK (
        data_type IN ('text', 'number', 'boolean', 'select', 'color', 'date')
    ),
    CONSTRAINT chk_attribute_input_type CHECK (
        input_type IN ('text', 'textarea', 'select', 'radio', 'checkbox', 'color_picker', 'date_picker')
    )
);

-- Attribute values (predefined for select attributes)
CREATE TABLE attribute_values (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    attribute_id UUID NOT NULL,
    value_text VARCHAR(255),
    value_number DECIMAL(10,2),
    value_boolean BOOLEAN,
    display_value VARCHAR(255),
    color_hex CHAR(7),
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_attribute_values_attribute FOREIGN KEY (attribute_id)
        REFERENCES attribute_definitions(id) ON DELETE CASCADE,
    CONSTRAINT chk_attribute_value_type CHECK (
        -- Ensure only one value field is populated based on attribute type
        CASE
            WHEN (SELECT data_type FROM attribute_definitions WHERE id = attribute_id) = 'text'
                THEN value_text IS NOT NULL AND value_number IS NULL AND value_boolean IS NULL
            WHEN (SELECT data_type FROM attribute_definitions WHERE id = attribute_id) = 'number'
                THEN value_number IS NOT NULL AND value_text IS NULL AND value_boolean IS NULL
            WHEN (SELECT data_type FROM attribute_definitions WHERE id = attribute_id) = 'boolean'
                THEN value_boolean IS NOT NULL AND value_text IS NULL AND value_number IS NULL
            WHEN (SELECT data_type FROM attribute_definitions WHERE id = attribute_id) IN ('select', 'color')
                THEN value_text IS NOT NULL AND value_number IS NULL AND value_boolean IS NULL
            ELSE true
        END
    ),
    CONSTRAINT chk_color_hex CHECK (
        color_hex IS NULL OR color_hex ~ '^#[0-9A-Fa-f]{6}$'
    )
);

-- Product attributes (EAV)
CREATE TABLE product_attributes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL,
    attribute_id UUID NOT NULL,
    attribute_value_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_product_attributes_product FOREIGN KEY (product_id)
        REFERENCES products(id) ON DELETE CASCADE,
    CONSTRAINT fk_product_attributes_attribute FOREIGN KEY (attribute_id)
        REFERENCES attribute_definitions(id),
    CONSTRAINT fk_product_attributes_value FOREIGN KEY (attribute_value_id)
        REFERENCES attribute_values(id),
    CONSTRAINT uq_product_attribute UNIQUE (product_id, attribute_id),

    -- Ensure attribute value matches attribute definition
    CONSTRAINT chk_attribute_value_match CHECK (
        EXISTS (
            SELECT 1 FROM attribute_values av
            JOIN attribute_definitions ad ON av.attribute_id = ad.id
            WHERE av.id = attribute_value_id
            AND ad.id = attribute_id
        )
    )
);

-- Indexes for attribute system
CREATE INDEX idx_attribute_definitions_slug ON attribute_definitions(slug);
CREATE INDEX idx_attribute_definitions_filterable ON attribute_definitions(is_filterable)
    WHERE is_filterable = true;
CREATE INDEX idx_attribute_values_attribute ON attribute_values(attribute_id);
CREATE INDEX idx_attribute_values_sort ON attribute_values(attribute_id, sort_order);
CREATE INDEX idx_product_attributes_product ON product_attributes(product_id);
CREATE INDEX idx_product_attributes_attribute ON product_attributes(attribute_id);
CREATE INDEX idx_product_attributes_value ON product_attributes(attribute_value_id);



## **4. Product Variants & Pricing Tables**


-- ============================================
-- PRODUCT VARIANTS & PRICING
-- ============================================

-- Product variants
CREATE TABLE product_variants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL,
    sku VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    price_adjustment DECIMAL(10,2) DEFAULT 0,
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_variants_product FOREIGN KEY (product_id)
        REFERENCES products(id) ON DELETE CASCADE,
    CONSTRAINT uq_variant_sku UNIQUE (sku),
    CONSTRAINT uq_product_default_variant UNIQUE (product_id, is_default)
        WHERE is_default = true,
    CONSTRAINT chk_variant_sku CHECK (sku ~ '^[A-Z0-9-]+$')
);

-- Variant attributes
CREATE TABLE variant_attributes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    variant_id UUID NOT NULL,
    attribute_id UUID NOT NULL,
    attribute_value_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_variant_attributes_variant FOREIGN KEY (variant_id)
        REFERENCES product_variants(id) ON DELETE CASCADE,
    CONSTRAINT fk_variant_attributes_attribute FOREIGN KEY (attribute_id)
        REFERENCES attribute_definitions(id),
    CONSTRAINT fk_variant_attributes_value FOREIGN KEY (attribute_value_id)
        REFERENCES attribute_values(id),
    CONSTRAINT uq_variant_attribute UNIQUE (variant_id, attribute_id)
);

-- Product prices with time validity
CREATE TABLE product_prices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL,
    sale_price DECIMAL(10,2) NOT NULL,
    compare_at_price DECIMAL(10,2),
    cost_price DECIMAL(10,2),
    effective_from DATE NOT NULL,
    effective_to DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_product_prices_product FOREIGN KEY (product_id)
        REFERENCES products(id) ON DELETE CASCADE,
    CONSTRAINT chk_product_prices CHECK (
        sale_price >= 0 AND
        (compare_at_price IS NULL OR compare_at_price >= 0) AND
        (cost_price IS NULL OR cost_price >= 0) AND
        (effective_to IS NULL OR effective_to > effective_from)
    ),
    -- Prevent overlapping price periods for same product
    EXCLUDE USING gist (
        product_id WITH =,
        daterange(effective_from, effective_to, '[]') WITH &&
    )
);

-- Currency table
CREATE TABLE currencies (
    code CHAR(3) PRIMARY KEY, -- ISO 4217
    name VARCHAR(100) NOT NULL,
    symbol VARCHAR(10),
    exchange_rate_to_usd DECIMAL(12,6) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    rate_updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_currency_code CHECK (code ~ '^[A-Z]{3}$'),
    CONSTRAINT chk_exchange_rate CHECK (exchange_rate_to_usd > 0)
);

-- Indexes for variants and pricing
CREATE INDEX idx_product_variants_product ON product_variants(product_id);
CREATE INDEX idx_product_variants_sku ON product_variants(sku);
CREATE INDEX idx_product_variants_default ON product_variants(product_id, is_default)
    WHERE is_default = true;
CREATE INDEX idx_variant_attributes_variant ON variant_attributes(variant_id);
CREATE INDEX idx_product_prices_product ON product_prices(product_id);
CREATE INDEX idx_product_prices_current ON product_prices(product_id, effective_from DESC)
    WHERE effective_from <= CURRENT_DATE AND (effective_to IS NULL OR effective_to >= CURRENT_DATE);
CREATE INDEX idx_product_prices_range ON product_prices USING gist (
    product_id,
    daterange(effective_from, effective_to, '[]')
);



## **5. Media Management Tables**


-- ============================================
-- MEDIA MANAGEMENT TABLES
-- ============================================

-- Media registry
CREATE TABLE media (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    media_type VARCHAR(20) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    storage_path VARCHAR(500) NOT NULL,
    mime_type VARCHAR(100),
    file_size_bytes INTEGER,
    width_px INTEGER,
    height_px INTEGER,
    duration_seconds INTEGER, -- For videos
    alt_text VARCHAR(255),
    metadata JSONB,
    uploaded_by UUID,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_media_uploaded_by FOREIGN KEY (uploaded_by)
        REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT chk_media_type CHECK (
        media_type IN ('image', 'video', 'document', 'audio')
    ),
    CONSTRAINT chk_media_size CHECK (file_size_bytes > 0),
    CONSTRAINT chk_media_dimensions CHECK (
        (media_type != 'image' OR (width_px IS NOT NULL AND height_px IS NOT NULL)) AND
        (media_type != 'video' OR duration_seconds IS NOT NULL)
    )
);

-- Product media
CREATE TABLE product_media (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL,
    media_id UUID NOT NULL,
    media_role VARCHAR(20) NOT NULL,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_product_media_product FOREIGN KEY (product_id)
        REFERENCES products(id) ON DELETE CASCADE,
    CONSTRAINT fk_product_media_media FOREIGN KEY (media_id)
        REFERENCES media(id) ON DELETE CASCADE,
    CONSTRAINT uq_product_main_image UNIQUE (product_id, media_role)
        WHERE media_role = 'main',
    CONSTRAINT chk_media_role CHECK (
        media_role IN ('main', 'gallery', 'thumbnail', 'document')
    )
);

-- Indexes for media
CREATE INDEX idx_media_type ON media(media_type);
CREATE INDEX idx_media_uploaded_at ON media(uploaded_at DESC);
CREATE INDEX idx_media_uploaded_by ON media(uploaded_by);
CREATE INDEX idx_product_media_product ON product_media(product_id);
CREATE INDEX idx_product_media_role ON product_media(product_id, media_role);
CREATE INDEX idx_product_media_sort ON product_media(product_id, sort_order);



## **6. Order Management Tables**


-- ============================================
-- ORDER MANAGEMENT TABLES
-- ============================================

-- Order statuses
CREATE TABLE order_statuses (
    code VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    sort_order INTEGER DEFAULT 0,
    is_terminal BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_status_code CHECK (code ~ '^[a-z_]+$')
);

INSERT INTO order_statuses (code, name, description, sort_order, is_terminal) VALUES
    ('pending', 'Pending', 'Order placed, awaiting payment', 1, false),
    ('processing', 'Processing', 'Payment confirmed, preparing order', 2, false),
    ('shipped', 'Shipped', 'Order shipped to customer', 3, false),
    ('delivered', 'Delivered', 'Order delivered successfully', 4, true),
    ('cancelled', 'Cancelled', 'Order cancelled', 5, true),
    ('refunded', 'Refunded', 'Order refunded', 6, true),
    ('failed', 'Failed', 'Payment failed', 7, true);

-- Orders table
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number VARCHAR(50) NOT NULL,
    user_id UUID NOT NULL,
    shipping_address_id UUID NOT NULL,
    billing_address_id UUID NOT NULL,
    order_status VARCHAR(50) NOT NULL DEFAULT 'pending',
    items_subtotal DECIMAL(10,2) NOT NULL DEFAULT 0,
    shipping_total DECIMAL(10,2) NOT NULL DEFAULT 0,
    tax_total DECIMAL(10,2) NOT NULL DEFAULT 0,
    discount_total DECIMAL(10,2) NOT NULL DEFAULT 0,
    grand_total DECIMAL(10,2) NOT NULL DEFAULT 0,
    currency_code CHAR(3) NOT NULL DEFAULT 'USD',
    notes TEXT,
    placed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_order_number UNIQUE (order_number),
    CONSTRAINT fk_orders_user FOREIGN KEY (user_id)
        REFERENCES users(id),
    CONSTRAINT fk_orders_shipping_address FOREIGN KEY (shipping_address_id)
        REFERENCES addresses(id),
    CONSTRAINT fk_orders_billing_address FOREIGN KEY (billing_address_id)
        REFERENCES addresses(id),
    CONSTRAINT fk_orders_status FOREIGN KEY (order_status)
        REFERENCES order_statuses(code),
    CONSTRAINT fk_orders_currency FOREIGN KEY (currency_code)
        REFERENCES currencies(code),
    CONSTRAINT chk_order_totals CHECK (
        grand_total = items_subtotal + shipping_total + tax_total - discount_total AND
        items_subtotal >= 0 AND
        shipping_total >= 0 AND
        tax_total >= 0 AND
        discount_total >= 0 AND
        grand_total >= 0
    ),
    CONSTRAINT chk_order_dates CHECK (
        (placed_at IS NULL AND order_status = 'pending') OR
        (placed_at IS NOT NULL)
    )
);

-- Order items table
CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL,
    product_id UUID NOT NULL,
    variant_id UUID,
    product_name VARCHAR(255) NOT NULL,
    sku VARCHAR(100) NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    attributes JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_order_items_order FOREIGN KEY (order_id)
        REFERENCES orders(id) ON DELETE CASCADE,
    CONSTRAINT fk_order_items_product FOREIGN KEY (product_id)
        REFERENCES products(id),
    CONSTRAINT fk_order_items_variant FOREIGN KEY (variant_id)
        REFERENCES product_variants(id),
    CONSTRAINT chk_order_item_quantity CHECK (quantity > 0),
    CONSTRAINT chk_order_item_prices CHECK (
        unit_price >= 0 AND
        total_price >= 0 AND
        total_price = unit_price * quantity
    )
);

-- Order status history
CREATE TABLE order_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL,
    status VARCHAR(50) NOT NULL,
    notes TEXT,
    changed_by UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_status_history_order FOREIGN KEY (order_id)
        REFERENCES orders(id) ON DELETE CASCADE,
    CONSTRAINT fk_status_history_status FOREIGN KEY (status)
        REFERENCES order_statuses(code),
    CONSTRAINT fk_status_history_changed_by FOREIGN KEY (changed_by)
        REFERENCES users(id) ON DELETE SET NULL
);

-- Indexes for orders
CREATE INDEX idx_orders_order_number ON orders(order_number);
CREATE INDEX idx_orders_user ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(order_status);
CREATE INDEX idx_orders_placed_at ON orders(placed_at DESC) WHERE placed_at IS NOT NULL;
CREATE INDEX idx_orders_created_at ON orders(created_at DESC);
CREATE INDEX idx_orders_total ON orders(grand_total DESC);
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);
CREATE INDEX idx_order_items_sku ON order_items(sku);
CREATE INDEX idx_order_status_history_order ON order_status_history(order_id);
CREATE INDEX idx_order_status_history_created ON order_status_history(created_at DESC);



## **7. Payment & Shipping Tables**


-- ============================================
-- PAYMENT & SHIPPING TABLES
-- ============================================

-- Payment methods
CREATE TABLE payment_methods (
    code VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO payment_methods (code, name, description) VALUES
    ('card', 'Credit/Debit Card', 'Pay with Visa, Mastercard, etc.'),
    ('bank_transfer', 'Bank Transfer', 'Direct bank transfer'),
    ('mobile_money', 'Mobile Money', 'Mobile money payment'),
    ('cash', 'Cash on Delivery', 'Pay when you receive order');

-- Payment statuses
CREATE TABLE payment_statuses (
    code VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO payment_statuses (code, name, description, sort_order) VALUES
    ('pending', 'Pending', 'Payment initiated', 1),
    ('processing', 'Processing', 'Payment being processed', 2),
    ('completed', 'Completed', 'Payment successful', 3),
    ('failed', 'Failed', 'Payment failed', 4),
    ('refunded', 'Refunded', 'Payment refunded', 5),
    ('cancelled', 'Cancelled', 'Payment cancelled', 6);

-- Payments table
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL,
    gateway VARCHAR(50) NOT NULL,
    gateway_transaction_id VARCHAR(255),
    reference VARCHAR(100) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency_code CHAR(3) NOT NULL,
    payment_method_code VARCHAR(50) NOT NULL,
    payment_status VARCHAR(50) NOT NULL DEFAULT 'pending',
    gateway_response JSONB,
    paid_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_payment_reference UNIQUE (reference),
    CONSTRAINT fk_payments_order FOREIGN KEY (order_id)
        REFERENCES orders(id),
    CONSTRAINT fk_payments_currency FOREIGN KEY (currency_code)
        REFERENCES currencies(code),
    CONSTRAINT fk_payments_method FOREIGN KEY (payment_method_code)
        REFERENCES payment_methods(code),
    CONSTRAINT fk_payments_status FOREIGN KEY (payment_status)
        REFERENCES payment_statuses(code),
    CONSTRAINT chk_payment_amount CHECK (amount > 0),
    CONSTRAINT chk_payment_dates CHECK (
        (paid_at IS NULL AND payment_status IN ('pending', 'processing', 'failed')) OR
        (paid_at IS NOT NULL AND payment_status IN ('completed', 'refunded', 'cancelled'))
    )
);

-- Payment status history
CREATE TABLE payment_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id UUID NOT NULL,
    status VARCHAR(50) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_payment_status_history_payment FOREIGN KEY (payment_id)
        REFERENCES payments(id) ON DELETE CASCADE,
    CONSTRAINT fk_payment_status_history_status FOREIGN KEY (status)
        REFERENCES payment_statuses(code)
);

-- Refunds table
CREATE TABLE refunds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id UUID NOT NULL,
    reference VARCHAR(100) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    reason TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    gateway_response JSONB,
    processed_by UUID,
    processed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_refund_reference UNIQUE (reference),
    CONSTRAINT fk_refunds_payment FOREIGN KEY (payment_id)
        REFERENCES payments(id),
    CONSTRAINT fk_refunds_processed_by FOREIGN KEY (processed_by)
        REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT chk_refund_amount CHECK (amount > 0),
    CONSTRAINT chk_refund_max_amount CHECK (
        amount <= (SELECT amount FROM payments WHERE id = payment_id)
    )
);

-- Shipping methods
CREATE TABLE shipping_methods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) NOT NULL,
    carrier VARCHAR(100),
    base_cost DECIMAL(10,2) NOT NULL DEFAULT 0,
    cost_per_kg DECIMAL(10,2) DEFAULT 0,
    free_shipping_threshold DECIMAL(10,2),
    estimated_days_min INTEGER,
    estimated_days_max INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_shipping_method_code UNIQUE (code),
    CONSTRAINT chk_shipping_costs CHECK (
        base_cost >= 0 AND
        (cost_per_kg IS NULL OR cost_per_kg >= 0) AND
        (free_shipping_threshold IS NULL OR free_shipping_threshold >= 0)
    ),
    CONSTRAINT chk_estimated_days CHECK (
        estimated_days_min >= 0 AND
        estimated_days_max >= estimated_days_min
    )
);

-- Order shipments
CREATE TABLE order_shipments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL,
    shipping_method_id UUID NOT NULL,
    tracking_number VARCHAR(100),
    carrier VARCHAR(100),
    tracking_url VARCHAR(500),
    shipped_at TIMESTAMP WITH TIME ZONE,
    estimated_delivery TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_order_shipments_order FOREIGN KEY (order_id)
        REFERENCES orders(id),
    CONSTRAINT fk_order_shipments_method FOREIGN KEY (shipping_method_id)
        REFERENCES shipping_methods(id),
    CONSTRAINT uq_shipment_tracking UNIQUE (tracking_number)
        WHERE tracking_number IS NOT NULL,
    CONSTRAINT chk_shipment_dates CHECK (
        (shipped_at IS NULL AND delivered_at IS NULL) OR
        (shipped_at IS NOT NULL AND (delivered_at IS NULL OR delivered_at >= shipped_at))
    )
);

-- Indexes for payments and shipping
CREATE INDEX idx_payments_order ON payments(order_id);
CREATE INDEX idx_payments_reference ON payments(reference);
CREATE INDEX idx_payments_status ON payments(payment_status);
CREATE INDEX idx_payments_paid_at ON payments(paid_at DESC) WHERE paid_at IS NOT NULL;
CREATE INDEX idx_payment_status_history_payment ON payment_status_history(payment_id);
CREATE INDEX idx_refunds_payment ON refunds(payment_id);
CREATE INDEX idx_refunds_status ON refunds(status);
CREATE INDEX idx_shipping_methods_active ON shipping_methods(is_active)
    WHERE is_active = true;
CREATE INDEX idx_order_shipments_order ON order_shipments(order_id);
CREATE INDEX idx_order_shipments_tracking ON order_shipments(tracking_number)
    WHERE tracking_number IS NOT NULL;



## **8. Reviews & Ratings Tables**


-- ============================================
-- REVIEWS & RATINGS TABLES
-- ============================================

-- Product reviews
CREATE TABLE product_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL,
    user_id UUID NOT NULL,
    order_item_id UUID,
    rating INTEGER NOT NULL,
    title VARCHAR(200),
    comment TEXT NOT NULL,
    pros JSONB,
    cons JSONB,
    moderation_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    helpful_votes INTEGER DEFAULT 0,
    unhelpful_votes INTEGER DEFAULT 0,
    is_verified_purchase BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_product_reviews_product FOREIGN KEY (product_id)
        REFERENCES products(id) ON DELETE CASCADE,
    CONSTRAINT fk_product_reviews_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_product_reviews_order_item FOREIGN KEY (order_item_id)
        REFERENCES order_items(id),
    CONSTRAINT uq_user_product_review UNIQUE (product_id, user_id),
    CONSTRAINT chk_review_rating CHECK (rating >= 1 AND rating <= 5),
    CONSTRAINT chk_moderation_status CHECK (
        moderation_status IN ('pending', 'approved', 'rejected', 'flagged')
    ),
    CONSTRAINT chk_verified_purchase CHECK (
        (is_verified_purchase = true AND order_item_id IS NOT NULL) OR
        (is_verified_purchase = false)
    )
);

-- Review media
CREATE TABLE review_media (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID NOT NULL,
    media_id UUID NOT NULL,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_review_media_review FOREIGN KEY (review_id)
        REFERENCES product_reviews(id) ON DELETE CASCADE,
    CONSTRAINT fk_review_media_media FOREIGN KEY (media_id)
        REFERENCES media(id) ON DELETE CASCADE
);

-- Review votes
CREATE TABLE review_votes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID NOT NULL,
    user_id UUID NOT NULL,
    is_helpful BOOLEAN NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_review_votes_review FOREIGN KEY (review_id)
        REFERENCES product_reviews(id) ON DELETE CASCADE,
    CONSTRAINT fk_review_votes_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT uq_user_review_vote UNIQUE (review_id, user_id)
);

-- Indexes for reviews
CREATE INDEX idx_product_reviews_product ON product_reviews(product_id);
CREATE INDEX idx_product_reviews_user ON product_reviews(user_id);
CREATE INDEX idx_product_reviews_rating ON product_reviews(rating);
CREATE INDEX idx_product_reviews_moderation ON product_reviews(moderation_status)
    WHERE moderation_status = 'approved';
CREATE INDEX idx_product_reviews_created ON product_reviews(created_at DESC);
CREATE INDEX idx_product_reviews_product_rating ON product_reviews(product_id, rating DESC)
    WHERE moderation_status = 'approved';
CREATE INDEX idx_review_media_review ON review_media(review_id);
CREATE INDEX idx_review_votes_review ON review_votes(review_id);
CREATE INDEX idx_review_votes_user ON review_votes(user_id);
CREATE INDEX idx_review_votes_helpful ON review_votes(review_id, is_helpful)
    WHERE is_helpful = true;



## **9. Inventory & Warehouse Tables**


-- ============================================
-- INVENTORY & WAREHOUSE TABLES
-- ============================================

-- Warehouses
CREATE TABLE warehouses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) NOT NULL,
    address_id UUID NOT NULL,
    contact_name VARCHAR(255),
    contact_phone VARCHAR(50),
    contact_email VARCHAR(255),
    is_active BOOLEAN
