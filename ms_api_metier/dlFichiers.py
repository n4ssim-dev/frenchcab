import requests
import pandas as pd
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parent / "data" / "raw"


def downloadData(base_dir=RAW_DIR):
    base_dir = Path(base_dir)
    base_dir.mkdir(parents=True, exist_ok=True)

    url = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2026-07.parquet"
    file_name = base_dir / "yellow_tripdata_2026-07.parquet"

    print(f"Téléchargement de {file_name.name}...")
    response = requests.get(url)

    if response.status_code == 200:
        file_name.write_bytes(response.content)
        print("Téléchargement terminé !")
        return file_name

    print(f"Impossible de télécharger {file_name.name} (HTTP {response.status_code})")
    return None


def convertCsv(parquet_file):
    parquet_file = Path(parquet_file)
    csv_file = parquet_file.with_suffix(".csv")
    df = pd.read_parquet(parquet_file)
    df.to_csv(csv_file, index=False)
    print(f"CSV créé : {csv_file}")
    return csv_file


if __name__ == "__main__":
    fichier = downloadData()
    if fichier:
        convertCsv(fichier)