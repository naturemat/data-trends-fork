CREATE TABLE IF NOT EXISTS tendencias (
    id SERIAL PRIMARY KEY,
    fecha DATE NOT NULL,
    hora TIME NOT NULL,
    tendencia VARCHAR(255) NOT NULL
);
