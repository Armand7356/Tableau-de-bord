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

def style_colonne(colonne):
    styles = []
    for idx, valeur in colonne.items():
        # ➔ Sauter la ligne "Somme" (dernière ligne)
        if idx == "Somme":
            styles.append("")
            continue
        
        limite = None
        for nom_colonne, valeur_limite in limites_eau:
            if nom_colonne.lower() in colonne.name.lower():
                limite = valeur_limite
                break

        if pd.isna(valeur):  # Gérer les NaN
            styles.append("")
        elif limite is not None and limite > 0 and valeur > limite:
            styles.append("background-color: red; color: white;")
        else:
            styles.append("")
    return styles

# Charger les limites
def charger_limites_eau(fichier_path):
    limites_eau = []
    try:
        with open(fichier_path, "r", encoding="utf-8") as f:
            for ligne in f:
                if "\t" in ligne:
                    colonne, limite = ligne.strip().split("\t")
                    if page in colonne.lower():
                        limites_eau.append([colonne,float(limite)])
    except FileNotFoundError:
        print(f"Fichier {fichier_path} introuvable.")
    except Exception as e:
        print(f"Erreur : {e}")
    return limites_eau



page = "elec"    #"elec" ou "eau" ou "gaz"


# Utilisation
fichier_limites = "pages_after_log/Menu/limites_consommation.txt"  # Ton chemin réel
limites_eau = charger_limites_eau(fichier_limites)
# Charger les données Excel
file_path = "tableau de bord Wit.xlsx"
data = pd.ExcelFile(file_path)

start_hour=0

# Charger les données horaires
df_hourly = data.parse("Conso_h")


# Configurer la page
write_log("Rapport Hebdomadaire - "+page)
st.title("Rapport Hebdomadaire - "+page)

# Create a horizontal layout for filters
col1, col2, col3, col4 = st.columns([1.9, 1.5, 2.2, 0.5])

with col1:

    # Sélection de la semaine
    current_date = datetime.now()
    default_start_date = (current_date - timedelta(days=current_date.weekday(), weeks=1)).date()
    week_number = st.number_input("Choisissez le numéro de la semaine :", value=default_start_date.isocalendar()[1], step=1)

with col2:

    year = st.number_input("Choisissez l'année :", value=default_start_date.year, step=1)

# Filtrer les données horaires pour la semaine sélectionnée
df_hourly["DateTime"] = pd.to_datetime(df_hourly["Date /h"], errors='coerce')
df_hourly["Semaine"] = df_hourly["DateTime"].dt.isocalendar().week
df_hourly["Annee"] = df_hourly["DateTime"].dt.year

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
    filtered_data["Jour"] = (filtered_data["DateTime"] - pd.to_timedelta((filtered_data["DateTime"].dt.hour < start_hour).astype(int), unit="D")).dt.date

    # Exclure les colonnes non numériques et celles contenant "Cpt" pour l'agrégation
    numeric_columns = filtered_data.select_dtypes(include=['number']).columns
    numeric_columns = [col for col in numeric_columns if "Cpt" not in col]
    numeric_columns = [col for col in numeric_columns if page in col.lower()]
    daily_data = filtered_data.groupby("Jour")[numeric_columns].sum()

    # S'assurer que l'index est au format datetime
    daily_data.index = pd.to_datetime(daily_data.index)

    # Limiter aux jours de Lundi (0) à Dimanche (6)
    daily_data = daily_data.loc[daily_data.index.dayofweek < 7]


    
    fig = go.Figure()
################################
##############################
############################


    
    # Ajout des compteurs de niveau 2 uniquement (hors sous-compteurs ballon)
    for col in daily_data.columns:
        if (
            "Consomation "+page in col and 
            col != "Consomation "+page+" chaudière vapeur" and 
            col != "Consomation "+page+" général" and 
            "MP" not in col
        ):
            fig.add_trace(go.Bar(
                x=daily_data.index,
                y=daily_data[col],
                name=col.replace("Consomation "+page, "").strip()
            ))


############################
##############################
################################



        # Ajouter une colonne "Autres"
    col_general = "Consomation " + page + " général"
    col_chaudiere = "Consomation " + page + " chaudière vapeur"

    if col_general in daily_data.columns:
        # Liste toutes les colonnes pertinentes
        columns_to_sum = [col for col in daily_data.columns 
                        if "Consomation " + page in col 
                        and col != col_general 
                        and (col != col_chaudiere if col_chaudiere in daily_data.columns else True)  # Seulement si la colonne chaudière existe
                        and "MP" not in col]
        
        # Calculer Autres uniquement si columns_to_sum n'est pas vide
        if columns_to_sum:
            daily_data[page + " Autres"] = (daily_data[col_general] - daily_data[columns_to_sum].sum(axis=1)).clip(lower=0)

            fig.add_trace(go.Bar(
                x=daily_data.index,
                y=daily_data[page + " Autres"],
                name="Autres"
            ))


    # Configurer et afficher l'histogramme
    fig.update_layout(
        template="plotly_white",
        barmode="stack",
        title="Consommation Générale "+page+" - Semaine "+str(week_number)+" / "+str(year),
        xaxis_title="Jour",
        yaxis_title="Consommation (m³)",
        legend_title="Catégories",
    )
    # Ajouter une ligne horizontale de limite
    for col in limites_eau:
        #st.write(col)
        if col[0] == "Consomation "+page+" général":
            limite_conso = col[1]
            break

    fig.add_shape(
        type="line",
        x0=daily_data.index.min(),
        x1=daily_data.index.max(),
        y0=limite_conso,
        y1=limite_conso,
        line=dict(color="red", width=2, dash="dash"),
        xref="x",
        yref="y"
    )

    st.plotly_chart(fig, use_container_width=True)

    # Ajouter un filtre pour n'afficher que les colonnes contenant "eau"
    filtered_columns = [col for col in daily_data.columns if page in col.lower()]
    filtered_table = daily_data[filtered_columns]

    

   # Ajouter Moyenne et Somme
    filtered_table.loc['Moyenne'] = filtered_table.mean()
    filtered_table.loc['Somme'] = filtered_table.sum() - filtered_table.loc['Moyenne']
    # Styliser
    styled_table = filtered_table.style.apply(style_colonne, axis=0)
   

    # Afficher
    st.write("### Données de consommation sur la semaine")
    st.dataframe(styled_table)



# Ajouter un diagramme en cercle pour la répartition des volumes consommés
st.write("### Répartition des volumes consommés")
if "filtered_table" in locals() or "filtered_table" in globals():
    consumption_columns = [col for col in filtered_table.columns if "Consomation "+page in col and
                        col != "Consomation "+page+" général" and 
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
        fig_pie.update_layout(title="Répartition des consommations "+page+" - Semaine "+str(week_number)+" / "+str(year))
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.warning("Aucune donnée disponible pour la répartition des consommations "+page+".")


