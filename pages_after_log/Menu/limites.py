import streamlit as st
import pandas as pd
import os

# === CHARGEMENT DU FICHIER EXCEL ===
file_path = "tableau de bord Wit.xlsx"


# Charger limites existantes si le fichier existe
limites_existantes = {}

limites_file_path = "./pages_after_log/Menu/limites_consommation.txt"

if os.path.exists(limites_file_path):
    with open(limites_file_path, "r", encoding="utf-8") as f:
        for ligne in f:
            if "\t" in ligne:
                col_name, limite = ligne.strip().split("\t")
                limites_existantes[col_name.strip()] = float(limite)


try:
    data = pd.ExcelFile(file_path)
    sheet_names = data.sheet_names
    st.success(f"✅ Fichier '{file_path}' chargé avec succès.")
except FileNotFoundError:
    st.error(f"❌ Fichier '{file_path}' non trouvé. Vérifiez le chemin.")
    st.stop()
except Exception as e:
    st.error(f"Erreur de lecture du fichier : {e}")
    st.stop()

# Lire une feuille (par exemple "Conso_h")
if "Conso_h" in sheet_names:
    df = pd.read_excel(file_path, sheet_name="Conso_h")
else:
    st.error("❌ Feuille 'Conso_h' introuvable dans le fichier.")
    st.stop()

# Nettoyer : supprimer colonnes contenant 'Cpt'
colonnes = [col for col in df.columns if "Cpt" not in col]
# Séparer les colonnes
eau_cols = [col for col in colonnes if "eau" in col.lower()]
gaz_cols = [col for col in colonnes if "gaz" in col.lower()]
elec_cols = [col for col in colonnes if "elec" in col.lower()]

st.title("Définir les limites de consommation")

limites = {}

def saisie_limites(titre, liste_cols):
    st.subheader(titre)
    for col in liste_cols:
        valeur_defaut = limites_existantes.get(col, 0.0)
        limite = st.number_input(f"{col}", min_value=0.0, step=0.1, format="%.2f", value=valeur_defaut)

        limites[col] = limite

saisie_limites("🌊 Consommation Eau", eau_cols)
saisie_limites("🔥 Consommation Gaz", gaz_cols)
saisie_limites("⚡ Consommation Électricité", elec_cols)
if st.button("📄 Générer le fichier de limites"):
    output_dir = "./pages_after_log/Menu"
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, "limites_consommation.txt")
    
    with open(output_path, "w", encoding="utf-8") as f:
        for col, limite in limites.items():
            f.write(f"{col}\t{limite}\n")
    
    st.success(f"✅ Fichier généré avec succès : {output_path}")
