# === CONFIGURATION ET IMPORTS ===
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import locale

# Configuration pour avoir les jours de la semaine en français
#locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
page = "elec"
# Fonction pour récupérer le jour en français
def get_french_day(date):
    return date.strftime('%A').capitalize()

# === CHARGEMENT DES DONNÉES ===
st.title("Rapport plage hoiraire "+page)

# Chargement via la fonction standard
file_path = "tableau de bord Wit.xlsx"

def load_data(file_path):
    """
    Charge les données depuis un fichier Excel.

    Renvoie :
    - daily_data : DataFrame de la consommation horaire
    - station_data : DataFrame des données par station (si besoin)
    """
    xls = pd.ExcelFile(file_path)
    
    if "Conso_h" in xls.sheet_names:
        daily_data = pd.read_excel(xls, sheet_name="Conso_h")
    else:
        st.error("La feuille 'Conso_h' est manquante dans le fichier Excel.")
        st.stop()
    
    if "Station" in xls.sheet_names:
        station_data = pd.read_excel(xls, sheet_name="Station")
    else:
        station_data = pd.DataFrame()  # Crée un DataFrame vide si la feuille n'existe pas

    return daily_data, station_data

# Appel de la fonction existante
daily_data, station_data = load_data(file_path)

# On travaille avec daily_data directement
data = daily_data.copy()

# Vérification que Date /h existe
if "Date /h" not in data.columns:
    st.error("La colonne 'Date /h' est manquante dans le fichier fourni.")
    st.stop()

# Traitement Date /h
data['Date /h'] = pd.to_datetime(data['Date /h'])
data['Jour'] = data['Date /h'].dt.date


# Préparation des colonnes
if "Date /h" not in data.columns:
    st.error("La colonne 'Date /h' est manquante dans le fichier.")
    st.stop()

data['Date /h'] = pd.to_datetime(data['Date /h'])
data['Jour'] = data['Date /h'].dt.date

# === SÉLECTION DE LA SEMAINE ET DE L'ANNÉE ===
current_year = datetime.now().year
current_week = datetime.now().isocalendar()[1]

year = st.number_input("Année :", min_value=2020, max_value=current_year, value=current_year)
week_number = st.number_input("Numéro de la semaine :", min_value=1, max_value=53, value=current_week-1)

filtered_data = data[data['Date /h'].dt.isocalendar().week == week_number]
filtered_data = filtered_data[filtered_data['Date /h'].dt.year == year]

# === SÉLECTION DU TYPE DE CONSOMMATION ===
if page=="eau":
    filter_option = st.radio(
        "Choisissez les données à analyser :",
        options=["Général", "MP", "Laveuses", "Personnalisé"],
        horizontal=True
    )
else:
    filter_option = st.radio(
        "Choisissez les données à analyser :",
        options=["Général", "Personnalisé"],
        horizontal=True
    )

if filter_option == "Personnalisé":
    available_columns = [col for col in data.columns if "Consomation "+page in col]
    selected_custom_columns = st.multiselect("Choisissez les colonnes à analyser :", available_columns)
    selected_columns = selected_custom_columns
else:
    selected_columns = []
    for col in filtered_data.columns:
        if "Consomation "+page in col:
            if filter_option == "Général" and "général" in col.lower():
                selected_columns.append(col)
            elif filter_option == "MP" and "MP" in col:
                selected_columns.append(col)
            elif filter_option == "Laveuses" and "laveuse" in col.lower():
                selected_columns.append(col)

# === DÉFINITION DES PLAGES HORAIRES ===
st.subheader("Définissez les plages horaires (en heures)")
nb_separateurs = st.number_input("Nombre de séparateurs :", min_value=1, max_value=12, value=3)

# Définition manuelle des valeurs par défaut
default_separateurs = [5, 16, 21]

separateurs = []
col_inputs = st.columns(nb_separateurs)
for i in range(nb_separateurs):
    with col_inputs[i]:
        if i < len(default_separateurs):
            valeur_defaut = default_separateurs[i]
        else:
            valeur_defaut = (i+1) * int(24 / (nb_separateurs+1))  # sinon réparti automatiquement
        
        heure = st.number_input(
            f"Séparateur {i+1}",
            min_value=0,
            max_value=23,
            value=valeur_defaut,
            step=1,
            key=f"separator_{i}"
        )
        separateurs.append(heure)


separateurs = sorted(set(separateurs))

# Construction des plages cycliques
plages = []
for i in range(len(separateurs)):
    start = separateurs[i]
    end = separateurs[(i+1) % len(separateurs)]
    plages.append((start, end))
# Appliquer le +1 pour traitement (calculation seulement)

# Palette de couleurs fixes
palette_couleurs = [
    "#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A",
    "#19D3F3", "#FF6692", "#B6E880", "#FF97FF", "#FECB52"
]

# === TRAITEMENT DES CONSOMMATIONS PAR PLAGE ===
daily_by_slot = pd.DataFrame()
for start, end in plages:
    col_name = f"{start}h-{end}h"
    if start < end:
        mask = (filtered_data['Date /h'].dt.hour >= start+1) & (filtered_data['Date /h'].dt.hour < end+1)
    else:
        mask = (filtered_data['Date /h'].dt.hour >= start+1) | (filtered_data['Date /h'].dt.hour < end+1)
    slot_data = filtered_data[mask]
    grouped = slot_data.groupby("Jour")[selected_columns].sum().sum(axis=1)
    daily_by_slot[col_name] = grouped

daily_by_slot = daily_by_slot[[f"{start}h-{end}h" for (start, end) in plages]]
weekly_by_slot = daily_by_slot.sum()
hourly_by_slot = daily_by_slot.copy()

# === VISUALISATION DES DONNÉES ===
# Graphique empilé journalier
fig_stack_pct = go.Figure()
daily_pct = daily_by_slot.div(daily_by_slot.sum(axis=1), axis=0) * 100
for idx, col in enumerate(daily_pct.columns):
    fig_stack_pct.add_trace(go.Scatter(
        x=daily_pct.index,
        y=daily_pct[col],
        mode="lines",
        stackgroup="one",
        name=col,
        hoverinfo="x+y+name",
        line=dict(color=palette_couleurs[idx % len(palette_couleurs)])
    ))
fig_stack_pct.update_layout(
    template="plotly_white",
    title="Répartition journalière par plage horaire",
    xaxis_title="Jour",
    yaxis_title="Pourcentage (%)",
    yaxis=dict(range=[0, 100], ticksuffix="%"),
    legend_title="Plages horaires"
)
st.plotly_chart(fig_stack_pct, use_container_width=True)

# Diagrammes circulaires jour par jour
day_charts = st.columns(4)
for i, (day, day_data) in enumerate(hourly_by_slot.iterrows()):
    fig_day = go.Figure(go.Pie(
        labels=hourly_by_slot.columns,
        values=[day_data[col] for col in hourly_by_slot.columns],
        marker_colors=[palette_couleurs[j % len(palette_couleurs)] for j in range(len(hourly_by_slot.columns))]
    ))
    fig_day.update_layout(title=f"{get_french_day(pd.to_datetime(day))} {pd.to_datetime(day).strftime('%d/%m/%Y')}")
    day_charts[i % 4].plotly_chart(fig_day, use_container_width=True)

# Diagramme de répartition de la semaine
fig_weekly = go.Figure(go.Pie(
    labels=weekly_by_slot.index,
    values=weekly_by_slot.values,
    marker_colors=[palette_couleurs[j % len(palette_couleurs)] for j in range(len(weekly_by_slot.index))]
))
fig_weekly.update_layout(
    title=f"Répartition hebdomadaire - Semaine {week_number}",
    legend_title="Plages horaires"
)
st.plotly_chart(fig_weekly, use_container_width=True)
