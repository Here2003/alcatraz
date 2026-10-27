import streamlit as st
from datetime import date

st.set_page_config(page_title="Grasse Déchets", page_icon="♻️", layout="wide")

SCHEDULE_URL = "https://www.paysdegrasse.fr/points-et-frequence-de-collecte"
PRO_URL = "https://www.paysdegrasse.fr/dechets-professionnels"
PHONE = "0800 506 586"

SECTORS = {
    "Je ne connais pas mon secteur": {
        "ordures": "à vérifier selon l'adresse",
        "tri": "à vérifier selon l'adresse",
    },
    "Centre-ville": {
        "ordures": "mardi et samedi (indicatif, à confirmer)",
        "tri": "jeudi (indicatif, à confirmer)",
    },
    "Centre historique": {
        "ordures": "à confirmer sur le calendrier officiel",
        "tri": "lundi et jeudi (indicatif, à confirmer)",
    },
    "Saint-Claude": {
        "ordures": "mardi et samedi (indicatif, à confirmer)",
        "tri": "mercredi (indicatif, à confirmer)",
    },
    "Le Plan / Saint-Marc / Sainte-Marguerite": {
        "ordures": "mardi et samedi (indicatif, à confirmer)",
        "tri": "vendredi (indicatif, à confirmer)",
    },
    "Saint-François / Super Grasse": {
        "ordures": "lundi et vendredi (indicatif, à confirmer)",
        "tri": "mardi (indicatif, à confirmer)",
    },
    "Les 4 Chemins / Saint-Antoine / Saint-Jacques / Sainte-Anne": {
        "ordures": "lundi et vendredi (indicatif, à confirmer)",
        "tri": "jeudi (indicatif, à confirmer)",
    },
    "Les Aspres / La Tourache / Les Roumiguières / Valcluse": {
        "ordures": "lundi et vendredi (indicatif, à confirmer)",
        "tri": "samedi (indicatif, à confirmer)",
    },
    "Saint-Mathieu / Magagnosc / Saint-Jean / Saint-Joseph / Plascassier": {
        "ordures": "mardi et samedi (indicatif, à confirmer)",
        "tri": "lundi (indicatif, à confirmer)",
    },
}

st.markdown("""
<style>
.stApp {background:#f4f7f3;}
.block-container {max-width:1050px;padding-top:2rem;padding-bottom:3rem;}
.hero {background:#173f30;color:white;padding:2rem;border-radius:20px;margin-bottom:1.5rem;}
.hero h1 {color:white;margin:.4rem 0;font-size:2.5rem;}
.hero p {color:#e1eee6;margin:0;}
.card {background:white;border:1px solid #dce6dd;border-radius:14px;padding:1.1rem;min-height:115px;}
.label {font-size:.9rem;color:#68766b;}
.value {font-weight:700;font-size:1.15rem;color:#173f30;margin-top:.55rem;}
</style>
<div class="hero">
  <div>♻️ GRASSE DÉCHETS</div>
  <h1>La collecte, en clair.</h1>
  <p>Informations pratiques pour toute la ville de Grasse.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("♻️ Grasse Déchets")
    profile = st.radio("Profil", ["Habitant", "Professionnel / hôtel"])
    sector = st.selectbox("Quartier / secteur", list(SECTORS.keys()))
    st.caption("Les consignes de la convention professionnelle peuvent prévaloir.")
    st.markdown("### Liens officiels")
    st.markdown(f"[Calendrier de collecte]({SCHEDULE_URL})")
    st.markdown(f"[Déchets professionnels]({PRO_URL})")
    st.caption(f"Service déchets : {PHONE}")

st.subheader("Informations du secteur")
info = SECTORS[sector]
col1, col2, col3 = st.columns(3)
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
with col3:
    st.markdown(
        f'<div class="card"><div class="label">📅 Aujourd’hui</div>'
        f'<div class="value">{date.today().strftime("%d/%m/%Y")}</div></div>',
        unsafe_allow_html=True,
    )

st.warning(
    "Les fréquences affichées sont indicatives. Vérifie le calendrier officiel pour l'adresse précise. "
    "Pour un hôtel, restaurant ou commerce, vérifie également la convention professionnelle."
)

st.subheader("Assistant de collecte")
st.write("Pose une question sur les bacs, le tri, les cartons ou les encombrants.")
question = st.text_area(
    "Ta question",
    placeholder="Ex. : Quand sortir les poubelles pour un hôtel ?",
    height=100,
)
submitted = st.button("Répondre", type="primary", use_container_width=True)

if submitted:
    if not question.strip():
        st.error("Écris une question avant de continuer.")
    else:
        q = question.lower()
        is_professional = profile == "Professionnel / hôtel" or any(
            word in q for word in ("hôtel", "hotel", "restaurant", "commerce", "entreprise", "professionnel")
        )

        if is_professional:
            answer = (
                "Pour un professionnel, les jours généraux d'un quartier ne confirment pas le planning "
                "de l'établissement. Vérifie la convention de collecte ou contacte le service déchets "
                f"du Pays de Grasse au {PHONE}. Consulte aussi les consignes professionnelles : {PRO_URL}"
            )
        elif any(word in q for word in ("encombrant", "meuble", "matelas", "gravats", "déchetterie")):
            answer = (
                "Ne dépose pas les encombrants sur le trottoir sans vérifier les consignes. "
                f"Consulte les informations officielles du Pays de Grasse : {SCHEDULE_URL}"
            )
        elif any(word in q for word in ("tri", "carton", "recycl", "emballage", "papier", "jaune", "verre")):
            answer = (
                f"Pour le secteur « {sector} », l'indication générale du tri est : {info['tri']}. "
                f"Confirme ce jour pour ton adresse sur le calendrier officiel : {SCHEDULE_URL}"
            )
        else:
            answer = (
                f"Pour le secteur « {sector} », l'indication générale des ordures ménagères est : "
                f"{info['ordures']}. Confirme ce jour pour ton adresse sur le calendrier officiel : {SCHEDULE_URL}"
            )

        st.markdown("### Réponse")
        st.write(answer)

st.divider()
left, right = st.columns(2)
with left:
    st.markdown("#### Calendrier officiel")
    st.write("Jours de collecte à vérifier par adresse.")
    st.link_button("Consulter le calendrier", SCHEDULE_URL, use_container_width=True)
with right:
    st.markdown("#### Professionnels")
    st.write("Consignes pour les hôtels, restaurants et commerces.")
    st.link_button("Consulter les consignes", PRO_URL, use_container_width=True)

st.caption("Grasse Déchets · Les informations générales ne remplacent pas la confirmation officielle par adresse.")
