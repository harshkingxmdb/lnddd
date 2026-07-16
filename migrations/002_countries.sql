-- Countries table
-- Stores available countries for accounts

CREATE TABLE IF NOT EXISTS countries (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    flag VARCHAR(10),
    is_active BOOLEAN DEFAULT TRUE,
    display_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default countries
INSERT INTO countries (name, flag, display_order) VALUES
('Bangladesh', '🇧🇩', 1),
('Ecuador', '🇪🇨', 2),
('Greenland', '🇬🇱', 3),
('India', '🇮🇳', 4),
('Myanmar', '🇲🇲', 5),
('Nepal', '🇳🇵', 6),
('SriLanka', '🇱🇰', 7),
('United Kingdom', '🇬🇧', 8),
('United States', '🇺🇸', 9),
('Uzbekistan', '🇺🇿', 10),
('Viet Nam', '🇻🇳', 11),
('Zimbabwe', '🇿🇼', 12)
ON CONFLICT (name) DO NOTHING;

-- Index
CREATE INDEX IF NOT EXISTS idx_countries_is_active ON countries(is_active);
