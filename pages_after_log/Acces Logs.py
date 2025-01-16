import streamlit as st
import os

# Chemin vers le fichier de log
log_file_path = "log.txt"

# Vérifier si le fichier de log existe
if not os.path.exists(log_file_path):
    with open(log_file_path, "w") as f:
        f.write("Fichier de log initialisé.\n")

# Interface principale
st.title("Accès aux Logs")
st.write("Cette page permet de lire et de télécharger les fichiers de log.")

# Bouton pour rafraîchir les logs
if st.button("Rafraîchir les logs"):
    st.experimental_rerun()

# Lire le contenu du fichier de log
st.write("### Les 500 dernières lignes des Logs")
try:
    with open(log_file_path, "r") as log_file:
        logs = log_file.readlines()
        if logs:
            # Afficher uniquement les 500 dernières lignes
            last_500_logs = logs[-500:] if len(logs) > 500 else logs
            st.text_area("Logs (dernières 500 lignes)", value="".join(last_500_logs), height=400)
        else:
            st.info("Aucune entrée dans le fichier de log.")
except Exception as e:
    st.error(f"Erreur lors de la lecture du fichier de log : {e}")

# Option pour télécharger le fichier complet
st.write("### Télécharger les Logs")
with open(log_file_path, "r") as log_file:
    st.download_button(
        label="Télécharger le fichier de log complet",
        data=log_file.read(),
        file_name="log.txt",
        mime="text/plain",
    )
