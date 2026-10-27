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
