DROP TABLE IF EXISTS impiegati;

CREATE TABLE IF NOT EXISTS impiegati (
    matricola INTEGER PRIMARY KEY,
    cognome TEXT NOT NULL,
    conteggio INTEGER NOT NULL
);

INSERT INTO impiegati (matricola, cognome, conteggio) VALUES
(101, 'Rossi', 1),
(102, 'Bruni', 2);
