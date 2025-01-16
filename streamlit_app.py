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

# Fonction pour écrire dans un fichier log
def write_log(message):
    with open("log.txt", "a") as log_file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"{timestamp} - {message}\n")

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

    # Navigation vers les pages
    pages_directory = "pages_after_log"
    available_pages = [
        file.replace(".py", "") for file in os.listdir(pages_directory) if file.endswith(".py")
    ]

    

    # Récupérer les fichiers et trier par ordre alphabétique
    available_pages = sorted(
    [file.replace(".py", "") for file in os.listdir(pages_directory) if file.endswith(".py")]
)

    # Restreindre l'accès à certaines pages (exemple : "Gestion utilisateurs" uniquement pour Admin)
    if st.session_state.username != "Admin":
        available_pages = [page for page in available_pages if page != "Gestion utilisateurs"]
        
    # Sélection de la page via le menu de navigation
    selected_page = st.sidebar.radio("Choisissez une page", available_pages)

    # Charger dynamiquement la page sélectionnée
    if selected_page:
        try:
            with open(f"{pages_directory}/{selected_page}.py", "r") as f:
                exec(f.read())  # Charge et exécute le contenu de la page
        except Exception as e:
            st.error(f"Erreur lors du chargement de la page {selected_page}: {e}")

    # Bouton de déconnexion
    if st.sidebar.button("Se déconnecter"):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.experimental_rerun()


