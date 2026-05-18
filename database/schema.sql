CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255),
    password_hash TEXT
);

CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    user_id INT,
    message TEXT,
    sender VARCHAR(10),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE risk_scores (
    id SERIAL PRIMARY KEY,
    user_id INT,
    score INT,
    level VARCHAR(20)
);