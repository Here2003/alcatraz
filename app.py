"""
Assistant de collecte des déchets pour un hôtel à Grasse
Lancement :
    pip install streamlit requests beautifulsoup4 openai
    streamlit run app.py

Option IA générative :
    Définir OPENAI_API_KEY dans l'environnement.
    Exemple macOS/Linux : export OPENAI_API_KEY="..."
    Exemple Windows PowerShell : $env:OPENAI_API_KEY="..."

Sans clé API, l'application fonctionne en mode réponses guidées.
Les horaires généraux sont ceux publiés par le Pays de Grasse.
Pour un hôtel, la convention professionnelle de collecte prévaut.
"""

import os
import re
from datetime import datetime
from urllib.parse import urlparse

import requests
import streamlit as st
from bs4 import BeautifulSoup

SCHEDULE_URL = "https://www.paysdegrasse.fr/points-et-frequence-de-collecte"
PRO_URL = "https://www.paysdegrasse.fr/dechets-professionnels"
CONTACT_PHONE = "0800 506 586"
CONTACT_EMAIL = "redevancespeciale@paysdegrasse.fr"

# Jours de collecte générale publiés par le Pays de Grasse.
# Attention : il ne s'agit pas nécessairement du planning applicable à un hôtel.
SECTORS = {
    "Saint-François / Super Grasse": {
        "ordures": ["lundi", "vendredi"],
        "tri": ["mardi"],
    },
    "Centre historique": {
        "ordures": ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"],
        "tri": ["lundi", "jeudi"],
    },
    "Les 4 Chemins / Saint-Antoine / Saint-Jacques / Sainte-Anne": {
        "ordures": ["lundi", "vendredi"],
        "tri": ["jeudi"],
    },
    "Les Aspres / La Tourache / Les Roumiguières / Valcluse": {
        "ordures": ["lundi", "vendredi"],
        "tri": ["samedi"],
    },
    "Le Plan / Saint-Marc / Sainte-Marguerite": {
        "ordures": ["mardi", "samedi"],
        "tri": ["vendredi"],
    },
    "Saint-Claude": {
        "ordures": ["mardi", "samedi"],
        "tri": ["mercredi"],
    },
    "Centre-ville": {
        "ordures": ["mardi", "samedi"],
        "tri": ["jeudi"],
    },
    "Saint-Mathieu / Magagnosc / Saint-Jean / Saint-Joseph / Plascassier": {
        "ordures": ["mardi", "samedi"],
        "tri": ["lundi"],
    },
}

DAYS_FR = [
    "lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"
]


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_official_text(url: str) -> str:
    """Récupère le texte public d'une page officielle, avec délai d'expiration."""
    try:
        response = requests.get(
            url,
            timeout=12,
            headers={"User-Agent": "HotelDechetsGrasse/1.0 (assistant informatif)"},
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
        return text[:18000]
    except requests.RequestException:
        return ""


def weekday_fr(date_obj):
    return DAYS_FR[date_obj.weekday()]


def official_context():
    schedule_text = fetch_official_text(SCHEDULE_URL)
    pro_text = fetch_official_text(PRO_URL)
    return (
        "SOURCE OFFICIELLE — FRÉQUENCES GÉNÉRALES PAR SECTEUR :\n"
        + (schedule_text or "Page officielle indisponible momentanément.")
        + "\n\nSOURCE OFFICIELLE — DÉCHETS PROFESSIONNELS :\n"
        + (pro_text or "Page officielle des professionnels indisponible momentanément.")
    )


def guided_answer(question: str, sector: str) -> str:
    """Mode de secours sans API : réponses prudentes à partir des données connues."""
    q = question.lower()
    info = SECTORS.get(sector)
    if info is None:
        return (
            "Je n'ai pas de secteur sélectionné. Choisis le secteur correspondant à "
            "l'adresse de l'hôtel. Pour un établissement professionnel, vérifie aussi "
            "la convention de collecte : elle peut prévoir des jours et modalités spécifiques."
        )

    if any(word in q for word in ["professionnel", "hôtel", "hotel", "convention", "contrat"]):
        return (
            "Pour un hôtel, le planning applicable dépend de la convention de collecte "
            "professionnelle conclue avec le Pays de Grasse. Les jours affichés dans "
            "l'application sont les fréquences générales du secteur et ne remplacent pas "
            "cette convention. Vérifie le contrat ou contacte le service déchets "
            f"professionnels au {CONTACT_PHONE} (gratuit), ou par e-mail : {CONTACT_EMAIL}."
        )

    if any(word in q for word in ["tri", "jaune", "recycl", "emballage", "carton"]):
        days = ", ".join(info["tri"])
        return (
            f"Pour le secteur **{sector}**, le jour général publié pour le tri sélectif "
            f"est : **{days}**. Pour un hôtel, confirme ce jour et les conditions de "
            "présentation dans la convention professionnelle. Les cartons doivent être "
            "vidés et pliés ; ne les laisse pas en vrac à côté des bacs."
        )

    if any(word in q for word in ["quand", "sortir", "jour", "ordure", "ménag", "poubelle", "bac"]):
        days = ", ".join(info["ordures"])
        return (
            f"Pour le secteur **{sector}**, les jours généraux publiés pour les ordures "
            f"ménagères sont : **{days}**. La consigne générale indique de sortir les "
            "bacs la veille au soir et de les rentrer dès que possible après leur vidage. "
            "**Pour un hôtel, la convention professionnelle prévaut** : ne considère pas "
            "ces jours comme confirmés pour ton établissement avant vérification."
        )

    return (
        f"Pour le secteur **{sector}**, les fréquences générales sont : ordures ménagères "
        f"({', '.join(info['ordures'])}) ; tri sélectif ({', '.join(info['tri'])}). "
        "Ces horaires ne confirment pas le planning particulier de l'hôtel. "
        "Consulte la convention professionnelle ou contacte le Pays de Grasse."
    )


def ask_ai(question: str, sector: str, context: str) -> str:
    """Utilise OpenAI si la clé est configurée, sinon le mode guidé."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return guided_answer(question, sector)

    try:
