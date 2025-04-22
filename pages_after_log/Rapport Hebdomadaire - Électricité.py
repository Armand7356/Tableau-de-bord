import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
import locale
import io
import io
import requests
import pandas as pd
from io import BytesIO

# Configurer la locale pour les noms des jours en français
locale.setlocale(locale.LC_TIME, "C")

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

write_log("Page Rapport hebdomadaire elec")

# Charger les données Excel
#write_log("Chargement du fichier Excel...")
file_path = "tableau de bord Wit.xlsx"
data = pd.ExcelFile(file_path)
#write_log(f"Fichier chargé avec succès : {data.sheet_names}")
    
# Charger les données horaires
#write_log("Chargement des données horaires...")
df_hourly = data.parse("Conso_h")
#write_log(f"Aperçu des données horaires : {df_hourly.head().to_string()}")

# Configurer la page
st.title("Rapport Hebdomadaire - Électricité")

# Create a horizontal layout for filters
col1, col2, col3, col4 = st.columns([1.7, 1.2, 1.2, 2])

with col1:

    # Sélection de la semaine
    current_date = datetime.now()
    default_start_date = (current_date - timedelta(days=current_date.weekday(), weeks=1)).date()
    week_number = st.number_input("Choisissez le numéro de la semaine :", value=default_start_date.isocalendar()[1], step=1)
    #write_log(f"Numéro de la semaine sélectionnée : {week_number}")

with col2:

    year = st.number_input("Choisissez l'année :", value=default_start_date.year, step=1)
    #write_log(f"Année sélectionnée : {year}")

with col3:

    # Choix de l'heure de début de journée
    start_hour = 0 # st.number_input("Heure de début de journée :", min_value=0, max_value=23, value=5, step=1)
    #write_log(f"Heure de début de journée sélectionnée : {start_hour}")
with col4:
    # Définir les plages horaires
    default_time_ranges = [(5, 16), (16, 21), (21, 5)]
    time_ranges = st.text_input(
        "Définissez les plages horaires (format : hh-hh,hh-hh,...) :",
        value=','.join([f"{start}-{end}" for start, end in default_time_ranges])
    )
    try:
        parsed_time_ranges = [(int(start), int(end)) for start, end in (range_.split('-') for range_ in time_ranges.split(','))]
        #write_log(f"Plages horaires sélectionnées : {parsed_time_ranges}")
    except ValueError:
        st.error("Format des plages horaires invalide. Utilisez le format hh-hh,hh-hh,...")
        #write_log("Erreur : Format des plages horaires invalide.")
        parsed_time_ranges = default_time_ranges


# Fonction pour traiter les données et afficher les rapports

def process_data_and_display_elec(df_hourly, week_number, year, start_hour, title_prefix):
    #write_log("Conversion des dates horaires et ajout des colonnes Semaine et Annee...")
    df_hourly["DateTime"] = pd.to_datetime(df_hourly["Date /h"], errors='coerce')
    df_hourly["Semaine"] = df_hourly["DateTime"].dt.isocalendar().week
    df_hourly["Annee"] = df_hourly["DateTime"].dt.year
    #write_log("Dates horaires converties avec succès.")

    #write_log("Filtrage des données horaires pour la semaine sélectionnée...")
    filtered_data = df_hourly[(df_hourly["Semaine"] == week_number) & (df_hourly["Annee"] == year)]
    filtered_data = filtered_data[filtered_data["DateTime"].dt.hour >= start_hour]
    filtered_data = filtered_data[filtered_data["DateTime"] < (filtered_data["DateTime"].max() + timedelta(days=1))]
    #write_log(f"Données horaires filtrées : {filtered_data.to_string()}")

    if filtered_data.empty:
        st.warning(f"Aucune donnée disponible pour {title_prefix} la semaine sélectionnée.")
        #write_log(f"Aucune donnée disponible pour {title_prefix} la semaine sélectionnée.")
        return

    # Ajuster les données pour refléter les jours de 5h à 5h (ou heure choisie)
    #write_log("Ajustement des données horaires pour le découpage des jours...")
    filtered_data["Jour"] = (filtered_data["DateTime"] - pd.to_timedelta((filtered_data["DateTime"].dt.hour < start_hour).astype(int), unit="D")).dt.date


    # Exclure les colonnes non numériques et celles contenant "général" ou qui ne sont pas des consommations
    numeric_columns = filtered_data.select_dtypes(include=['number']).columns
    numeric_columns = [col for col in numeric_columns if "elec" in col.lower() if "consomation" in col.lower() and "général" not in col.lower()]
    daily_data = filtered_data.groupby("Jour")[numeric_columns].sum()



    # S'assurer que l'index est au format datetime
    daily_data.index = pd.to_datetime(daily_data.index)

    # Limiter aux jours de Lundi (0) à Dimanche (6)
    daily_data = daily_data.loc[daily_data.index.dayofweek < 7]

    #write_log(f"Données journalières calculées : {daily_data.to_string()}")

    # Création de l'histogramme empilé
    #write_log("Création de l'histogramme empilé...")
    fig = go.Figure()
    for col in numeric_columns:
        fig.add_trace(go.Bar(
            x=daily_data.index,
            y=daily_data[col],
            name=col.replace("Consomation", "").strip()
        ))

    # Configurer et afficher l'histogramme
    fig.update_layout(
        template="plotly_white",
        barmode="stack",
        title=f"{title_prefix} - Semaine {week_number} {year}",
        xaxis_title="Jour",
        yaxis_title="Consommation (kWh)",
        legend_title="Catégories",
    )
    st.plotly_chart(fig, use_container_width=True)

    # Vérifier si les colonnes HC, HP et général existent
    if all(col in filtered_data.columns for col in ["Consomation elec HC", "Consomation elec HP", "Consomation elec général"]):
        # Grouper les données par jour et calculer les sommes journalières
        recap_table = filtered_data.groupby("Jour")[["Consomation elec HC", "Consomation elec HP", "Consomation elec général"]].sum()
        
        # Ajouter une ligne somme pour la semaine
        recap_table.loc["Total Semaine"] = recap_table.sum()
    
        # Ajouter les unités kWh à chaque valeur
        recap_table = recap_table.applymap(lambda x: f"{x:.2f} kWh")
        
        # Afficher le tableau
        st.write("### Tableau de récapitulation des consommations (kWh)")
        st.dataframe(recap_table)
    else:
        st.warning("Les colonnes nécessaires ('elec HC', 'elec HP', 'elec général') ne sont pas toutes présentes dans les données.")



    # Vérifier si les colonnes HP et HC existent
    if "Consomation elec HP" in filtered_data.columns and "Consomation elec HC" in filtered_data.columns:
        # Calculer les totaux des heures pleines et heures creuses
        total_hp = filtered_data["Consomation elec HP"].sum()
        total_hc = filtered_data["Consomation elec HC"].sum()
    
        # Création du diagramme en cercle
        fig_pie = go.Figure()
        fig_pie.add_trace(go.Pie(
            labels=["Heures Pleines", "Heures Creuses"],
            values=[total_hp, total_hc],
            textinfo='label+percent',
            insidetextorientation='radial'
        ))
        fig_pie.update_layout(
            title="Répartition Consommation HP/HC",
            showlegend=True
        )
    
        # Afficher le diagramme
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.warning("Les colonnes 'elec HP' et 'elec HC' sont introuvables dans les données.")


    
       
# Page : Électricité
process_data_and_display_elec(df_hourly, week_number, year, start_hour, "Consommation Générale d'Électricité")
