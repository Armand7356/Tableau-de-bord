import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from scipy.stats import linregress
import numpy as np
from datetime import datetime

# Fonction pour charger les données
# Charge les données des différentes feuilles d'un fichier Excel
def load_data(file_path):
    data = pd.ExcelFile(file_path)
    hourly_data = data.parse('Conso_h')  # Consommation horaire
    daily_data = data.parse('Conso_jour')  # Consommation journalière
    weekly_data = data.parse('Conso_semaine')  # Consommation hebdomadaire
    return hourly_data, daily_data, weekly_data

# Charger les données
file_path = "tableau de bord Wit.xlsx"
hourly_data, daily_data, weekly_data = load_data(file_path)

# Page principale
st.title("Consommation Générale")
st.write("Visualisation des consommations générales (eau, électricité, gaz)")

# Filtres
# Permet de sélectionner la temporalité et la plage de dates
col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1.5])

with col1:
    timeframe = st.selectbox("Temporisation", ["Jour","Semaine", "Mois", "Année", "Tout"])
with col2:
    start_date = st.date_input("Début", value=daily_data['Jour'].min())
with col3:
    end_date = st.date_input("Fin", value=min(daily_data['Jour'].max().date(), datetime.today().date()))

# Sélection des données selon la temporisation
if timeframe == "Jour":
    # Regrouper les données par jour
    df = daily_data.resample('D', on="Jour").sum().reset_index()
    date_col = "Jour"
elif timeframe == "Semaine":
    # Regrouper les données par semaine
    df = daily_data.resample('W', on="Jour").sum().reset_index()
    date_col = "Jour"
elif timeframe == "Mois":
    # Regrouper les données par mois
    df = daily_data.resample('ME', on="Jour").sum().reset_index()
    date_col = "Jour"
elif timeframe == "Année":
    # Regrouper les données par année
    df = daily_data.resample('Y', on="Jour").sum().reset_index()
    date_col = "Jour"
else:  # Tout
    # Toutes les données sans regroupement
    df = daily_data
    date_col = "Jour"

# Filtrer les données selon la plage de dates
filtered_data = df[(df[date_col] >= pd.Timestamp(start_date)) & (df[date_col] <= pd.Timestamp(end_date))]

# Supprimer les valeurs à zéro, sauf si la temporisation est "Jour"
if timeframe != "Jour":
    filtered_data = filtered_data[(filtered_data["Consomation eau général"] > 0) | (filtered_data["Consomation gaz général"] > 0) | (filtered_data["Consomation elec général"] > 0)]

# Ajouter les colonnes nécessaires
filtered_data = filtered_data[["Jour", "Consomation eau général", "Consomation gaz général", "Consomation elec général"]]

# Graphique avec deux échelles (m³ pour l'eau, kWh pour gaz et électricité)
fig = go.Figure()

# Variables et leurs couleurs/échelles
variables = ["Consomation gaz général", "Consomation elec général", "Consomation eau général"]
colors = ["green", "orange","blue"]
units = ["kWh", "kWh","m³"]

# Tracer les séries de données avec ajustement des échelles
for var, color, unit in zip(variables, colors, units):
    axis = "y" if var != "Consomation eau général" else "y2"  # Utiliser y2 pour l'eau
    scaling_factor = 1 if var != "Consomation eau général" else 1  # Échelle pour l'eau
    fig.add_trace(go.Scatter(
        x=filtered_data[date_col],
        y=filtered_data[var] * scaling_factor,  # Ajuster les valeurs en fonction de l'échelle
        mode="lines+markers",
        name=f"{var} ({unit})",
        line=dict(color=color),
        yaxis=axis  # Associer à l'axe principal ou secondaire
    ))

# Ajouter une courbe de tendance linéaire pour chaque variable
for var, color, unit in zip(variables, colors, units):
    scaling_factor = 1 if var != "Consomation eau général" else 1
    slope, intercept, _, _, _ = linregress(range(len(filtered_data)), filtered_data[var] * scaling_factor)
    trendline = [slope * x + intercept for x in range(len(filtered_data))]
    axis = "y" if var != "Consomation eau général" else "y2"
    fig.add_trace(go.Scatter(
        x=filtered_data[date_col],
        y=trendline,  # Tendance linéaire ajustée à l'échelle
        mode="lines",
        name=f"Tendance {var} ({unit})",
        line=dict(dash="dash", color=color),
        yaxis=axis
    ))

# Calcul automatique des bornes
y1_min, y1_max = 0, max(filtered_data[["Consomation gaz général", "Consomation elec général"]].max())

# Calcul des tailles de grille
y1_dtick = (y1_max - y1_min) / 10  # 10 intervalles pour l'axe principal
y2_dtick = (y1_max - y1_min) / 1000  # 10 intervalles pour l'axe principal

# Appliquer les bornes et les grilles
fig.update_layout(
    yaxis=dict(
        title="Consommation Gaz/Élec (kWh)",
        titlefont=dict(color="orange"),
        side="left",
        range=[0, y1_max * 1.1]  # Ajouter une marge de 10 %
    ),
    yaxis2=dict(
        title="Consommation Eau (m³)",
        titlefont=dict(color="blue"),
        overlaying="y",
        side="right",
        range=[0, y1_max*0.01 * 1.1]
    ),
    legend=dict(
        orientation="h",  # Orientation horizontale
        yanchor="top",    # Alignement vertical
        y=-0.2,           # Position verticale (négatif pour placer en dessous)
        xanchor="center", # Alignement horizontal
        x=0.5             # Centrer horizontalement
    )
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

# Créer un DataFrame pour les statistiques
stats_df = pd.DataFrame(stats)
stats_df.iloc[:, 1:4] = stats_df.iloc[:, 1:4].round(0)  # Arrondir les valeurs numériques

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



