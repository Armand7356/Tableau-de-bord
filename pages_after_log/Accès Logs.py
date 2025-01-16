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
st.write("### Contenu des Logs")
try:
    with open(log_file_path, "r") as log_file:
        logs = log_file.readlines()
        if logs:
            st.text_area("Logs", value="".join(logs), height=400)
        else:
            st.info("Aucune entrée dans le fichier de log.")
except Exception as e:
    st.error(f"Erreur lors de la lecture du fichier de log : {e}")

# Option pour télécharger le fichier de log
st.write("### Télécharger les Logs")
with open(log_file_path, "r") as log_file:
    st.download_button(
        label="Télécharger le fichier de log",
        data=log_file.read(),
        file_name="log.txt",
        mime="text/plain",
    )
