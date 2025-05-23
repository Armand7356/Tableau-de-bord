import streamlit as st
import os
import bcrypt
import json
from datetime import datetime

# Chemin vers le fichier contenant les utilisateurs
users_file = "users.json"

# Configurer l'application principale
st.set_page_config(
    page_title="Tableau de Bord",
    layout="wide",
)

# Initialisation du fichier utilisateurs si inexistant
if not os.path.exists(users_file):
    default_user = {
        "Admin": bcrypt.hashpw("Admin".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    }
    with open(users_file, "w") as f:
        json.dump(default_user, f)

# Fonction pour charger les utilisateurs
def load_users():
    with open(users_file, "r") as f:
        return json.load(f)

# Fonction pour sauvegarder les utilisateurs
def save_users(users):
    with open(users_file, "w") as f:
        json.dump(users, f)

import socket
from datetime import datetime
import streamlit as st

# Fonction pour obtenir l'adresse IP de l'utilisateur
def get_user_ip():
    try:
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)
    except Exception as e:
        return "IP inconnue"

# Fonction pour écrire dans un fichier log
def write_log(message):
    user = st.session_state.get("username", "Utilisateur inconnu")
    user_ip = get_user_ip()
    with open("log.txt", "a") as log_file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"{timestamp} - {user} ({user_ip}) - {message}\n")


# Fonction d'authentification
def authenticate(username, password, users):
    return username in users and bcrypt.checkpw(password.encode("utf-8"), users[username].encode("utf-8"))

# Initialisation de l'état de session
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = None
if "username" not in st.session_state:
    st.session_state.username = None


# Gestion de l'authentification
if not st.session_state.authenticated:
    st.title("Connexion à l'application")
    username = st.text_input("Nom d'utilisateur")
    password = st.text_input("Mot de passe", type="password")
    login_button = st.button("Se connecter")

    if login_button:
        users = load_users()
        if authenticate(username, password, users):
            st.session_state.authenticated = True
            st.session_state.username = username
            write_log(f"Connexion réussie : {username}")

        else:
            st.error("Nom d'utilisateur ou mot de passe incorrect.")
            write_log(f"Tentative de connexion échouée : {username}")
else:
    # Interface principale après connexion
    st.sidebar.title(f"Bienvenue, {st.session_state.username} !")

    pages_directory = "pages_after_log"

    # Scan des sous-dossiers et des fichiers .py
    page_structure = {}
    for root, dirs, files in os.walk(pages_directory):
        relative_root = os.path.relpath(root, pages_directory)
        if relative_root == ".":
            continue  # on saute la racine directe
        section = relative_root.replace("\\", "/")  # Windows-friendly
        page_structure[section] = [file.replace(".py", "") for file in files if file.endswith(".py")]

    if not page_structure:
        st.error("Aucune page trouvée dans l'arborescence.")
    else:
        # Sélectionner un dossier (section)
        selected_section = st.sidebar.selectbox("Choisissez un rapport :", sorted(page_structure.keys()))

        # Ensuite, choisir la page dans ce dossier
        if selected_section:
            selected_page = st.sidebar.radio(f"Pages dans {selected_section} :", page_structure[selected_section])

            # Charger dynamiquement
            if selected_page:
                try:
                    page_path = os.path.join(pages_directory, selected_section, selected_page + ".py")
                    with open(page_path, "r", encoding="utf-8") as f:
                        exec(f.read())
                except Exception as e:
                    st.error(f"Erreur lors du chargement de {selected_page} : {e}")

    # Déconnexion
    if st.sidebar.button("Se déconnecter"):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.experimental_rerun()



