"""
Assistant de collecte des déchets pour toute la ville de Grasse.
Lancement :
    pip install streamlit openai
    streamlit run app.py

Pour activer les réponses IA, définir OPENAI_API_KEY dans les secrets
Streamlit ou dans l'environnement. Sans clé, le mode guidé fonctionne.
Les jours affichés sont des fréquences générales à vérifier sur le site officiel.
"""
import os
from datetime import datetime

import streamlit as st

st.set_page_config(
    page_title="Assistant déchets — Grasse",
    page_icon="🗑️",
    layout="centered",
)

SCHEDULE_URL = "https://www.paysdegrasse.fr/points-et-frequence-de-collecte"
PRO_URL = "https://www.paysdegrasse.fr/dechets-professionnels"
CONTACT_PHONE = "0800 506 586"

# Fréquences générales indicatives par secteur.
# Vérifier la page officielle : la collecte peut varier selon la rue et le type d'usager.
SECTORS = {
    "Centre-ville": {"ordures": "mardi et samedi", "tri": "jeudi"},
    "Centre historique": {
        "ordures": "fréquence quotidienne indiquée à confirmer",
        "tri": "lundi et jeudi",
    },
    "Saint-Claude": {"ordures": "mardi et samedi", "tri": "mercredi"},
    "Le Plan / Saint-Marc / Sainte-Marguerite": {
        "ordures": "mardi et samedi", "tri": "vendredi"
    },
    "Saint-François / Super Grasse": {
        "ordures": "lundi et vendredi", "tri": "mardi"
    },
    "Les 4 Chemins / Saint-Antoine / Saint-Jacques / Sainte-Anne": {
        "ordures": "lundi et vendredi", "tri": "jeudi"
    },
    "Les Aspres / La Tourache / Les Roumiguières / Valcluse": {
        "ordures": "lundi et vendredi", "tri": "samedi"
    },
    "Saint-Mathieu / Magagnosc / Saint-Jean / Saint-Joseph / Plascassier": {
        "ordures": "mardi et samedi", "tri": "lundi"
    },
}


def guided_answer(question, sector, user_type):
    q = question.lower()
    info = SECTORS[sector]

    if any(word in q for word in ["encombrant", "meuble", "matelas", "déchetterie", "decheterie"]):
        return (
            "Pour les encombrants ou les déchets qui ne vont pas dans les bacs habituels, "
            "consulte le site officiel du Pays de Grasse pour connaître les modalités à jour. "
            "Ne les dépose pas sur le trottoir sans confirmation."
        )

    if any(word in q for word in ["tri", "carton", "recycl", "emballage", "jaune", "papier", "verre"]):
        answer = (
            f"Pour le secteur **{sector}**, le jour général indiqué ici pour le tri sélectif "
            f"est **{info['tri']}**. Les consignes peuvent dépendre de la rue et du type de bac. "
            f"Vérifie le calendrier officiel : {SCHEDULE_URL}"
        )
    elif any(word in q for word in ["professionnel", "commerce", "restaurant", "hôtel", "hotel", "entreprise", "contrat", "convention"]):
        answer = (
            "Pour les professionnels, les jours et modalités peuvent être définis par une "
            "convention de collecte spécifique. Consulte la page officielle des déchets "
            f"professionnels : {PRO_URL}, ou contacte le service du Pays de Grasse au "
            f"{CONTACT_PHONE}. Ne te fie pas uniquement aux fréquences générales du quartier."
        )
    elif any(word in q for word in ["quand", "sortir", "jour", "ordure", "ménag", "menag", "poubelle", "bac", "noire"]):
        answer = (
            f"Pour le secteur **{sector}**, les fréquences générales des ordures ménagères "
            f"sont indiquées comme **{info['ordures']}**. La consigne générale peut être de "
            "sortir le bac la veille au soir, mais vérifie les règles exactes de ton adresse "
            f"sur le site officiel : {SCHEDULE_URL}."
        )
    else:
        answer = (
            f"Pour le secteur **{sector}**, les fréquences générales affichées sont : "
            f"ordures ménagères — **{info['ordures']}** ; tri sélectif — **{info['tri']}**. "
            "Pour confirmer le jour exact, consulte la page officielle de collecte."
        )

    if user_type == "Professionnel":
        answer += (
            "\n\n**Attention :** pour un commerce, restaurant, hôtel ou autre professionnel, "
            "la convention de collecte peut prévoir des modalités différentes."
        )
    return answer
