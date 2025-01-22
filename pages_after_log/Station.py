import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from scipy.stats import linregress
import numpy as np
from datetime import datetime

# Fonction pour charger les données
def load_data(file_path):
    data = pd.ExcelFile(file_path)
    daily_data = data.parse('Conso_jour')  # Consommation journalière
    return daily_data

# Charger les données
file_path = "tableau de bord Wit.xlsx"
daily_data = load_data(file_path)

# Page principale
st.title("Analyse de l'Eau")
st.write("Visualisation des consommations d'eau dans les différentes parties de l'usine")

# Filtres
col1, col2, col3 = st.columns([1, 1, 1.5])

with col1:
    timeframe = st.selectbox("Temporisation", ["Semaine", "Mois", "Année", "Tout"])
with col2:
    start_date = st.date_input("Début", value=daily_data['Jour'].min())
with col3:
    end_date = st.date_input("Fin", value=min(daily_data['Jour'].max().date(), datetime.today().date()))

# Sélection des données selon la temporisation
def group_by_timeframe(data, timeframe, date_col):
    if timeframe == "Semaine":
        data["Semaine"] = data[date_col].dt.to_period("W-SUN").apply(lambda r: r.start_time)
        grouped_data = data.groupby("Semaine").sum().reset_index()
    elif timeframe == "Mois":
        data["Mois"] = data[date_col].dt.to_period("M").apply(lambda r: r.start_time)
        grouped_data = data.groupby("Mois").sum().reset_index()
    elif timeframe == "Année":
        data["Année"] = data[date_col].dt.to_period("A").apply(lambda r: r.start_time)
        grouped_data = data.groupby("Année").sum().reset_index()
    else:  # Tout
        grouped_data = data
    return grouped_data

daily_data["Jour"] = pd.to_datetime(daily_data["Jour"])  # S'assurer que "Jour" est au format datetime
df = group_by_timeframe(daily_data, timeframe, "Jour")

# Filtrer les données selon la plage de dates
filtered_data = df[(df["Jour"] >= pd.Timestamp(start_date)) & (df["Jour"] <= pd.Timestamp(end_date))]

# Variables à analyser
variables = ["Consomation eau général", "Station pre-traitement", "Entrée Bassin", "Sortie Bassin"]
filtered_data = filtered_data[["Jour"] + variables]

# Graphique avec les variables sélectionnées (Graphiques linéaires)
fig = go.Figure()
colors = ["blue", "green", "orange", "purple"]

for var, color in zip(variables, colors):
    fig.add_trace(go.Scatter(
        x=filtered_data["Jour"],
        y=filtered_data[var],
        mode="lines+markers",
        name=var,
        line=dict(color=color)
    ))

# Configurer le graphique
fig.update_layout(
    title="Consommation d'Eau par Secteur",
    xaxis_title="Date",
    yaxis_title="Volume (m³)",
    legend=dict(orientation="h")
)

st.plotly_chart(fig, use_container_width=True)

# Analyse des volumes entrants et sortants
st.write("### Analyse des Volumes Entrants et Sortants")

# Convertir les colonnes en type numérique
for var in variables:
    filtered_data[var] = pd.to_numeric(filtered_data[var], errors='coerce').fillna(0)

# Calcul des volumes entrants et sortants
total_entree = filtered_data["Consomation eau général"].sum()
total_sortie = filtered_data["Entrée Bassin"].sum()

# Pourcentage d'eau entrant ressortant
pourcentage_sortie = (total_sortie / total_entree) * 100 if total_entree > 0 else 0

# Affichage des résultats
st.write(f"Volume Total Entrant : **{total_entree:.2f} m³**")
st.write(f"Volume Total Sortant (Entrée Bassin) : **{total_sortie:.2f} m³**")
st.write(f"Pourcentage d'eau entrant ressortant : **{pourcentage_sortie:.2f}%**")

# Diagramme en anneau pour visualiser la répartition
fig_donut = go.Figure()
fig_donut.add_trace(go.Pie(
    labels=["Eau Entrante", "Eau Sortante"],
    values=[total_entree - total_sortie, total_sortie],
    hole=0.5,
    marker=dict(colors=["skyblue", "orange"])
))

fig_donut.update_layout(title="Répartition des Volumes d'Eau")
st.plotly_chart(fig_donut, use_container_width=True)
