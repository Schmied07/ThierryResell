import pandas as pd

# Test simple pour vérifier openpyxl
try:
    # Lire le fichier Excel existant
    df = pd.read_excel('/app/catalog_sample.xlsx', engine='openpyxl')
    print(f"✅ Fichier lu avec succès: {len(df)} lignes")
    print(f"Colonnes: {list(df.columns)}")
except Exception as e:
    print(f"❌ Erreur: {e}")
