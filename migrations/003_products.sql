-- Products table (Accounts stock)
-- Stores all Telegram accounts with session strings

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    country_id INT REFERENCES countries(id) ON DELETE CASCADE,
    phone_number VARCHAR(20) NOT NULL,
    session_string TEXT NOT NULL,
    price DECIMAL(10,2) DEFAULT 0.00,
    status VARCHAR(20) DEFAULT 'available', -- available, sold, blocked, expired
    added_by BIGINT,
    sold_to BIGINT,
    sold_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_products_country_id ON products(country_id);
CREATE INDEX IF NOT EXISTS idx_products_status ON products(status);
CREATE INDEX IF NOT EXISTS idx_products_country_status ON products(country_id, status);

-- View to get available stock count per country
CREATE OR REPLACE VIEW available_stock AS
SELECT 
    c.id as country_id,
    c.name as country_name,
    c.flag,
    COUNT(p.id) as available_count
FROM countries c
LEFT JOIN products p ON c.id = p.country_id AND p.status = 'available'
WHERE c.is_active = TRUE
GROUP BY c.id, c.name, c.flag;
