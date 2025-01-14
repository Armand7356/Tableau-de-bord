import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import io
import requests
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta
import locale

# Configure Streamlit page layout
st.set_page_config(page_title="Tableau de bord", layout="wide")


# Fonction pour écrire dans un fichier log
def write_log(message):
    with open("log.txt", "a") as log_file:
        log_file.write(f"{datetime.now()} - {message}\n")
        
# Charger les données Excel
write_log("Chargement du fichier Excel...")
file_path = "tableau de bord Wit.xlsx"
data = pd.ExcelFile(file_path)
write_log(f"Fichier chargé avec succès : {data.sheet_names}")

# Load data from specific sheets
hourly_data = data.parse('Conso_h')
daily_data = data.parse('Conso_jour')
weekly_data = data.parse('Conso_semaine')

# Streamlit app
st.title("Visualisation des Données du Tableau de Bord")

# Create a horizontal layout for filters
col1, col2, col3, col4, col5 = st.columns([1, 1.2, 1.2, 1.2, 1.8])

# Filter 1: Temporisation
with col1:
    timeframe = st.selectbox("Temporisation", ["Heures", "Jours", "Semaines"])

# Filter 2: Type de graphique
with col2:
    graph_type = st.selectbox("Type de graphique", ["Graphique linéaire", "Camembert", "Histogramme"])

# Map the selected timeframe to the dataset
if timeframe == "Heures":
    df = hourly_data
    date_col = "Date /h"
elif timeframe == "Jours":
    df = daily_data
    date_col = "Jour"
else:
    df = weekly_data
    date_col = "Semaines"  # Adjust if column name differs in your dataset

# Vérification de l'existence de la colonne
if date_col not in df.columns:
    st.error(f"La colonne '{date_col}' est introuvable dans la feuille sélectionnée. Vérifiez le fichier Excel.")
else:
    # Convert the date column for filtering
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

    # Déterminez la plage de dates
    min_date, max_date = df[date_col].min(), df[date_col].max()

    # Filters: Date range, columns, etc.
    with col3:
        start_date = st.date_input("Début", value=min_date, min_value=min_date, max_value=max_date)
    with col4:
        end_date = st.date_input("Fin", value=max_date, min_value=min_date, max_value=max_date)
    with col5:
        columns = st.multiselect("Données à observer", df.columns[1:], help="Choisissez les données à afficher.")

    # Seconde ligne pour les coûts par unité d'énergie
    st.write("### Coût par unité d'énergie (modifiable)")
    cost_col1, cost_col2, cost_col3 = st.columns([1, 1, 1])
    with cost_col1:
        cost_water = st.number_input("Prix eau (€/m³)", value=2.5, step=0.1)
    with cost_col2:
        cost_elec = st.number_input("Prix électricité (€/kWh)", value=0.15, step=0.01)
    with cost_col3:
        cost_gas = st.number_input("Prix gaz (€/kWh)", value=0.08, step=0.01)

    
    ######
    # Récupération des données filtrées
    if not columns:
           st.warning("Veuillez sélectionner au moins une colonne pour visualiser les données.")
    else:
           filtered_data = df[(df[date_col] >= pd.to_datetime(start_date)) & (df[date_col] <= pd.to_datetime(end_date))]
           filtered_data = filtered_data[[date_col] + columns]
           all_data = df[[date_col] + columns]  # Toutes les données pour interactivité
           # Dictionnaire des unités
           units = {col: 'm³' if 'eau' in col.lower() else 'kWh' for col in columns}
    
           # Ajout des unités comme légende
           columns_with_units = [f"{col} ({units[col]})" for col in columns]
    
           # Calcul des statistiques
           stats = round(filtered_data[columns].describe().T[['mean', 'std', 'min', 'max']],1)  #.astype(int)
           stats['Date min'] = [
               filtered_data.loc[filtered_data[col].idxmin(), date_col] if not filtered_data[col].isnull().all() else None
               for col in columns
           ]
           stats['Date max'] = [
               filtered_data.loc[filtered_data[col].idxmax(), date_col] if not filtered_data[col].isnull().all() else None
               for col in columns
           ]
           stats['Somme'] = filtered_data[columns].sum().astype(int)
           stats['Coût (€)'] = [
               row['Somme'] * (cost_water if 'eau' in col.lower() else cost_elec if 'elec' in col.lower() else cost_gas)
               for col, row in stats.iterrows()
           ]
           stats = stats.rename(columns={
               'mean': 'Moyenne',
               'std': 'Écart type',
               'min': 'Minimum',
               'max': 'Maximum'
           })
    
           # Affichage des données et statistiques
           col_data, col_stats = st.columns([5, 10])
    
           with col_data:
               st.write("### Aperçu des données")
               st.dataframe(filtered_data, height=300)
    
           with col_stats:
               st.write("### Statistiques des données")
               st.dataframe(stats)
    
           # Téléchargement des données
           csv_data = filtered_data.to_csv(index=False).encode('utf-8')
           st.download_button(
               label="Télécharger les données en CSV",
               data=csv_data,
               file_name="données_filtrées.csv",
               mime="text/csv"
           )
    
    
            # Visualisation
           st.write(f"**{graph_type} des données sélectionnées ({timeframe})**")

    if graph_type == "Graphique linéaire":
            fig = go.Figure()
            for col in columns:
                # Tracer des données complètes pour interactivité
                fig.add_trace(go.Scatter(
                    x=all_data[date_col],
                    y=all_data[col],
                    mode='lines+markers',
                    name=col,
                    line=dict(width=1),
                    opacity=0.3
                ))
                # Tracer les données filtrées
                fig.add_trace(go.Scatter(
                    x=filtered_data[date_col],
                    y=filtered_data[col],
                    mode='lines+markers',
                    name=f"{col} (sélection)",
                    line=dict(width=3)
                ))
            fig.update_layout(
                title="Graphique Linéaire",
                xaxis_title="Date",
                yaxis_title="Valeurs",
                xaxis=dict(range=[pd.to_datetime(start_date), pd.to_datetime(end_date)])
            )
            st.plotly_chart(fig, use_container_width=True)

    elif graph_type == "Camembert":
            if len(columns) < 2:
                st.error("Le camembert nécessite au moins deux colonnes pour visualiser un rapport.")
            else:
                pie_data = filtered_data[columns].sum()
                fig = px.pie(
                    values=pie_data.values,
                    names=columns,
                    title=f"Répartition entre {start_date} et {end_date}"
                )
                st.plotly_chart(fig, use_container_width=True)

    elif graph_type == "Histogramme":
            fig = go.Figure()
            for col in columns:
                # Tracer des données complètes pour interactivité
                #fig.add_trace(go.Bar(
                #    x=all_data[date_col],
                #    y=all_data[col],
                #    name=col,
                #    opacity=0.3
                #))
                # Tracer les données filtrées
                aggregated_data = filtered_data.groupby(date_col)[col].sum()
                fig.add_trace(go.Bar(
                    x=aggregated_data.index,
                    y=aggregated_data.values,
                    name=f"{col} (sélection)"
                ))
            fig.update_layout(
                title=f"Histogramme ({timeframe})",
                xaxis_title="Date",
                yaxis_title="Valeurs",
                xaxis=dict(range=[pd.to_datetime(start_date), pd.to_datetime(end_date)])
            )
            st.plotly_chart(fig, use_container_width=True)
