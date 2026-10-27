"""VideoIA — transformer une image en vidéo animée."""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import streamlit as st

from config import (
    DUREE_MAX_CLIP_UNIQUE_SECONDES,
    DUREES_DISPONIBLES,
    FORMATS_DISPONIBLES,
    MOTEUR_VIDEO,
    QUALITES_DISPONIBLES,
    REPLICATE_API_TOKEN,
    SEUIL_AVERTISSEMENT_SECONDES,
    UPLOADS_DIR,
    ParametresGeneration,
)
from engine.base import MoteurVideoNonConfigure
from pipeline.job_manager import creer_et_planifier, executer_job
from storage import db

st.set_page_config(page_title="VideoIA", page_icon="🎬", layout="centered")
db.initialiser()

# --------------------------------------------------
# Identité de l'utilisateur (très simple : un identifiant de session)
# --------------------------------------------------

if "utilisateur" not in st.session_state:
    st.session_state["utilisateur"] = f"invite-{uuid.uuid4().hex[:8]}"
UTILISATEUR = st.session_state["utilisateur"]

st.title("🎬 VideoIA")
st.caption("Transforme une image en vidéo animée, pilotée par l'IA.")

if not REPLICATE_API_TOKEN:
    st.error(
        "**Aucun fournisseur vidéo n'est configuré.** VideoIA ne peut "
        "générer aucune vidéo tant qu'un jeton d'API réel (`REPLICATE_API_TOKEN`) "
        "n'est pas renseigné : voir le README. Rien n'est simulé — tu peux "
        "régler tous les paramètres ci-dessous, mais la génération sera "
        "refusée sans jeton valide."
    )

# --------------------------------------------------
# Barre latérale : historique et reprise
# --------------------------------------------------

with st.sidebar:
    st.header("📜 Historique")
    historique = db.historique_utilisateur(UTILISATEUR)
    if not historique:
        st.caption("Aucune création pour l'instant.")
    for job in historique:
        icone = {
            "termine": "✅", "echec": "❌", "interrompu": "⏸️",
            "en_cours": "⏳", "en_attente": "🕓",
        }.get(job["statut"], "•")
        st.write(f"{icone} {job['description'][:30] or '(sans description)'}")
        st.caption(f"{job['format_nom']} · {job['duree_cible_secondes']} s · {job['statut']}")
        if job["statut"] in ("en_attente", "en_cours", "interrompu"):
            if st.button("↻ Reprendre", key=f"reprendre_{job['id']}"):
                st.session_state["job_a_reprendre"] = job["id"]
                st.rerun()
        st.divider()

# --------------------------------------------------
# Reprise d'un job interrompu
# --------------------------------------------------

if "job_a_reprendre" in st.session_state:
    job_id = st.session_state.pop("job_a_reprendre")
    job = db.obtenir_job(job_id)
    if job:
        parametres = ParametresGeneration(
            description=job["description"],
            duree_cible_secondes=job["duree_cible_secondes"],
            format_nom=job["format_nom"],
            qualite_nom=job["qualite_nom"],
        )
        st.subheader("Reprise de la génération")
        st.write(f"« {job['description']} » — {job['duree_cible_secondes']} s")
        zone_progression = st.empty()
        barre = st.progress(0)
        for etat in executer_job(job_id, parametres):
            with zone_progression:
                st.write(etat.message)
            if etat.nb_segments:
                barre.progress(min(1.0, etat.segment_courant / etat.nb_segments))
            if etat.etape == "termine":
                st.success("Vidéo prête.")
                st.video(etat.chemin_video_finale)
                with open(etat.chemin_video_finale, "rb") as f:
                    st.download_button(
                        "⬇️ Télécharger le MP4", f, file_name="videoia.mp4", mime="video/mp4",
                    )
            elif etat.etape == "erreur":
                st.error(etat.message)
        st.stop()

# --------------------------------------------------
# Formulaire principal
# --------------------------------------------------

st.subheader("1. Image de départ")
image_televersee = st.file_uploader(
    "Dépose une image (JPG, PNG ou WEBP)", type=["jpg", "jpeg", "png", "webp"],
)
if image_televersee is not None:
    st.image(image_televersee, caption="Aperçu", width="stretch")

st.subheader("2. Description de l'animation (facultatif)")
description = st.text_area(
    "Décris le mouvement ou l'ambiance souhaités",
    placeholder="Ex. : la caméra avance lentement, les nuages défilent, "
                "lumière dorée de fin de journée…",
    height=100,
)

st.subheader("3. Paramètres")
col1, col2 = st.columns(2)
duree_nom = col1.selectbox("Durée", list(DUREES_DISPONIBLES.keys()), index=1)
format_nom = col2.selectbox("Format", list(FORMATS_DISPONIBLES.keys()))
qualite_nom = st.selectbox("Qualité", list(QUALITES_DISPONIBLES.keys()))

duree_cible_secondes = DUREES_DISPONIBLES[duree_nom]
parametres = ParametresGeneration(
    description=description.strip(),
    duree_cible_secondes=duree_cible_secondes,
    format_nom=format_nom,
    qualite_nom=qualite_nom,
)

# ---- Estimation et avertissements, calculés dès que la durée change ----

st.write(
    f"Cette vidéo demandera **{parametres.nb_segments} segment(s)** de "
    f"{DUREE_MAX_CLIP_UNIQUE_SECONDES} s maximum chacun, enchaînés et "
    "assemblés automatiquement."
)
st.caption(
    f"Estimation (ordre de grandeur, pas un engagement) : environ "
    f"{parametres.estimation_secondes // 60} min {parametres.estimation_secondes % 60} s "
    f"de traitement et {parametres.estimation_cout_usd:.2f} $ d'appels API."
)

if duree_cible_secondes >= SEUIL_AVERTISSEMENT_SECONDES:
    st.warning(
        f"**Durée importante ({duree_nom}).** Une vidéo aussi longue, "
        "générée par segments successifs, demande de nombreux appels au "
        "moteur vidéo, du temps (potentiellement plusieurs heures), de "
        "l'espace de stockage et un budget réel. La cohérence visuelle "
        "entre les segments n'est pas garantie à 100 % : chaque segment "
        "repart de l'image de départ, mais un moteur de génération peut "
        "dériver sur de longues séquences. Confirme ci-dessous pour "
        "continuer."
    )
    confirmation = st.checkbox(
        "Je comprends le temps, le coût et les limites de cohérence, et je "
        "veux continuer."
    )
else:
    confirmation = True

st.subheader("4. Génération")
bouton_pret = image_televersee is not None and confirmation

if st.button("🎬 Générer ma vidéo", type="primary", disabled=not bouton_pret):
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    extension = Path(image_televersee.name).suffix or ".png"
    chemin_image = str(UPLOADS_DIR / f"{uuid.uuid4().hex}{extension}")
    with open(chemin_image, "wb") as f:
        f.write(image_televersee.getbuffer())

    job_id = creer_et_planifier(UTILISATEUR, chemin_image, parametres)

    zone_progression = st.empty()
    barre = st.progress(0)
    try:
        for etat in executer_job(job_id, parametres):
            with zone_progression:
                st.write(etat.message)
            if etat.nb_segments:
                barre.progress(min(1.0, etat.segment_courant / etat.nb_segments))
            if etat.etape == "termine":
                st.success("🎉 Vidéo prête !")
                st.video(etat.chemin_video_finale)
                with open(etat.chemin_video_finale, "rb") as f:
                    st.download_button(
                        "⬇️ Télécharger le MP4", f, file_name="videoia.mp4",
                        mime="video/mp4",
                    )
            elif etat.etape == "erreur":
                st.error(etat.message)
                st.info(
                    "Le job est enregistré comme interrompu : tu peux le "
                    "reprendre depuis l'historique, à gauche, sans repayer "
                    "les segments déjà générés."
                )
    except MoteurVideoNonConfigure as e:
        st.error(str(e))

elif not image_televersee:
    st.caption("Importe une image pour activer la génération.")
elif not confirmation:
    st.caption("Confirme l'avertissement ci-dessus pour activer la génération.")

