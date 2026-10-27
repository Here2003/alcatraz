import streamlit as st
from datetime import datetime

# Grasse Déchets — version volontairement simple et robuste.
# Aucune clé API nécessaire, aucun appel réseau au démarrage.

st.set_page_config(
    page_title="Grasse Déchets",
    page_icon="♻️",
    layout="wide",
)

SCHEDULE_URL = "https://www.paysdegrasse.fr/points-et-frequence-de-collecte"
PRO_URL = "https://www.paysdegrasse.fr/dechets-professionnels"
PHONE = "0800 506 586"

st.markdown("""
<style>
  .stApp { background: #f5f7f4; }
  .block-container { max-width: 1050px; padding-top: 2rem; padding-bottom: 3rem; }
  .hero { background: #163f30; color: #fff; border-radius: 22px; padding: 2rem; margin-bottom: 1.4rem; }
  .hero h1 { color: #fff; font-size: 2.6rem; margin: .25rem 0 .5rem 0; }
  .hero p { color: #dcebe2; font-size: 1.05rem; margin-bottom: 0; }
  .tile { background: white; border: 1px solid #e0e8e1; border-radius: 16px; padding: 1.2rem; min-height: 125px; }
  .tile-label { color: #627267; font-size: .9rem; }
  .tile-value { color: #163f30; font-size: 1.2rem; font-weight: 700; margin-top: .6rem; }
  div.stButton > button[kind="primary"] { background: #176747; border: none; border-radius: 10px; min-height: 2.8rem; }
  div.stButton > button { border-radius: 10px; }
</style>
<div class="hero">
  <div>♻️ GRASSE DÉCHETS · GUIDE DE COLLECTE</div>
  <h1>Les poubelles, au bon moment.</h1>
  <p>Informations de collecte pour les habitants et les professionnels de Grasse.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("♻️ Grasse Déchets")
    st.write("Paramètres")
    audience = st.radio("Profil", ["Habitant", "Professionnel / hôtel"])
    sector = st.selectbox(
        "Secteur (fréquences générales)",
        [
            "Je ne sais pas",
            "Centre-ville",
            "Centre historique",
            "Saint-Claude",
            "Le Plan / Saint-Marc / Sainte-Marguerite",
            "Saint-François / Super Grasse",
            "Les 4 Chemins / Saint-Antoine / Saint-Jacques / Sainte-Anne",
            "Les Aspres / La Tourache / Les Roumiguières / Valcluse",
            "Saint-Mathieu / Magagnosc / Saint-Jean / Saint-Joseph / Plascassier",
        ],
    )
    st.caption("Pour les professionnels, la convention de collecte de l'établissement peut prévaloir.")

# Ces valeurs sont présentées comme indicatives, jamais comme un planning garanti.
frequencies = {
    "Centre-ville": ("Mardi et samedi (à confirmer)", "Jeudi (à confirmer)"),
    "Centre historique": ("À vérifier sur le calendrier officiel", "Lundi et jeudi (à confirmer)"),
    "Saint-Claude": ("Mardi et samedi (à confirmer)", "Mercredi (à confirmer)"),
    "Le Plan / Saint-Marc / Sainte-Marguerite": ("Mardi et samedi (à confirmer)", "Vendredi (à confirmer)"),
    "Saint-François / Super Grasse": ("Lundi et vendredi (à confirmer)", "Mardi (à confirmer)"),
    "Les 4 Chemins / Saint-Antoine / Saint-Jacques / Sainte-Anne": ("Lundi et vendredi (à confirmer)", "Jeudi (à confirmer)"),
    "Les Aspres / La Tourache / Les Roumiguières / Valcluse": ("Lundi et vendredi (à confirmer)", "Samedi (à confirmer)"),
    "Saint-Mathieu / Magagnosc / Saint-Jean / Saint-Joseph / Plascassier": ("Mardi et samedi (à confirmer)", "Lundi (à confirmer)"),
    "Je ne sais pas": ("Recherche par adresse nécessaire", "Recherche par adresse nécessaire"),
}
ordures, tri = frequencies[sector]

st.subheader("Aperçu de la collecte")
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f'<div class="tile"><div class="tile-label">🗑️ Ordures ménagères</div><div class="tile-value">{ordures}</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="tile"><div class="tile-label">♻️ Tri sélectif</div><div class="tile-value">{tri}</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="tile"><div class="tile-label">📅 Date du jour</div><div class="tile-value">{datetime.now().strftime("%d/%m/%Y")}</div></div>', unsafe_allow_html=True)

st.warning(
    "Ces fréquences sont indicatives et doivent être confirmées avec le calendrier officiel. "
    "Pour un hôtel, un restaurant ou un commerce, vérifie les modalités professionnelles."
)

st.subheader("Assistant de collecte")
st.write("Pose une question sur les ordures, le tri, les cartons ou les déchets encombrants.")
question = st.text_input(
    "Ta question",
    placeholder="Ex. : Quand sortir les cartons pour mon hôtel ?",
)
ask = st.button("Répondre", type="primary")

if ask:
    if not question.strip():
        st.error("Écris d'abord une question.")
    else:
