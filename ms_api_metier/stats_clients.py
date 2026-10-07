import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "data" / "frenchcab.db"

conn = sqlite3.connect(DB_PATH)
requete = """
SELECT c.nom,
       COUNT(*)                           AS nb_trajets,
       ROUND(AVG(t.trip_distance), 2)     AS distance_moy,
       ROUND(AVG(t.trip_duration_min), 1) AS duree_moy_min,
       ROUND(SUM(t.total_amount), 2)      AS depense_totale
FROM clients c
JOIN reservations r ON r.uid_client = c.uid_client
JOIN trajets t      ON t.uid_reservation = r.uid_reservation
GROUP BY c.uid_client
ORDER BY nb_trajets DESC
"""
print(f"{'Client':<16}{'Trajets':>8}{'Dist.':>8}{'Durée':>8}{'Total $':>12}")
for nom, nb, dist, duree, total in conn.execute(requete):
    print(f"{nom:<16}{nb:>8}{dist:>8}{duree:>8}{total:>12}")
conn.close()