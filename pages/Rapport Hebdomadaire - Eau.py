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

# Fonction pour écrire dans un fichier log
def write_log(message):
    with open("log.txt", "a") as log_file:
        log_file.write(f"{datetime.now()} - {message}\n")



# Charger les données Excel
write_log("Chargement du fichier Excel...")
file_path = "tableau de bord Wit.xlsx"
data = pd.ExcelFile(file_path)
write_log(f"Fichier chargé avec succès : {data.sheet_names}")


# Charger les données horaires
write_log("Chargement des données horaires...")
df_hourly = data.parse("Conso_h")
write_log(f"Aperçu des données horaires : {df_hourly.head().to_string()}")

# Configurer la page
st.title("Rapport Hebdomadaire - EAU")

# Create a horizontal layout for filters
col1, col2, col3, col4, col5 = st.columns([1.8, 1.2, 1.2, 1.8, 1.8])

with col1:

    # Sélection de la semaine
    current_date = datetime.now()
    default_start_date = (current_date - timedelta(days=current_date.weekday(), weeks=1)).date()
    week_number = st.number_input("Choisissez le numéro de la semaine :", value=default_start_date.isocalendar()[1], step=1)
    write_log(f"Numéro de la semaine sélectionnée : {week_number}")

with col2:

    year = st.number_input("Choisissez l'année :", value=default_start_date.year, step=1)
    write_log(f"Année sélectionnée : {year}")

with col3:

    # Choix de l'heure de début de journée
    start_hour = st.number_input("Heure de début de journée :", min_value=0, max_value=23, value=5, step=1)
    write_log(f"Heure de début de journée sélectionnée : {start_hour}")
with col4:
    # Définir les plages horaires
    default_time_ranges = [(5, 16), (16, 21), (21, 5)]
    time_ranges = st.text_input(
        "Définissez les plages horaires (format : hh-hh,hh-hh,...) :",
        value=','.join([f"{start}-{end}" for start, end in default_time_ranges])
    )
    try:
        parsed_time_ranges = [(int(start), int(end)) for start, end in (range_.split('-') for range_ in time_ranges.split(','))]
        write_log(f"Plages horaires sélectionnées : {parsed_time_ranges}")
    except ValueError:
        st.error("Format des plages horaires invalide. Utilisez le format hh-hh,hh-hh,...")
        write_log("Erreur : Format des plages horaires invalide.")
        parsed_time_ranges = default_time_ranges

# Filtrer les données horaires pour la semaine sélectionnée
write_log("Conversion des dates horaires et ajout des colonnes Semaine et Annee...")
df_hourly["DateTime"] = pd.to_datetime(df_hourly["Date /h"], errors='coerce')
df_hourly["Semaine"] = df_hourly["DateTime"].dt.isocalendar().week
df_hourly["Annee"] = df_hourly["DateTime"].dt.year
write_log("Dates horaires converties avec succès.")

write_log("Filtrage des données horaires pour la semaine sélectionnée...")
filtered_data = df_hourly[(df_hourly["Semaine"] == week_number) & (df_hourly["Annee"] == year)]
filtered_data = filtered_data[filtered_data["DateTime"].dt.hour >= start_hour]
filtered_data = filtered_data[filtered_data["DateTime"] < (filtered_data["DateTime"].max() + timedelta(days=1))]
write_log(f"Données horaires filtrées : {filtered_data.to_string()}")

if filtered_data.empty:
    st.warning("Aucune donnée disponible pour la semaine sélectionnée.")
    write_log("Aucune donnée disponible pour la semaine sélectionnée.")
else:
    # Ajuster les données pour refléter les jours de 5h à 5h (ou heure choisie)
    write_log("Ajustement des données horaires pour le découpage des jours...")
    filtered_data["Jour"] = (filtered_data["DateTime"] - pd.to_timedelta((filtered_data["DateTime"].dt.hour < start_hour).astype(int), unit="D")).dt.date

    # Exclure les colonnes non numériques et celles contenant "Cpt" pour l'agrégation
    numeric_columns = filtered_data.select_dtypes(include=['number']).columns
    numeric_columns = [col for col in numeric_columns if "Cpt" not in col]
    numeric_columns = [col for col in numeric_columns if "eau" in col.lower()]
    daily_data = filtered_data.groupby("Jour")[numeric_columns].sum()

    # S'assurer que l'index est au format datetime
    daily_data.index = pd.to_datetime(daily_data.index)

    # Limiter aux jours de Lundi (0) à Dimanche (6)
    daily_data = daily_data.loc[daily_data.index.dayofweek < 7]

    write_log(f"Données journalières calculées : {daily_data.to_string()}")

    # Création de l'histogramme empilé
    write_log("Création de l'histogramme empilé...")
    fig = go.Figure()
    for col in ["Consomation eau ballon", "Consomation eau laveuse", "Consomation eau chauferie"]:
        if col in daily_data.columns:
            fig.add_trace(go.Bar(
                x=daily_data.index,
                y=daily_data[col],
                name=col
            ))



    # Ajouter une colonne "Autres"
    if "Consomation eau général" in daily_data.columns:
        daily_data["Autres"] = daily_data["Consomation eau général"] - (
            daily_data.get("Consomation eau ballon", 0) +
            daily_data.get("Consomation eau laveuse", 0) +
            daily_data.get("Consomation eau chauferie", 0)
        ).clip(lower=0)
            
        
        fig.add_trace(go.Bar(
            x=daily_data.index,
            y=daily_data["Autres"],
            name="Autres"
        ))

    # Configurer et afficher l'histogramme
    fig.update_layout(
        template="plotly_white",
        barmode="stack",
        title=f"Consommation Générale d'Eau - Semaine {week_number} {year}",
        xaxis_title="Jour",
        yaxis_title="Consommation (m³)",
        legend_title="Catégories",
    )
    st.plotly_chart(fig, use_container_width=True)

    # Ajouter un filtre pour n'afficher que les colonnes contenant "eau"
    filtered_columns = [col for col in daily_data.columns if "eau" in col.lower()]
    filtered_table = daily_data[filtered_columns]


    # Afficher le tableau des valeurs de consommation pour la semaine
    st.write("### Données de consommation sur la semaine")
    st.dataframe(daily_data)

# Créer les colonnes pour les plages horaires
write_log("Calcul des consommations par plages horaires...")
hourly_data = []
for start, end in parsed_time_ranges:
    col_name = f"{start}h-{end}h"
    if start < end:
        hourly_data.append(
            filtered_data[(filtered_data["DateTime"].dt.hour >= start) & (filtered_data["DateTime"].dt.hour < end)]
            .groupby("Jour")["Consomation eau général"].sum()
            .rename(col_name)
        )
    else:
        hourly_data.append(
            filtered_data[(filtered_data["DateTime"].dt.hour >= start) | (filtered_data["DateTime"].dt.hour < end)]
            .groupby("Jour")["Consomation eau général"].sum()
            .rename(col_name)
        )
hourly_data = pd.concat(hourly_data, axis=1)

# Garantir un ordre constant des colonnes
hourly_data = hourly_data[[f"{start}h-{end}h" for start, end in parsed_time_ranges]]
write_log(f"Données horaires par plage calculées : {hourly_data.to_string()}")

# Palette de couleurs fixe pour chaque plage horaire
color_mapping = {f"{start}h-{end}h": color for (start, end), color in zip(parsed_time_ranges, ["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A"])}

# Création des diagrammes en cercle pour chaque jour
write_log("Création des diagrammes en cercle pour chaque jour...")
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
write_log("Création du diagramme en cercle pour la semaine entière...")
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


