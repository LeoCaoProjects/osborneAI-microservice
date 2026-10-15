-- Store each notification requested by another service.
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    feedback_id INTEGER NOT NULL,
    recipient VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);