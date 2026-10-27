import os
from datetime import datetime

import streamlit as st

st.set_page_config(page_title="Assistant déchets - Grasse", page_icon="🗑️", layout="centered")

SCHEDULE_URL = "https://www.paysdegrasse.fr/points-et-frequence-de-collecte"
PRO_URL = "https://www.paysdegrasse.fr/dechets-professionnels"
CONTACT_PHONE = "0800 506 586"

SECTORS = {
    "Centre-ville": {"ordures": "mardi et samedi", "tri": "jeudi"},
    "Centre historique": {"ordures": "tous les jours (fréquence générale à confirmer)", "tri": "lundi et jeudi"},
    "Saint-Claude": {"ordures": "mardi et samedi", "tri": "mercredi"},
    "Le Plan / Saint-Marc / Sainte-Marguerite": {"ordures": "mardi et samedi", "tri": "vendredi"},
    "Saint-François / Super Grasse": {"ordures": "lundi et vendredi", "tri": "mardi"},
    "Les 4 Chemins / Saint-Antoine / Saint-Jacques / Sainte-Anne": {"ordures": "lundi et vendredi", "tri": "jeudi"},
    "Les Aspres / La Tourache / Les Roumiguières / Valcluse": {"ordures": "lundi et vendredi", "tri": "samedi"},
    "Saint-Mathieu / Magagnosc / Saint-Jean / Saint-Joseph / Plascassier": {"ordures": "mardi et samedi", "tri": "lundi"},
}

def answer_question(question, sector):
    q = question.lower()
    info = SECTORS[sector]
    if any(word in q for word in ["tri", "carton", "recycl", "emballage", "jaune"]):
        return (
            f"Pour le secteur {sector}, le jour général indiqué pour le tri est : "
            f"{info['tri']}. Attention : pour un hôtel, confirme ce jour dans la convention "
            "de collecte professionnelle avant de t'y fier."
        )
    if any(word in q for word in ["contrat", "convention", "professionnel", "hôtel", "hotel"]):
        return (
            "Le planning applicable à un hôtel peut être différent du calendrier général. "
            f"Vérifie la convention de collecte ou contacte le service déchets du Pays de Grasse "
            f"au {CONTACT_PHONE}. Consulte aussi la page officielle des déchets professionnels."
        )
    return (
        f"Pour le secteur {sector}, les jours généraux des ordures ménagères sont : "
        f"{info['ordures']}. La consigne générale est de sortir les bacs la veille au soir "
        "et de les rentrer après le passage. Pour un hôtel, la convention professionnelle "
        "prévaut : confirme les jours et horaires exacts auprès du service de collecte."
    )

def main():
    st.title("🗑️ Assistant déchets — Hôtel à Grasse")
    st.write("Pose une question sur les jours de collecte, les bacs ou le tri.")

    with st.sidebar:
        st.header("Configuration")
        sector = st.selectbox("Secteur de Grasse", list(SECTORS.keys()), index=0)
        st.markdown("### Sources officielles")
        st.markdown(f"[Fréquences de collecte]({SCHEDULE_URL})")
        st.markdown(f"[Déchets professionnels]({PRO_URL})")
        st.write(f"Contact service déchets : {CONTACT_PHONE}")

    st.warning(
        "Important : les fréquences ci-dessous sont générales. Pour un hôtel, "
        "la convention professionnelle et les consignes données à l'établissement priment."
    )

    left, right = st.columns(2)
    left.metric("Ordures ménagères", SECTORS[sector]["ordures"])
    right.metric("Tri sélectif", SECTORS[sector]["tri"])

    with st.form("ask_form"):
        question = st.text_area(
            "Ta question",
            placeholder="Ex. : Quand sortir les poubelles noires ?",
        )
        submitted = st.form_submit_button("Répondre")

    if submitted:
        if not question.strip():
            st.error("Écris une question.")
        else:
            api_key = os.getenv("OPENAI_API_KEY", "").strip()
            if api_key:
                try:
                    from openai import OpenAI
                    client = OpenAI(api_key=api_key)
                    response = client.responses.create(
                        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
                        instructions=(
                            "Tu es un assistant de collecte des déchets pour un hôtel à Grasse. "
                            "Réponds en français, simplement, sans inventer les horaires. "
                            "Précise que la convention professionnelle de l'hôtel prévaut sur "
                            "les fréquences générales et recommande de vérifier les sources officielles."
                        ),
                        input=(
                            f"Secteur : {sector}. Fréquence générale ordures : "
                            f"{SECTORS[sector]['ordures']}. Fréquence générale tri : "
                            f"{SECTORS[sector]['tri']}. Question : {question}\n"
                            f"Sources : {SCHEDULE_URL} et {PRO_URL}"
                        ),
                    )
                    result = response.output_text
                except Exception:
                    result = answer_question(question, sector)
                    st.info("L'IA n'est pas disponible pour le moment ; réponse guidée affichée.")
            else:
                result = answer_question(question, sector)
                st.caption("Mode guidé activé. Pour les réponses générées par IA, configure OPENAI_API_KEY.")
            st.subheader("Réponse")
            st.write(result)
            st.markdown(f"Sources : [Collecte générale]({SCHEDULE_URL}) · [Professionnels]({PRO_URL})")

    st.caption(f"Application informative — {datetime.now().strftime('%d/%m/%Y')}. Vérifie toujours les consignes propres à l'hôtel.")

if __name__ == "__main__":
    main()
