"""
Orchestre la génération d'un job complet : planifie les segments, les génère
un par un via le moteur vidéo actif, gère les erreurs et les reprises, puis
assemble le résultat final avec FFmpeg.

Conçu pour être appelé depuis l'interface Streamlit via un générateur Python
(`for etat in executer_job(...): ...`) afin que l'UI puisse afficher la
progression en direct, sans fil d'exécution séparé.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from config import OUTPUTS_DIR, SEGMENTS_DIR, ParametresGeneration
from engine.base import DemandeClip, EchecGenerationClip, MoteurVideoNonConfigure, StatutClip
from engine.registry import obtenir_moteur
from pipeline.assembler import EchecAssemblage, assembler_par_concatenation
from pipeline.segmenter import planifier_segments
from storage import db

NB_TENTATIVES_MAX_PAR_SEGMENT = 3
INTERVALLE_VERIFICATION_SECONDES = 4.0


@dataclass
class EtatProgression:
    job_id: str
    etape: str  # "planification" | "segment" | "assemblage" | "termine" | "erreur"
    segment_courant: int
    nb_segments: int
    message: str
    chemin_video_finale: str | None = None


def creer_et_planifier(
    utilisateur: str, chemin_image: str, parametres: ParametresGeneration,
) -> str:
    """Crée le job et ses segments en base, renvoie l'id du job."""
    job_id = db.creer_job(
        utilisateur=utilisateur,
        description=parametres.description,
        duree_cible_secondes=parametres.duree_cible_secondes,
        format_nom=parametres.format_nom,
        qualite_nom=parametres.qualite_nom,
        chemin_image=chemin_image,
    )
    plan = planifier_segments(
        parametres.description,
        parametres.duree_cible_secondes,
        parametres.duree_segment_secondes,
    )
    db.ajouter_segments(
        job_id, [(s.position, s.description, s.duree_secondes) for s in plan]
    )
    return job_id


def executer_job(job_id: str, parametres: ParametresGeneration):
    """
    Générateur : produit un EtatProgression à chaque avancée. Reprend
    automatiquement les segments déjà "termine" (c'est la reprise d'un job
    interrompu) et ne régénère que ce qui manque.
    """
    job = db.obtenir_job(job_id)
    if job is None:
        yield EtatProgression(job_id, "erreur", 0, 0, "Job introuvable.")
        return

    segments = db.obtenir_segments(job_id)
    nb_segments = len(segments)
    db.maj_statut_job(job_id, "en_cours")

    try:
        moteur = obtenir_moteur()
    except Exception as e:
        db.maj_statut_job(job_id, "echec", message_erreur=str(e))
        yield EtatProgression(job_id, "erreur", 0, nb_segments, str(e))
        return

    largeur, hauteur = parametres.resolution
    qualite_cle = parametres.qualite_nom

    for segment in segments:
        position = segment["position"]
        yield EtatProgression(
            job_id, "segment", position, nb_segments,
            f"Segment {position + 1}/{nb_segments}…",
        )

        if segment["statut"] == "termine" and segment["chemin_fichier"] and (
            Path(segment["chemin_fichier"]).exists()
        ):
            # Déjà généré lors d'une tentative précédente : on garde le
            # fichier existant plutôt que de refaire un appel payant.
            continue

        demande = DemandeClip(
            chemin_image=job["chemin_image"],
            description=segment["description"],
            duree_secondes=segment["duree_secondes"],
            largeur=largeur,
            hauteur=hauteur,
            qualite_cle=qualite_cle,
            graine=0,  # graine fixe : limite la dérive de style entre segments
        )

        reussi = False
        derniere_erreur = None
        for _ in range(NB_TENTATIVES_MAX_PAR_SEGMENT):
            db.incrementer_tentatives(segment["id"])
            try:
                resultat = moteur.generer_bloquant(
                    demande, str(SEGMENTS_DIR / job_id),
                    intervalle_secondes=INTERVALLE_VERIFICATION_SECONDES,
                )
            except (MoteurVideoNonConfigure, EchecGenerationClip) as e:
                derniere_erreur = str(e)
                continue

            if resultat.statut == StatutClip.TERMINE:
                db.maj_segment(
                    segment["id"], statut="termine",
                    chemin_fichier=resultat.chemin_fichier,
                    id_tache_fournisseur=resultat.id_tache_fournisseur,
                    message_erreur=None,
                )
                reussi = True
                break
            derniere_erreur = resultat.message_erreur or "Échec non précisé."

        if not reussi:
            db.maj_segment(segment["id"], statut="echec", message_erreur=derniere_erreur)
            db.maj_statut_job(job_id, "interrompu", message_erreur=(
                f"Échec au segment {position + 1}/{nb_segments} : {derniere_erreur}. "
                "Le job peut être repris : les segments déjà générés sont conservés."
            ))
            yield EtatProgression(
                job_id, "erreur", position, nb_segments,
                f"Échec au segment {position + 1}/{nb_segments} : {derniere_erreur}",
            )
            return

    # Tous les segments sont prêts : assemblage.
    yield EtatProgression(job_id, "assemblage", nb_segments, nb_segments, "Assemblage final…")
    segments = db.obtenir_segments(job_id)
    chemins = [s["chemin_fichier"] for s in segments]
    if any(c is None for c in chemins):
        db.maj_statut_job(job_id, "echec", message_erreur="Segment manquant avant assemblage.")
        yield EtatProgression(job_id, "erreur", nb_segments, nb_segments,
                              "Segment manquant avant assemblage : incohérence interne.")
        return

    chemin_sortie = str(OUTPUTS_DIR / f"{job_id}.mp4")
    try:
        assembler_par_concatenation(chemins, chemin_sortie)
    except EchecAssemblage as e:
        db.maj_statut_job(job_id, "echec", message_erreur=str(e))
        yield EtatProgression(job_id, "erreur", nb_segments, nb_segments, str(e))
        return

    db.maj_statut_job(job_id, "termine", chemin_video_finale=chemin_sortie)
    yield EtatProgression(
        job_id, "termine", nb_segments, nb_segments,
        "Vidéo prête.", chemin_video_finale=chemin_sortie,
    )
