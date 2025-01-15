import streamlit as st
import os
from datetime import datetime

# Fonction pour lire les utilisateurs et mots de passe depuis un fichier texte
def load_users(file_path):
    users = {}
    try:
        with open(file_path, "r") as f:
            for line in f:
                username, password = line.strip().split(",")
                users[username] = password
    except Exception as e:
        st.error(f"Erreur lors du chargement des utilisateurs : {e}")
    return users

# Fonction pour écrire dans un fichier log
def write_log(message):
    with open("log.txt", "a") as log_file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"{timestamp} - {message}\n")

# Fonction d'authentification
def authenticate(username, password, users):
    return username in users and users[username] == password

# Charger les utilisateurs depuis le fichier
users_file = "users.txt"  # Chemin vers le fichier contenant les utilisateurs
users = load_users(users_file)

# Initialiser l'état de session
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Gestion de l'authentification
if not st.session_state.authenticated:
    st.title("Connexion à l'application")
    username = st.text_input("Nom d'utilisateur")
    password = st.text_input("Mot de passe", type="password")
    login_button = st.button("Se connecter")

    if login_button:
        if authenticate(username, password, users):
            st.session_state.authenticated = True
            st.success(f"Bienvenue, {username} !")
            write_log(f"Connexion réussie : {username}")
            st.experimental_rerun()  # Recharger pour cacher les pages
        else:
            st.error("Nom d'utilisateur ou mot de passe incorrect.")
            write_log(f"Tentative de connexion échouée : {username}")
else:
    # Une fois connecté, afficher les pages de l'application
    st.sidebar.title("Navigation")
    available_pages = [file.replace(".py", "") for file in os.listdir("pages_after_log") if file.endswith(".py")]
    selected_page = st.sidebar.radio("Choisissez une page", available_pages)

    # Charger et exécuter la page sélectionnée
    if selected_page:
        with open(f"pages_after_log/{selected_page}.py", "r") as f:
            exec(f.read())

    # Bouton de déconnexion
    if st.sidebar.button("Se déconnecter"):
        st.session_state.authenticated = False
        st.experimental_rerun()
