const sqlite3 = require("sqlite3").verbose();

const db = new sqlite3.Database("./data/taxi_test.db");

db.run(`
CREATE TABLE IF NOT EXISTS reservations(
    uid_reservation INTEGER PRIMARY KEY AUTOINCREMENT,
    resa_PU_locationID INTEGER NOT NULL,
    resa_DO_locationID INTEGER NOT NULL,
    resa_date DATE NOT NULL,
    resa_heure TIME NOT NULL,
    estimation_duree_course REAL NOT NULL,
    date_heure_reservation DATETIME NOT NULL,
    statut_resa INTEGER NOT NULL,
    uid_trajet INTEGER NOT NULL,
    locationID INTEGER NOT NULL,
    locationID_1 INTEGER NOT NULL,
    uid_client INTEGER NOT NULL
)
`);

db.close();