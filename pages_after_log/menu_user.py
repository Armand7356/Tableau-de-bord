import streamlit as st
import bcrypt
import os
import json
from datetime import datetime
    
    
# Configurer la page
st.title("Menu gestion des utilisateurs")

# Section de gestion des utilisateurs pour l'Admin
    if st.session_state.username == "Admin":
        st.sidebar.write("**Gestion des utilisateurs**")
        users = load_users()

        # Liste des utilisateurs
        st.write("### Utilisateurs enregistrés")
        for user in users:
            st.write(user)

        # Ajouter un utilisateur
        st.write("### Ajouter un utilisateur")
        new_username = st.text_input("Nom du nouvel utilisateur", key="new_username")
        new_password = st.text_input("Mot de passe", type="password", key="new_password")
        if st.button("Ajouter"):
            if new_username in users:
                st.error("L'utilisateur existe déjà.")
            else:
                users[new_username] = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                save_users(users)
                st.success(f"Utilisateur {new_username} ajouté.")
                write_log(f"Utilisateur {new_username} ajouté par Admin.")

        # Supprimer un utilisateur
        st.write("### Supprimer un utilisateur")
        delete_username = st.selectbox("Utilisateur à supprimer", [u for u in users if u != "Admin"])
        if st.button("Supprimer"):
            if delete_username:
                del users[delete_username]
                save_users(users)
                st.success(f"Utilisateur {delete_username} supprimé.")
                write_log(f"Utilisateur {delete_username} supprimé par Admin.")

        # Modifier un mot de passe
        st.write("### Modifier un mot de passe")
        user_to_update = st.selectbox("Utilisateur à modifier", users.keys())
        new_password_update = st.text_input("Nouveau mot de passe", type="password", key="update_password")
        if st.button("Mettre à jour le mot de passe"):
            if user_to_update:
                users[user_to_update] = bcrypt.hashpw(new_password_update.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                save_users(users)
                st.success(f"Mot de passe pour {user_to_update} mis à jour.")
                write_log(f"Mot de passe pour {user_to_update} modifié par Admin.")