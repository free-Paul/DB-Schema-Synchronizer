CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL
);

-- данные, которые должны сохраниться при миграции
INSERT INTO users (username, email) VALUES 
    ('admin', 'admin@example.com'),
    ('test_user', 'test@example.com');