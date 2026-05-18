INSERT INTO users (email, password_hash)
VALUES ('test@example.com', 'hashedpassword');

INSERT INTO risk_scores (user_id, score, level)
VALUES (1, 65, 'High');