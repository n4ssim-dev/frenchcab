from unittest.mock import patch, MagicMock
from ms_api_metier.dlFichiers import downloadData

def test_fichiersTelecharges(tmp_path):
    
    with patch('ms_api_metier.dlFichiers.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"faux data"
        mock_get.return_value = mock_response

        
        downloadData(base_dir=str(tmp_path))

    # On récupère la liste de tout ce qui a été créé dans le dossier
    fichiers_crees = list(tmp_path.glob("*"))
    
    # On vérifie que la liste n'est pas vide
    assert len(fichiers_crees) > 0 
    
    # On vérifie qu'au moins l'un des éléments est bien un fichier
    assert any(f.is_file() for f in fichiers_crees)