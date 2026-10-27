import os
from datetime import date

import streamlit as st

st.set_page_config(
    page_title="Grasse Déchets",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded",
)

SCHEDULE_URL = "https://www.paysdegrasse.fr/points-et-frequence-de-collecte"
PRO_URL = "https://www.paysdegrasse.fr/dechets-professionnels"
CONTACT_PHONE = "0800 506 586"

SECTORS = {
    "Centre-ville": {"ordures": "mardi et samedi", "tri": "jeudi"},
    "Centre historique": {"ordures": "fréquence à confirmer", "tri": "lundi et jeudi"},
    "Saint-Claude": {"ordures": "mardi et samedi", "tri": "mercredi"},
    "Le Plan / Saint-Marc / Sainte-Marguerite": {"ordures": "mardi et samedi", "tri": "vendredi"},
    "Saint-François / Super Grasse": {"ordures": "lundi et vendredi", "tri": "mardi"},
    "Les 4 Chemins / Saint-Antoine / Saint-Jacques / Sainte-Anne": {"ordures": "lundi et vendredi", "tri": "jeudi"},
    "Les Aspres / La Tourache / Les Roumiguières / Valcluse": {"ordures": "lundi et vendredi", "tri": "samedi"},
    "Saint-Mathieu / Magagnosc / Saint-Jean / Saint-Joseph / Plascassier": {"ordures": "mardi et samedi", "tri": "lundi"},
    "Je ne connais pas mon secteur": {"ordures": "à vérifier par adresse", "tri": "à vérifier par adresse"},
}


def answer_without_ai(question: str, sector: str, user_type: str) -> str:
    q = question.lower()
    info = SECTORS[sector]

    if sector == "Je ne connais pas mon secteur":
        return (
            "Je ne peux pas confirmer le jour de collecte sans connaître le secteur ou l'adresse. "
            "Consulte le calendrier officiel du Pays de Grasse et recherche ton adresse. "
            f"Pour les professionnels, vérifie aussi la convention de collecte : {PRO_URL}"
        )

    if any(x in q for x in ["encombrant", "matelas", "meuble", "déchetterie", "decheterie", "gravats"]):
        return (
            "Les encombrants et déchets spéciaux ne doivent pas être laissés sur le trottoir sans consigne. "
            "Consulte les informations à jour du Pays de Grasse pour connaître les modalités de dépôt "
            "ou de collecte. Si tu es un professionnel, demande les consignes correspondant à ton activité."
        )

    if user_type == "Professionnel" or any(x in q for x in ["hôtel", "hotel", "professionnel", "commerce", "entreprise", "restaurant", "convention", "contrat"]):
        return (
            f"Pour les professionnels, le calendrier général du secteur ({sector}) ne suffit pas à confirmer "
            "le passage applicable à l'établissement : une convention ou une organisation spécifique peut exister. "
            f"Vérifie la page officielle des déchets professionnels : {PRO_URL}, ou contacte le service au "
            f"{CONTACT_PHONE}. Les jours affichés ci-dessus sont indicatifs et ne remplacent pas la convention."
        )

    if any(x in q for x in ["tri", "carton", "recycl", "emballage", "jaune", "papier", "verre"]):
        return (
            f"Pour le secteur **{sector}**, le jour général de tri indiqué dans cette application est "
            f"**{info['tri']}**. Confirme toujours la consigne de ton adresse sur le calendrier officiel : "
            f"{SCHEDULE_URL}. Les consignes peuvent varier selon la rue et le type de bac."
        )

    if any(x in q for x in ["quand", "sortir", "jour", "ordure", "ménag", "menag", "poubelle", "bac", "noire", "ce soir"]):
        return (
            f"Pour le secteur **{sector}**, les fréquences générales des ordures ménagères sont indiquées "
            f"comme **{info['ordures']}**. Le bon moment de sortie dépend des consignes applicables à l'adresse. "
            f"Vérifie le calendrier officiel : {SCHEDULE_URL}. Ne considère pas cette fréquence comme confirmée "
            "pour une adresse précise tant qu'elle n'a pas été vérifiée."
        )

    return (
        f"Pour **{sector}**, les fréquences générales affichées sont : ordures ménagères — "
        f"**{info['ordures']}** ; tri sélectif — **{info['tri']}**. "
        f"Pour confirmer selon une adresse, consulte {SCHEDULE_URL}."
    )


def answer_with_ai(question: str, sector: str, user_type: str) -> str:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        return answer_without_ai(question, sector, user_type)
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        info = SECTORS[sector]
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            instructions=(
                "Tu es Grasse Déchets, assistant d'information sur la collecte des déchets à Grasse. "
                "Réponds en français, de façon concise et utile. N'invente jamais un jour de collecte, "
                "une règle ou une source. Les fréquences fournies sont indicatives et peuvent être anciennes. "
                "Pour les professionnels, précise que la convention spécifique prévaut. Si l'adresse ou le "
                "secteur précis manque, demande de vérifier la source officielle. Cite les liens fournis."
            ),
            input=(
                f"Type d'usager : {user_type}\nSecteur choisi : {sector}\n"
