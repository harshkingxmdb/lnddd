-- Payments table
-- Stores all payment transactions

CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    txn_id VARCHAR(100) UNIQUE,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    order_id VARCHAR(50) REFERENCES orders(order_id),
    amount DECIMAL(10,2) NOT NULL,
    utr_number VARCHAR(50),
    screenshot_url TEXT,
    payment_method VARCHAR(20), -- upi, crypto
    status VARCHAR(20) DEFAULT 'pending', -- pending, verified, failed, refunded
    verified_by BIGINT,
    verified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_utr_number ON payments(utr_number);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_payments_user_status ON payments(user_id, status);
