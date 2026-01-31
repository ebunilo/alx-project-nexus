


-- Reference addresses by ID
CREATE TABLE orders (
    shipping_address_id UUID REFERENCES addresses(id),
    billing_address_id UUID REFERENCES addresses(id)
);


-- Variants reference base price with adjustments
CREATE TABLE product_variants (
    price_adjustment DECIMAL(10,2) -- +/- from base price
);



-- 1. Attribute Definitions (3NF)
CREATE TABLE attribute_definitions (
    id UUID PRIMARY KEY,
    name VARCHAR(100),
    slug VARCHAR(100) UNIQUE,
    data_type VARCHAR(20), -- text/number/boolean/select
    input_type VARCHAR(20), -- text/select/radio/color_picker
    is_filterable BOOLEAN DEFAULT false,
    is_required BOOLEAN DEFAULT false
);

-- 2. Predefined Values for Select Attributes (3NF)
CREATE TABLE attribute_values (
    id UUID PRIMARY KEY,
    attribute_id UUID REFERENCES attribute_definitions(id),
    value_text VARCHAR(255),
    value_number DECIMAL(10,2),
    value_boolean BOOLEAN,
    display_value VARCHAR(255),
    color_hex CHAR(7),
    sort_order INTEGER
);

-- 3. Product-Attribute Relationships (3NF)
CREATE TABLE product_attributes (
    id UUID PRIMARY KEY,
    product_id UUID REFERENCES products(id),
    attribute_id UUID REFERENCES attribute_definitions(id),
    attribute_value_id UUID REFERENCES attribute_values(id)
);



CREATE TABLE media (
    id UUID PRIMARY KEY,
    media_type VARCHAR(20), -- image/video/document
    original_filename VARCHAR(255),
    storage_path VARCHAR(500),
    mime_type VARCHAR(100),
    file_size_bytes INTEGER,
    alt_text VARCHAR(255),
    metadata JSONB
);

CREATE TABLE product_media (
    product_id UUID REFERENCES products(id),
    media_id UUID REFERENCES media(id),
    media_role VARCHAR(20) -- main/gallery/thumbnail
);


-- Remove calculated fields, compute on demand or cache separately
CREATE TABLE carts (
    -- No calculated totals stored
);

-- Use views or materialized views for aggregates
CREATE VIEW product_ratings AS
SELECT
    product_id,
    AVG(rating) as average_rating,
    COUNT(*) as review_count
FROM product_reviews
WHERE moderation_status = 'approved'
GROUP BY product_id;


-- ============================================
-- COUNTRY REFERENCE TABLE (3NF)
-- ============================================
CREATE TABLE countries (
    code CHAR(2) PRIMARY KEY, -- ISO 3166-1 alpha-2
    name VARCHAR(100) NOT NULL,
    phone_code VARCHAR(10),
    currency_code CHAR(3),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- NORMALIZED ADDRESS TABLE (3NF)
-- ============================================
CREATE TABLE addresses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    address_type VARCHAR(20) NOT NULL CHECK (
        address_type IN ('home', 'work', 'billing', 'shipping')
    ),
    contact_name VARCHAR(255),
    phone VARCHAR(50),
    street_line1 VARCHAR(255) NOT NULL,
    street_line2 VARCHAR(255),
    city VARCHAR(100) NOT NULL,
    state_province VARCHAR(100),
    postal_code VARCHAR(20) NOT NULL,
    country_code CHAR(2) REFERENCES countries(code),
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_country_code FOREIGN KEY (country_code)
        REFERENCES countries(code)
);

-- Indexes for address queries
CREATE INDEX idx_addresses_user ON addresses(user_id);
CREATE INDEX idx_addresses_user_type ON addresses(user_id, address_type);
CREATE INDEX idx_addresses_country ON addresses(country_code);

-- ============================================
-- ATTRIBUTE SYSTEM (EAV - 3NF)
-- ============================================
CREATE TABLE attribute_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(100),
    data_type VARCHAR(20) NOT NULL CHECK (
        data_type IN ('text', 'number', 'boolean', 'select', 'color')
    ),
    input_type VARCHAR(20) NOT NULL CHECK (
        input_type IN ('text', 'select', 'radio', 'checkbox', 'color_picker')
    ),
    is_filterable BOOLEAN DEFAULT false,
    is_required BOOLEAN DEFAULT false,
    is_variant_attribute BOOLEAN DEFAULT false,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE attribute_values (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    attribute_id UUID NOT NULL REFERENCES attribute_definitions(id)
        ON DELETE CASCADE,
    value_text VARCHAR(255),
    value_number DECIMAL(10,2),
    value_boolean BOOLEAN,
    display_value VARCHAR(255),
    color_hex CHAR(7), -- #RRGGBB format
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Ensure only one value type is set based on attribute data_type
    CONSTRAINT chk_value_type CHECK (
        (value_text IS NOT NULL AND value_number IS NULL AND value_boolean IS NULL) OR
        (value_text IS NULL AND value_number IS NOT NULL AND value_boolean IS NULL) OR
        (value_text IS NULL AND value_number IS NULL AND value_boolean IS NOT NULL)
    )
);

CREATE TABLE product_attributes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    attribute_id UUID NOT NULL REFERENCES attribute_definitions(id),
    attribute_value_id UUID NOT NULL REFERENCES attribute_values(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(product_id, attribute_id),

    CONSTRAINT fk_attribute_value_type CHECK (
        EXISTS (
            SELECT 1 FROM attribute_values av
            JOIN attribute_definitions ad ON av.attribute_id = ad.id
            WHERE av.id = attribute_value_id
            AND ad.id = attribute_id
        )
    )
);

-- ============================================
-- PRICE HISTORY (3NF - Time-based)
-- ============================================
CREATE TABLE product_prices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    sale_price DECIMAL(10,2) NOT NULL CHECK (sale_price >= 0),
    compare_at_price DECIMAL(10,2) CHECK (compare_at_price >= 0),
    cost_price DECIMAL(10,2) CHECK (cost_price >= 0),
    effective_from DATE NOT NULL,
    effective_to DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CHECK (effective_to IS NULL OR effective_to > effective_from),

    -- Ensure no overlapping price periods for same product
    EXCLUDE USING gist (
        product_id WITH =,
        daterange(effective_from, effective_to, '[]') WITH &&
    )
);

-- Function to get current price
CREATE OR REPLACE FUNCTION get_current_product_price(product_uuid UUID)
RETURNS DECIMAL AS $$
DECLARE
    current_price DECIMAL;
BEGIN
    SELECT sale_price INTO current_price
    FROM product_prices
    WHERE product_id = product_uuid
    AND effective_from <= CURRENT_DATE
    AND (effective_to IS NULL OR effective_to >= CURRENT_DATE)
    ORDER BY effective_from DESC
    LIMIT 1;

    RETURN COALESCE(current_price, 0);
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- INVENTORY MANAGEMENT (3NF)
-- ============================================
CREATE TABLE warehouses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    address_id UUID REFERENCES addresses(id),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE product_inventory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    warehouse_id UUID NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
    available_quantity INTEGER NOT NULL DEFAULT 0 CHECK (available_quantity >= 0),
    reserved_quantity INTEGER NOT NULL DEFAULT 0 CHECK (reserved_quantity >= 0),
    low_stock_threshold INTEGER DEFAULT 10,
    last_counted TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(product_id, warehouse_id),

    -- Computed column (virtual)
    total_quantity INTEGER GENERATED ALWAYS AS
        (available_quantity + reserved_quantity) STORED
);

-- ============================================
-- VIEWS FOR DENORMALIZED DATA ACCESS
-- ============================================

-- Product catalog view with current prices
CREATE VIEW product_catalog AS
SELECT
    p.id,
    p.name,
    p.slug,
    p.sku,
    c.name as category_name,
    b.name as brand_name,
    COALESCE(pp.sale_price, 0) as current_price,
    pp.compare_at_price,
    SUM(pi.available_quantity) as total_stock,
    EXISTS (
        SELECT 1 FROM product_reviews pr
        WHERE pr.product_id = p.id
        AND pr.moderation_status = 'approved'
    ) as has_reviews
FROM products p
LEFT JOIN categories c ON p.category_id = c.id
LEFT JOIN brands b ON p.brand_id = b.id
LEFT JOIN product_prices pp ON p.id = pp.product_id
    AND pp.effective_from <= CURRENT_DATE
    AND (pp.effective_to IS NULL OR pp.effective_to >= CURRENT_DATE)
LEFT JOIN product_inventory pi ON p.id = pi.product_id
WHERE p.is_published = true
GROUP BY p.id, c.name, b.name, pp.sale_price, pp.compare_at_price;

-- Order summary view
CREATE VIEW order_summary AS
SELECT
    o.id,
    o.order_number,
    o.placed_at,
    u.email as customer_email,
    os.name as status,
    o.grand_total,
    COUNT(oi.id) as item_count,
    SUM(oi.quantity) as total_quantity
FROM orders o
JOIN users u ON o.user_id = u.id
JOIN order_statuses os ON o.order_status = os.code
LEFT JOIN order_items oi ON o.id = oi.order_id
GROUP BY o.id, u.email, os.name;

