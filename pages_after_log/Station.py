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
elif timeframe == "Semaine":
    df = daily_data.resample('W', on="Jour").sum().reset_index()
    date_col = "Jour"
elif timeframe == "Mois":
    df = daily_data.resample('M', on="Jour").sum().reset_index()
    date_col = "Jour"
elif timeframe == "Année":
    df = daily_data.resample('Y', on="Jour").sum().reset_index()
    date_col = "Jour"
else:  # Tout
    df = daily_data
    date_col = "Jour"

# Filtrer les données selon la plage de dates
filtered_data = df[(df[date_col] >= pd.Timestamp(start_date)) & (df[date_col] <= pd.Timestamp(end_date))]

# Variables à analyser
variables = ["Consomation eau général", "Station pre-traitement", "Entrée Bassin", "Sortie Bassin"]
filtered_data = filtered_data[["Jour"] + variables]

# Graphique avec les variables sélectionnées
fig = go.Figure()
colors = ["blue", "green", "orange", "purple"]

for var, color in zip(variables, colors):
    fig.add_trace(go.Bar(
        x=filtered_data[date_col],
        y=filtered_data[var],
        name=var,
        marker=dict(color=color)
    ))

# Configurer l'histogramme
fig.update_layout(
    title="Consommation d'Eau par Secteur",
    xaxis_title="Date",
    yaxis_title="Volume (m³)",
    barmode="stack",
    legend=dict(orientation="h")
)

st.plotly_chart(fig, use_container_width=True)

# Analyse des volumes entrants et sortants
st.write("### Analyse des Volumes Entrants et Sortants")

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
