import streamlit as st
import socket
from datetime import datetime



page_title="Application Multi-pages"

# Configurer l'application principale
st.set_page_config(
    page_title="Application Multi-pages",
)

# Fonction pour écrire dans un fichier log
def write_log(message):
    with open("log.txt", "a") as log_file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"{timestamp} - {message}\n")


st.title("Tableau de bord énergie")
st.write("Utilisez le menu pour naviguer entre les pages.")
st.write("-   page 1: Rapport Consomation eau par semaine")
st.write("-   page 2: Rapport Consomation gaz par semaine")
st.write("-   page 3: Rapport Consomation éléctricité par semaine")
st.write("-   page 4: Visualisation manuelle")

import os
import time
import threading
import requests
from datetime import datetime
import streamlit as st

# URL du fichier sur Google Drive
url = "https://docs.google.com/spreadsheets/d/1pZSRFIo9qApzhwmFf_gHZ0lO8bsmGhFF/export?format=xlsx"

# Chemin local pour enregistrer le fichier
local_file_path = "tableau de bord Wit.xlsx"

# Période de mise à jour automatique (en secondes, 1 heure par défaut)
update_interval = 3600


def download_file(url, local_path):
    """Télécharge le fichier depuis l'URL et l'enregistre localement."""
    try:
        # Télécharger le fichier
        response = requests.get(url, allow_redirects=True)
        response.raise_for_status()  # Vérifie les erreurs HTTP

        # Écrire le fichier localement
        with open(local_path, "wb") as f:
            f.write(response.content)

        # Mettre à jour la date de modification locale
        current_time = datetime.now().timestamp()
        os.utime(local_path, (current_time, current_time))

        return "Fichier téléchargé et mis à jour avec succès."
    except Exception as e:
        return f"Erreur lors du téléchargement : {e}"


def auto_update_file(url, local_path, interval):
    """Met à jour automatiquement le fichier toutes les `interval` secondes."""
    while True:
        message = download_file(url, local_path)
        print(f"{datetime.now()} - {message}")  # Enregistre dans la console/log
        time.sleep(interval)


# Démarrer le thread pour la mise à jour automatique
if "update_thread_started" not in st.session_state:
    st.session_state.update_thread_started = True
    update_thread = threading.Thread(target=auto_update_file, args=(url, local_file_path, update_interval), daemon=True)
    update_thread.start()


# Interface utilisateur Streamlit
st.title("Mise à jour du fichier Google Drive")

# Bouton pour mise à jour manuelle
if st.button("Mettre à jour le document maintenant"):
    message = download_file(url, local_file_path)
    if "Erreur" in message:
        st.error(message)
    else:
        st.success(message)

# Afficher le chemin local et l'état
if os.path.exists(local_file_path):
    local_mod_time = datetime.fromtimestamp(os.path.getmtime(local_file_path))
    st.write(f"Fichier local : `{local_file_path}`")
    st.write(f"Dernière mise à jour locale : {local_mod_time}")
else:
    st.warning("Le fichier local n'existe pas encore.")
