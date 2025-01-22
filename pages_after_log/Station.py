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

# Prétraitement de la colonne "Jour"
daily_data["Jour"] = pd.to_datetime(daily_data["Jour"], errors='coerce')
filtered_data = daily_data[(daily_data["Jour"] >= pd.Timestamp(start_date)) & (daily_data["Jour"] <= pd.Timestamp(end_date))]

# Fonction pour regrouper par plage de temps
def group_by_timeframe(data, timeframe):
    if timeframe == "Semaine":
        data["Temps"] = data["Jour"].dt.to_period("W-SUN").apply(lambda r: r.start_time)
    elif timeframe == "Mois":
        data["Temps"] = data["Jour"].dt.to_period("M").apply(lambda r: r.start_time)
    elif timeframe == "Année":
        data["Temps"] = data["Jour"].dt.to_period("A").apply(lambda r: r.start_time)
    else:
        data["Temps"] = data["Jour"]

    # Somme des variables numériques par période
    numeric_columns = data.select_dtypes(include=[np.number]).columns
    grouped_data = data.groupby("Temps")[numeric_columns].sum().reset_index()
    return grouped_data

# Regrouper les données selon la plage de temps
grouped_data = group_by_timeframe(filtered_data, timeframe)

# Variables à analyser
variables = ["Consomation eau général", "Station pre-traitement", "Entrée Bassin", "Sortie Bassin"]
result_data = grouped_data[["Temps"] + [var for var in variables if var in grouped_data.columns]]

# Calcul des volumes entrants et sortants
if "Consomation eau général" in result_data.columns and "Sortie Bassin" in result_data.columns:
    result_data["Volume Non Sortant"] = result_data["Consomation eau général"] - result_data["Sortie Bassin"]

# Afficher le tableau regroupé
st.write("### Données regroupées")
st.dataframe(result_data)

# Création du graphique
fig = go.Figure()
colors = ["blue", "green", "orange", "purple", "red"]

for var, color in zip(variables + ["Volume Non Sortant"], colors):
    if var in result_data.columns:
        fig.add_trace(go.Scatter(
            x=result_data["Temps"],
            y=result_data[var],
            mode="lines+markers",
            name=var,
            line=dict(color=color)
        ))

# Configurer le graphique
fig.update_layout(
    title="Consommation d'Eau par Secteur",
    xaxis_title="Période",
    yaxis_title="Volume (m³)",
    legend=dict(orientation="h")
)

st.plotly_chart(fig, use_container_width=True)

# Analyse et affichage des volumes entrants et sortants
st.write("### Analyse des volumes entrants et sortants")
if "Consomation eau général" in result_data.columns and "Sortie Bassin" in result_data.columns:
    # Calcul des volumes totaux
    total_entree = result_data["Consomation eau général"].sum()
    total_sortie = result_data["Sortie Bassin"].sum()

    if total_entree > 0:  # Éviter les divisions par zéro
        pourcentage_sortie = (total_sortie / total_entree) * 100
    else:
        pourcentage_sortie = 0

    # Afficher les résultats
    st.write(f"Volume Total Entrant : **{total_entree:.2f} m³**")
    st.write(f"Volume Total Sortant : **{total_sortie:.2f} m³**")
    st.write(f"Pourcentage d'eau ressortant : **{pourcentage_sortie:.2f}%**")

    # Vérification des valeurs pour le diagramme
    if total_entree > total_sortie >= 0:
        # Diagramme en cercle
        fig_donut = go.Figure()
        fig_donut.add_trace(go.Pie(
            labels=["Volume Entrant", "Volume Sortant"],
            values=[total_entree - total_sortie, total_sortie],
            hole=0.5,
            marker=dict(colors=["skyblue", "orange"])
        ))
        fig_donut.update_layout(
            title="Répartition des Volumes d'Eau",
            legend=dict(orientation="h"),
        )
        st.plotly_chart(fig_donut, use_container_width=True)
    else:
        st.warning("Les volumes calculés ne sont pas valides pour tracer un diagramme.")
else:
    st.error("Colonnes nécessaires non disponibles pour l'analyse des volumes entrants et sortants.")

