import os
import streamlit as st

st.set_page_config(
    page_title="Grasse Déchets",
    page_icon="♻️",
    layout="centered",
)

SCHEDULE_URL = "https://www.paysdegrasse.fr/points-et-frequence-de-collecte"
PRO_URL = "https://www.paysdegrasse.fr/dechets-professionnels"
PHONE = "0800 506 586"

SECTORS = {
    "Je ne connais pas mon secteur": {
        "ordures": "À vérifier selon l'adresse",
        "tri": "À vérifier selon l'adresse",
    },
    "Centre-ville": {"ordures": "Mardi et samedi (indicatif)", "tri": "Jeudi (indicatif)"},
    "Centre historique": {"ordures": "À confirmer", "tri": "Lundi et jeudi (indicatif)"},
    "Saint-Claude": {"ordures": "Mardi et samedi (indicatif)", "tri": "Mercredi (indicatif)"},
    "Le Plan / Saint-Marc / Sainte-Marguerite": {"ordures": "Mardi et samedi (indicatif)", "tri": "Vendredi (indicatif)"},
    "Saint-François / Super Grasse": {"ordures": "Lundi et vendredi (indicatif)", "tri": "Mardi (indicatif)"},
    "Les 4 Chemins / Saint-Antoine / Saint-Jacques / Sainte-Anne": {"ordures": "Lundi et vendredi (indicatif)", "tri": "Jeudi (indicatif)"},
    "Les Aspres / La Tourache / Les Roumiguières / Valcluse": {"ordures": "Lundi et vendredi (indicatif)", "tri": "Samedi (indicatif)"},
    "Saint-Mathieu / Magagnosc / Saint-Jean / Saint-Joseph / Plascassier": {"ordures": "Mardi et samedi (indicatif)", "tri": "Lundi (indicatif)"},
}

st.markdown("""
<style>
.stApp { background: #f4f7f4; }
.block-container { max-width: 900px; padding-top: 2rem; }
.hero { padding: 1.8rem; border-radius: 18px; background: #174d38; color: white; margin-bottom: 1rem; }
.hero h1 { color: white; margin: .3rem 0; }
.hero p { color: #e0eee5; margin-bottom: 0; }
.card { background: white; border: 1px solid #dce7df; border-radius: 14px; padding: 1rem; min-height: 120px; }
.label { color: #637368; font-size: .9rem; }
.value { color: #174d38; font-weight: 700; font-size: 1.15rem; margin-top: .5rem; }
</style>
<div class="hero">
  <div>♻️ GRASSE DÉCHETS</div>
  <h1>Quand sortir les poubelles ?</h1>
  <p>Informations de collecte pour les quartiers de Grasse.</p>
</div>
""", unsafe_allow_html=True)

st.subheader("1. Choisis ton secteur")
sector = st.selectbox("Secteur de Grasse", list(SECTORS.keys()))
info = SECTORS[sector]

col1, col2 = st.columns(2)
with col1:
    st.markdown(
        f'<div class="card"><div class="label">🗑️ Ordures ménagères</div>'
        f'<div class="value">{info["ordures"]}</div></div>',
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        f'<div class="card"><div class="label">♻️ Tri sélectif</div>'
        f'<div class="value">{info["tri"]}</div></div>',
        unsafe_allow_html=True,
    )

st.warning(
    "Les jours affichés sont indicatifs et doivent être confirmés avec le calendrier officiel. "
    "Pour un hôtel, commerce ou restaurant, la convention professionnelle peut prévoir d'autres modalités."
)

st.subheader("2. Pose ta question")
user_type = st.radio("Tu es :", ["Habitant", "Professionnel"], horizontal=True)
question = st.text_area(
    "Ta question",
    placeholder="Ex. : Quand sortir les cartons ? Est-ce que les horaires sont différents pour un hôtel ?",
    height=100,
)

if st.button("Obtenir une réponse", type="primary", use_container_width=True):
    if not question.strip():
        st.error("Écris une question avant de continuer.")
    else:
        q = question.lower()
        if user_type == "Professionnel" or any(word in q for word in ["hôtel", "hotel", "commerce", "restaurant", "professionnel", "convention"]):
            answer = (
                "Pour un professionnel, les fréquences générales du quartier ne suffisent pas à confirmer "
                "le jour de collecte. Vérifie la convention de collecte de l'établissement ou consulte "
                f"la page officielle : {PRO_URL}. Téléphone du service : {PHONE}."
            )
        elif any(word in q for word in ["tri", "carton", "recycl", "emballage", "papier", "jaune"]):
            answer = (
                f"Pour le secteur « {sector} », l'information indicative sur le tri est : {info['tri']}. "
                f"Vérifie le calendrier officiel pour ton adresse : {SCHEDULE_URL}."
            )
        elif any(word in q for word in ["encombrant", "meuble", "matelas", "gravats"]):
            answer = (
                "Ne dépose pas les encombrants sur le trottoir sans consigne. Consulte les règles et "
