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
st.title("Rapport Hebdomadaire - EAU")

# Create a horizontal layout for filters
col1, col2, col3, col4 = st.columns([1.9, 1.5, 2.2, 0.5])

with col1:

    # Sélection de la semaine
    current_date = datetime.now()
    default_start_date = (current_date - timedelta(days=current_date.weekday(), weeks=1)).date()
    week_number = st.number_input("Choisissez le numéro de la semaine :", value=default_start_date.isocalendar()[1], step=1)
    #write_log(f"Numéro de la semaine sélectionnée : {week_number}")

with col2:

    year = st.number_input("Choisissez l'année :", value=default_start_date.year, step=1)
    #write_log(f"Année sélectionnée : {year}")

with col4:

    # Choix de l'heure de début de journée
    #start_hour = st.number_input("Heure de début de journée :", min_value=0, max_value=23, value=0, step=1)
    start_hour=0
    #write_log(f"Heure de début de journée sélectionnée : {start_hour}")


# Filtrer les données horaires pour la semaine sélectionnée
#write_log("Conversion des dates horaires et ajout des colonnes Semaine et Annee...")
df_hourly["DateTime"] = pd.to_datetime(df_hourly["Date /h"], errors='coerce')
df_hourly["Semaine"] = df_hourly["DateTime"].dt.isocalendar().week
df_hourly["Annee"] = df_hourly["DateTime"].dt.year
#write_log("Dates horaires converties avec succès.")

#write_log("Filtrage des données horaires pour la semaine sélectionnée...")
filtered_data = df_hourly[(df_hourly["Semaine"] == week_number) & (df_hourly["Annee"] == year)]

# Ajuster la plage de temps : début à start_hour, fin à start_hour + 24h (le lendemain avant la même heure)
filtered_data = filtered_data[
    (filtered_data["DateTime"] >= filtered_data["DateTime"].dt.normalize() + pd.to_timedelta(start_hour, unit="h")) &
    (filtered_data["DateTime"] < filtered_data["DateTime"].dt.normalize() + pd.to_timedelta(start_hour + 24, unit="h"))
]

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
    numeric_columns = [col for col in numeric_columns if "eau" in col.lower()]
    daily_data = filtered_data.groupby("Jour")[numeric_columns].sum()

    # S'assurer que l'index est au format datetime
    daily_data.index = pd.to_datetime(daily_data.index)

    # Limiter aux jours de Lundi (0) à Dimanche (6)
    daily_data = daily_data.loc[daily_data.index.dayofweek < 7]

    #write_log(f"Données journalières calculées : {daily_data.to_string()}")

    # Création de l'histogramme empilé
    #write_log("Création de l'histogramme empilé...")
    
    fig = go.Figure()
    """
    for col in daily_data.columns:
        if "Consomation eau" in col and col != "Consomation eau chaudière vapeur" and col != "Consomation eau général":
            fig.add_trace(go.Bar(
                x=daily_data.index,
                y=daily_data[col],
                name=col.replace("Consomation", "").strip()
            ))
    """
################################
##############################
############################


    

    # Ajout des compteurs de niveau 2 uniquement (hors sous-compteurs ballon)
    for col in daily_data.columns:
        if (
            "Consomation eau" in col and 
            col != "Consomation eau chaudière vapeur" and 
            col != "Consomation eau général" and 
            "MP" not in col
        ):
            fig.add_trace(go.Bar(
                x=daily_data.index,
                y=daily_data[col],
                name=col.replace("Consomation eau", "").strip()
            ))


############################
##############################
################################



    # Ajouter une colonne "Autres"
    if "Consomation eau général" in daily_data.columns:
        columns_to_sum = [col for col in daily_data.columns 
                          if "Consomation eau" in col and 
                          col != "Consomation eau général" and 
                          col != "Consomation eau chaudière vapeur"
                          and "MP" not in col]
        daily_data["eau Autres"] = daily_data["Consomation eau général"] - daily_data[columns_to_sum].sum(axis=1).clip(lower=0)

        fig.add_trace(go.Bar(
            x=daily_data.index,
            y=daily_data["eau Autres"],
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

################################
##############################
############################

############################
##############################
################################

    # Ajouter un filtre pour n'afficher que les colonnes contenant "eau"
    filtered_columns = [col for col in daily_data.columns if "eau" in col.lower()]
    filtered_table = daily_data[filtered_columns]

    # Ajouter les lignes moyenne et somme au tableau des données filtrées
    filtered_table.loc['Moyenne'] = filtered_table.mean()
    filtered_table.loc['Somme'] = filtered_table.sum()-filtered_table.loc['Moyenne']

    # Afficher le tableau des valeurs de consommation pour la semaine
    st.write("### Données de consommation sur la semaine")
    st.dataframe(filtered_table)
###################################


# Définir les plages horaires
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

# Boutons de filtre pour les graphiques
st.markdown("### Choisissez une vue :")
filter_option = st.radio(
    label="",
    options=["Général", "MP", "Laveuses", "Personnalisé"],
    horizontal=True
)

######################################
######################################

st.write("### Répartition journalière par plages horaires (en %)")
# 1. Colonnes sélectionnées selon le filtre

selected_custom_columns = []
if filter_option == "Personnalisé":
    available_columns = [col for col in filtered_data.columns if "Consomation eau" in col]
    selected_custom_columns = st.multiselect(
        "Sélectionnez les données d'eau à visualiser :",
        options=available_columns,
        default=available_columns  # tu peux mettre [] si tu veux aucun par défaut
    )


# 1. Colonnes sélectionnées selon le filtre
selected_columns = []

if filter_option == "Personnalisé":
    selected_columns = selected_custom_columns
else:
    for col in filtered_data.columns:
        if "Consomation eau" not in col:
            continue
        if filter_option == "Général":
            if "général" not in col.lower():
                continue
        elif filter_option == "MP":
            if "MP" not in col:
                continue
        elif filter_option == "Laveuses":
            if "laveuse" not in col.lower():
                continue
        selected_columns.append(col)


# 2. Calcul des consommations par jour et plage horaire
daily_by_slot = pd.DataFrame()

for start, end in parsed_time_ranges:
    col_name = f"{start}h-{end}h"
    start+=1
    end+=1
    if start < end:
        mask = (filtered_data["DateTime"].dt.hour >= start) & (filtered_data["DateTime"].dt.hour < end)
    else:
        mask = (filtered_data["DateTime"].dt.hour >= start) | (filtered_data["DateTime"].dt.hour < end)

    slot_data = filtered_data[mask]
    grouped = slot_data.groupby("Jour")[selected_columns].sum().sum(axis=1)
    daily_by_slot[col_name] = grouped

# Réorganiser l'ordre
daily_by_slot = daily_by_slot[[f"{start}h-{end}h" for start, end in parsed_time_ranges]]

# 3. Calcul des pourcentages
daily_pct = daily_by_slot.div(daily_by_slot.sum(axis=1), axis=0) * 100


# 4. Graphique final
fig_stack_pct = go.Figure()
for col in daily_pct.columns:
    fig_stack_pct.add_trace(go.Scatter(
        x=daily_pct.index,
        y=daily_pct[col],
        mode="lines",
        stackgroup="one",
        name=col,
        hoverinfo="x+y+name"
    ))

fig_stack_pct.update_layout(
    template="plotly_white",
    title=f"Répartition journalière des plages horaires - {filter_option}",
    xaxis_title="Jour",
    yaxis_title="Pourcentage (%)",
    legend_title="Plages horaires",
    yaxis=dict(range=[0, 100], ticksuffix="%")
)

st.plotly_chart(fig_stack_pct, use_container_width=True)




######################################
############################################################################
############################################################################
######################################

# Créer les colonnes pour les plages horaires
#write_log("Calcul des consommations par plages horaires...")
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
#write_log(f"Données horaires par plage calculées : {hourly_data.to_string()}")

# Palette de couleurs fixe pour chaque plage horaire
color_mapping = {f"{start}h-{end}h": color for (start, end), color in zip(parsed_time_ranges, ["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A"])}

"""
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
"""
# Création du diagramme en cercle pour la semaine entière
#write_log("Création du diagramme en cercle pour la semaine entière...")
st.write("### Répartition des consommations par tranches horaires")
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


# Ajouter un diagramme en cercle pour la répartition des volumes consommés
st.write("### Répartition des volumes consommés")
if "filtered_table" in locals() or "filtered_table" in globals():
    consumption_columns = [col for col in filtered_table.columns if "Consomation eau" in col and
                        col != "Consomation eau général" and 
                        "MP" not in col]
    if consumption_columns:
        total_consumptions = filtered_table.loc["Somme", consumption_columns]
        fig_pie = go.Figure()
        fig_pie.add_trace(go.Pie(
            labels=consumption_columns,
            values=total_consumptions,
            hole=0.4,
            marker=dict(colors=go.Figure().layout.template.layout.colorway)
        ))
        fig_pie.update_layout(title=f"Répartition des consommations d'eau - Semaine n°{week_number} {year}")
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.warning("Aucune donnée disponible pour la répartition des consommations d'eau.")



        st.write("### Définir vos plages horaires")

#############################

#############################

#############################
import streamlit as st
from streamlit_elements import elements, mui, sync

#st.set_page_config(layout="wide")

st.title("🕐 Timeline Interactive - Plages Horaires")

st.write("Déplacez les curseurs pour découper la journée.")

# Valeurs initiales (en heures)
default_marks = {
    0: "00:00",
    6: "06:00",
    12: "12:00",
    18: "18:00",
    24: "24:00"
}

# Stockage des valeurs de curseurs
if "slider_values" not in st.session_state:
    st.session_state.slider_values = [5, 16, 21]

# Fonction de mise à jour
def update_slider(values):
    st.session_state.slider_values = values

# Interface interactive
with elements("timeline"):
    sync()  # Important pour synchroniser avec Streamlit

    mui.Box(
        sx={"width": "100%", "padding": "30px"},
        children=[
            mui.Slider(
                value=st.session_state.slider_values,
                min=0,
                max=24,
                step=1,
                marks=[{"value": v, "label": t} for v, t in default_marks.items()],
                onChange=lambda e, v: update_slider(v),
                valueLabelDisplay="on",
                disableSwap=True
            )
        ]
    )

# Génération automatique des plages horaires à partir des curseurs
slider_values = sorted(st.session_state.slider_values)
ranges = []

# Plages de 0 -> premier curseur, puis entre chaque curseur, puis dernier curseur -> 24
if slider_values[0] != 0:
    ranges.append((0, slider_values[0]))

for i in range(len(slider_values) - 1):
    ranges.append((slider_values[i], slider_values[i+1]))

if slider_values[-1] != 24:
    ranges.append((slider_values[-1], 24))

# Résultat
st.success("Plages horaires définies :")
for start, end in ranges:
    st.write(f"- {start:02.0f}h - {end:02.0f}h")

# Tu peux utiliser `ranges` pour faire ton traitement après (comme parsed_time_ranges)
parsed_time_ranges = ranges
