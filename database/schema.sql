-- Amazon Deals Scraper Database Schema
-- PostgreSQL 15+
-- Date: November 21, 2025

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- PRODUCTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    product_id VARCHAR(20) UNIQUE NOT NULL,  -- Amazon ASIN
    title TEXT NOT NULL,
    brand VARCHAR(255),
    category VARCHAR(100) NOT NULL,
    current_price DECIMAL(10, 2),
    original_price DECIMAL(10, 2),
    discount_percentage INTEGER,
    rating DECIMAL(3, 2),  -- 0.00 to 5.00
    review_count INTEGER,
    product_url TEXT NOT NULL,
    image_url TEXT,
    availability VARCHAR(50),
    is_sponsored BOOLEAN DEFAULT FALSE,
    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- PRICE HISTORY TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS price_history (
    id SERIAL PRIMARY KEY,
    product_id VARCHAR(20) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    original_price DECIMAL(10, 2),
    discount_percentage INTEGER,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
);

-- ============================================================================
-- CATEGORIES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    total_products INTEGER DEFAULT 0,
    last_scraped_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SCRAPING SESSIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS scraping_sessions (
    id SERIAL PRIMARY KEY,
    session_id UUID DEFAULT uuid_generate_v4(),
    category VARCHAR(100),
    pages_scraped INTEGER DEFAULT 0,
    products_found INTEGER DEFAULT 0,
    products_saved INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'running',  -- running, completed, failed
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Products table indexes
CREATE INDEX IF NOT EXISTS idx_products_product_id ON products(product_id);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand);
CREATE INDEX IF NOT EXISTS idx_products_price ON products(current_price);
CREATE INDEX IF NOT EXISTS idx_products_rating ON products(rating);
CREATE INDEX IF NOT EXISTS idx_products_discount ON products(discount_percentage);
CREATE INDEX IF NOT EXISTS idx_products_last_updated ON products(last_updated_at);
CREATE INDEX IF NOT EXISTS idx_products_category_price ON products(category, current_price);
CREATE INDEX IF NOT EXISTS idx_products_category_rating ON products(category, rating);
CREATE INDEX IF NOT EXISTS idx_products_category_discount ON products(category, discount_percentage);

-- Price history indexes
CREATE INDEX IF NOT EXISTS idx_price_history_product_id ON price_history(product_id);
CREATE INDEX IF NOT EXISTS idx_price_history_recorded_at ON price_history(recorded_at);

-- Categories indexes
CREATE INDEX IF NOT EXISTS idx_categories_name ON categories(name);

-- Sessions indexes
CREATE INDEX IF NOT EXISTS idx_sessions_status ON scraping_sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_started_at ON scraping_sessions(started_at);

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Best deals view (products with highest discounts)
CREATE OR REPLACE VIEW best_deals AS
SELECT 
    product_id,
    title,
    brand,
    category,
    current_price,
    original_price,
    discount_percentage,
    rating,
    review_count,
    product_url,
    image_url,
    last_updated_at
FROM products
WHERE discount_percentage IS NOT NULL 
  AND discount_percentage > 0
  AND current_price IS NOT NULL
ORDER BY discount_percentage DESC;

-- Top rated products view
CREATE OR REPLACE VIEW top_rated AS
SELECT 
    product_id,
    title,
    brand,
    category,
    current_price,
    rating,
    review_count,
    product_url,
    image_url,
    last_updated_at
FROM products
WHERE rating >= 4.5 
  AND review_count >= 100
ORDER BY rating DESC, review_count DESC;

-- Category summary view
CREATE OR REPLACE VIEW category_summary AS
SELECT 
    category,
    COUNT(*) as total_products,
    AVG(current_price) as avg_price,
    MIN(current_price) as min_price,
    MAX(current_price) as max_price,
    AVG(rating) as avg_rating,
    AVG(discount_percentage) as avg_discount,
    MAX(last_updated_at) as last_updated
FROM products
WHERE current_price IS NOT NULL
GROUP BY category;

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function to update last_updated_at timestamp
CREATE OR REPLACE FUNCTION update_last_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for products table
DROP TRIGGER IF EXISTS trigger_update_last_updated ON products;
CREATE TRIGGER trigger_update_last_updated
    BEFORE UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_last_updated_at();

-- Function to record price history
CREATE OR REPLACE FUNCTION record_price_change()
RETURNS TRIGGER AS $$
BEGIN
    -- Only record if price actually changed
    IF OLD.current_price IS DISTINCT FROM NEW.current_price THEN
        INSERT INTO price_history (product_id, price, original_price, discount_percentage)
        VALUES (NEW.product_id, NEW.current_price, NEW.original_price, NEW.discount_percentage);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for price history
DROP TRIGGER IF EXISTS trigger_price_history ON products;
CREATE TRIGGER trigger_price_history
    AFTER UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION record_price_change();

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Insert common categories
INSERT INTO categories (name, description) VALUES
    ('laptop', 'Laptops and notebook computers'),
    ('headphones', 'Headphones and earbuds'),
    ('monitor', 'Computer monitors and displays'),
    ('keyboard', 'Computer keyboards'),
    ('mouse', 'Computer mice and pointing devices')
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- UTILITY QUERIES (commented)
-- ============================================================================

-- Get products with price drops
-- SELECT * FROM price_history 
-- WHERE price < (SELECT price FROM price_history WHERE product_id = price_history.product_id ORDER BY recorded_at DESC LIMIT 1 OFFSET 1);

-- Get category statistics
-- SELECT * FROM category_summary;

-- Get best deals
-- SELECT * FROM best_deals LIMIT 10;

-- Get recent scraping sessions
-- SELECT * FROM scraping_sessions ORDER BY started_at DESC LIMIT 10;
