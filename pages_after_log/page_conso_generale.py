import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from scipy.stats import linregress
import numpy as np
from datetime import datetime

# Fonction pour charger les données
def load_data(file_path):
    data = pd.ExcelFile(file_path)
    hourly_data = data.parse('Conso_h')
    daily_data = data.parse('Conso_jour')
    weekly_data = data.parse('Conso_semaine')
    return hourly_data, daily_data, weekly_data

# Charger les données
file_path = "tableau de bord Wit.xlsx"
hourly_data, daily_data, weekly_data = load_data(file_path)

# Page principale
st.title("Consommation Générale")
st.write("Visualisation des consommations générales (eau, électricité, gaz)")

# Filtres
col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1.5])

with col1:
    timeframe = st.selectbox("Temporisation", ["Jour","Semaine", "Mois", "Année", "Tout"])
with col2:
    start_date = st.date_input("Début", value=daily_data['Jour'].min())
with col3:
    end_date = st.date_input("Fin", value=min(daily_data['Jour'].max().date(), datetime.today().date()))

# Sélection des données selon la temporisation
if timeframe == "Jour":
    df = daily_data.resample('D', on="Jour").sum().reset_index()
    date_col = "Jour"
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

# Supprimer les valeurs à zéro, sauf si la temporisation est "Jour"
if timeframe != "Jour":
    filtered_data = filtered_data[(filtered_data["Consomation eau général"] > 0) | (filtered_data["Consomation gaz général"] > 0) | (filtered_data["Consomation elec général"] > 0)]

# Supprimer les valeurs à zéro, sauf si la temporisation est "Jour"
if timeframe != "Jour":
    filtered_data = filtered_data[(filtered_data["Consomation eau général"] > 0) | (filtered_data["Consomation gaz général"] > 0) | (filtered_data["Consomation elec général"] > 0)]

# Ajouter les colonnes nécessaires
filtered_data = filtered_data[["Jour", "Consomation eau général", "Consomation gaz général", "Consomation elec général"]]

# Graphique avec deux échelles (m³ pour l'eau, kWh pour gaz et électricité)
fig = go.Figure()

variables = ["Consomation eau général", "Consomation gaz général", "Consomation elec général"]
colors = ["blue", "green", "orange"]
units = ["m³", "kWh", "kWh"]

for var, color, unit in zip(variables, colors, units):
    axis = "y" if var != "Consomation eau général" else "y2"  # Utiliser y2 pour l'eau
    scaling_factor = 1 if var != "Consomation eau général" else 0.1
    fig.add_trace(go.Scatter(
        x=filtered_data[date_col],
        y=filtered_data[var] * scaling_factor,
        mode="lines+markers",
        name=f"{var} ({unit})",
        line=dict(color=color),
        yaxis=axis  # Spécifier l'axe
    ))

# Ajouter une courbe de tendance linéaire pour chaque variable
for var, color, unit in zip(variables, colors, units):
    scaling_factor = 1 if var != "Consomation eau général" else 0.1
    slope, intercept, _, _, _ = linregress(range(len(filtered_data)), filtered_data[var] * scaling_factor)
    trendline = [slope * x + intercept for x in range(len(filtered_data))]
    axis = "y" if var != "Consomation eau général" else "y2"  # Utiliser y2 pour l'eau
    fig.add_trace(go.Scatter(
        x=filtered_data[date_col],
        y=trendline,
        mode="lines",
        name=f"Tendance {var} ({unit})",
        line=dict(dash="dash", color=color),
        yaxis=axis  # Spécifier l'axe
    ))

# Configurer l'axe secondaire
fig.update_layout(
    title="Consommation Générale avec Courbes de Tendance",
    xaxis_title="Date",
    yaxis=dict(
        title="Consommation Gaz/Élec (kWh)",
        titlefont=dict(color="orange"),
        side="left"
    ),
    yaxis2=dict(
        title="Consommation Eau (m³)",
        titlefont=dict(color="blue"),
        overlaying="y",
        side="right"
    ),
    legend=dict(orientation="h"),
)

st.plotly_chart(fig, use_container_width=True)

# Calcul des statistiques
stats = {
    "Variable": ["Eau (m³)", "Gaz (kWh)", "Électricité (kWh)"],
    "Moyenne": [filtered_data[var].mean() for var in variables],
    "Somme": [filtered_data[var].sum() for var in variables],
    "Prix (€)": [
        filtered_data["Consomation eau général"].sum() * 2.5,
        filtered_data["Consomation gaz général"].sum() * 0.08,
        filtered_data["Consomation elec général"].sum() * 0.15
    ],
    "Tendance (Coef directeur)": [
        linregress(range(len(filtered_data)), filtered_data[var])[0] for var in variables
    ]
}

stats_df = pd.DataFrame(stats)
stats_df.iloc[:, 1:4] = stats_df.iloc[:, 1:4].round(0)

# Affichage du tableau récapitulatif
st.write("### Tableau Récapitulatif")
st.dataframe(stats_df)

# Option de téléchargement
csv_data = filtered_data.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Télécharger les données filtrées",
    data=csv_data,
    file_name="consommation_generale.csv",
    mime="text/csv"
)
