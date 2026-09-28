import requests
import os


def downloadData(base_dir="ms_data/data/raw"):
    # Création d'un dossier pour stocker les fichiers téléchargés
    os.makedirs(base_dir, exist_ok=True)

    for year in range(2026, 2022, -1):
        for month in range(1, 13):
            # Construction de l'url de téléchargement en fonction de l'année et du mois
            download_url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{year}-{month:02d}.parquet"
            file_name = f"{base_dir}/yellow_tripdata_{year}-{month:02d}.parquet"

            # Télécharger le fichier
            print(f"Téléchargement de {file_name}...")
            response = requests.get(download_url)

            if response.status_code == 200:
                with open(file_name, "wb") as f:
                    f.write(response.content)
            else:
                print(f"Impossible de télécharger {file_name}. Code de statut HTTP: {response.status_code}")

    print("Téléchargement terminé!")


if __name__ == "__main__":
    downloadData()
