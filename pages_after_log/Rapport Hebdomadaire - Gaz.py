import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
import locale
import io
import requests
import pandas as pd
from io import BytesIO

# Configurer la locale pour les noms des jours en français
locale.setlocale(locale.LC_TIME, "C")


# Dictionnaire pour traduire les jours de la semaine en français
days_translation = {
    "Monday": "Lundi",
    "Tuesday": "Mardi",
    "Wednesday": "Mercredi",
    "Thursday": "Jeudi",
    "Friday": "Vendredi",
    "Saturday": "Samedi",
    "Sunday": "Dimanche",
}

# Fonction pour obtenir un nom de jour en français
def get_french_day(date):
    day_english = date.strftime("%A")  # Nom du jour en anglais
    return days_translation.get(day_english, day_english)  # Traduction en français

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

write_log("Page Rapport hebdomadaire EAU")

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
st.title("Rapport Hebdomadaire - Gaz")

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
    start_hour = st.number_input("Heure de début de journée :", min_value=0, max_value=23, value=5, step=1)
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

# Filtrer les données horaires pour la semaine sélectionnée
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
    st.warning("Aucune donnée disponible pour la semaine sélectionnée.")
    #write_log("Aucune donnée disponible pour la semaine sélectionnée.")
else:
    # Ajuster les données pour refléter les jours de 5h à 5h (ou heure choisie)
    #write_log("Ajustement des données horaires pour le découpage des jours...")
    filtered_data["Jour"] = (filtered_data["DateTime"] - pd.to_timedelta((filtered_data["DateTime"].dt.hour < start_hour).astype(int), unit="D")).dt.date

    # Exclure les colonnes non numériques et celles contenant "Cpt" pour l'agrégation
    numeric_columns = filtered_data.select_dtypes(include=['number']).columns
    numeric_columns = [col for col in numeric_columns if "Cpt" not in col]
    numeric_columns = [col for col in numeric_columns if "gaz" in col.lower()]
    daily_data = filtered_data.groupby("Jour")[numeric_columns].sum()

    # S'assurer que l'index est au format datetime
    daily_data.index = pd.to_datetime(daily_data.index)

    # Limiter aux jours de Lundi (0) à Dimanche (6)
    daily_data = daily_data.loc[daily_data.index.dayofweek < 7]

    #write_log(f"Données journalières calculées : {daily_data.to_string()}")

    # Création de l'histogramme empilé
    #write_log("Création de l'histogramme empilé...")
    fig = go.Figure()
    for col in ["Consomation gaz chaudiere 1", "Consomation gaz chaudiere 2"]:
        if col in daily_data.columns:
            fig.add_trace(go.Bar(
                x=daily_data.index,
                y=daily_data[col],
                name=col.replace("Consomation", "").strip()
            ))



    # Ajouter une colonne "Autres"
    if "Consomation gaz général" in daily_data.columns:
        daily_data["gaz Autres"] = daily_data["Consomation gaz général"] - (
            daily_data.get("Consomation gaz chaudiere 1", 0) +
            daily_data.get("Consomation gaz chaudiere 2", 0)
        ).clip(lower=0)
            
        
        fig.add_trace(go.Bar(
            x=daily_data.index,
            y=daily_data["gaz Autres"],
            name="Autres"
        ))

    # Configurer et afficher l'histogramme
    fig.update_layout(
        template="plotly_white",
        barmode="stack",
        title=f"Consommation Générale de Gaz - Semaine {week_number} {year}",
        xaxis_title="Jour",
        yaxis_title="Consommation (m³)",
        legend_title="Catégories",
    )
    st.plotly_chart(fig, use_container_width=True)

# Create a horizontal layout for filters
col11, col12, col13, col14 = st.columns([1.7, 1.2, 1.2, 2])

with col11:

    # Sélection du prix
    Prix_gaz = 0.20
    Prix_gaz = st.number_input("Prix gaz (€/kWh)", value=0.2, step=0.01)

# Ajouter un filtre pour n'afficher que les colonnes contenant "gaz"
filtered_columns = [col for col in daily_data.columns if "gaz" in col.lower()]
filtered_table = daily_data[filtered_columns]



# Ajouter les lignes moyenne et somme au tableau des données filtrées
filtered_table.loc['Moyenne'] = filtered_table.mean()
filtered_table.loc['Somme'] = filtered_table.sum()-filtered_table.loc['Moyenne']
filtered_table.loc['Prix'] = filtered_table.loc['Somme']*Prix_gaz
filtered_table= round(filtered_table,1)
# Afficher le tableau des valeurs de consommation pour la semaine
st.write("### Données de consommation sur la semaine")
st.dataframe(filtered_table)

# Créer les colonnes pour les plages horaires
#write_log("Calcul des consommations par plages horaires...")
hourly_data = []
for start, end in parsed_time_ranges:
    col_name = f"{start}h-{end}h"
    if start < end:
        hourly_data.append(
            filtered_data[(filtered_data["DateTime"].dt.hour >= start) & (filtered_data["DateTime"].dt.hour < end)]
            .groupby("Jour")["Consomation gaz général"].sum()
            .rename(col_name)
        )
    else:
        hourly_data.append(
            filtered_data[(filtered_data["DateTime"].dt.hour >= start) | (filtered_data["DateTime"].dt.hour < end)]
            .groupby("Jour")["Consomation gaz général"].sum()
            .rename(col_name)
        )
hourly_data = pd.concat(hourly_data, axis=1)

# Garantir un ordre constant des colonnes
hourly_data = hourly_data[[f"{start}h-{end}h" for start, end in parsed_time_ranges]]
#write_log(f"Données horaires par plage calculées : {hourly_data.to_string()}")

# Palette de couleurs fixe pour chaque plage horaire
color_mapping = {f"{start}h-{end}h": color for (start, end), color in zip(parsed_time_ranges, ["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A"])}

# Création des diagrammes en cercle pour chaque jour
#write_log("Création des diagrammes en cercle pour chaque jour...")
day_charts = st.columns(4)
for i, (day, day_data) in enumerate(hourly_data.iterrows()):
    fig = go.Figure()
    fig.add_trace(go.Pie(
        labels=hourly_data.columns,
        values=[day_data[col] for col in hourly_data.columns],
        name=f"{day}",
        marker_colors=[color_mapping[col] for col in hourly_data.columns]  # Appliquer les couleurs fixes
    ))

    fig.update_layout(
        title=f"{get_french_day(day) + day.strftime(' %d/%m/%Y').capitalize()}",
        legend=dict(traceorder="normal")  # Assurer l'ordre constant des légendes
    )
    day_charts[i % 4].plotly_chart(fig, use_container_width=True)

# Création du diagramme en cercle pour la semaine entière
#write_log("Création du diagramme en cercle pour la semaine entière...")
weekly_totals = hourly_data.sum()
fig_weekly = go.Figure()
fig_weekly.add_trace(go.Pie(
    labels=hourly_data.columns,
    values=[weekly_totals[col] for col in hourly_data.columns],
    name="Semaine",
    marker_colors=[color_mapping[col] for col in hourly_data.columns]  # Appliquer les couleurs fixes
))
fig_weekly.update_layout(
    title=f"Répartition des consommations par plages horaires - Semaine n°{week_number} {year}",
    legend=dict(traceorder="normal")  # Assurer l'ordre constant des légendes
)
st.plotly_chart(fig_weekly, use_container_width=True)


