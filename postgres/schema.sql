CREATE TABLE IF NOT EXISTS pending_actions (
    action_id VARCHAR(255) PRIMARY KEY,
    sender VARCHAR(255),
    subject TEXT,
    decision VARCHAR(50),
    category VARCHAR(50),
    reason TEXT,
    confidence_score FLOAT,
    status VARCHAR(50) DEFAULT 'PENDING',
    result_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE EXTENSION IF NOT EXISTS vector;
