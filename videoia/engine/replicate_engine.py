"""
Moteur réel : appelle l'API Replicate (https://replicate.com) pour générer
un clip vidéo à partir d'une image.

Replicate héberge plusieurs modèles image→vidéo sous une seule API HTTP
(Stable Video Diffusion, et d'autres selon ce qui est disponible) — c'est
pourquoi il est choisi comme fournisseur par défaut : ça laisse le choix du
modèle précis sans changer de code d'intégration.

Rien ici n'est simulé : si REPLICATE_API_TOKEN n'est pas renseigné, ou si
l'appel échoue, une exception est levée. Aucune fausse vidéo n'est produite.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from pathlib import Path

from config import REPLICATE_API_TOKEN, REPLICATE_MODELE_IMAGE_VERS_VIDEO
from engine.base import (
    DemandeClip,
    EchecGenerationClip,
    MoteurVideoNonConfigure,
    ResultatClip,
    StatutClip,
    VideoEngine,
)

API_BASE = "https://api.replicate.com/v1"


class MoteurReplicate(VideoEngine):
    nom = "replicate"

    def __init__(self, token: str | None = None, modele: str | None = None):
        self.token = token or REPLICATE_API_TOKEN
        self.modele = modele or REPLICATE_MODELE_IMAGE_VERS_VIDEO

    # ---------------------------------------------------------------
    # Appels HTTP bas niveau (sans dépendance externe : urllib suffit)
    # ---------------------------------------------------------------

    def _requete(self, methode: str, chemin: str, corps: dict | None = None) -> dict:
        if not self.token:
            raise MoteurVideoNonConfigure(
                "Aucun jeton Replicate (REPLICATE_API_TOKEN). VideoIA ne "
                "peut pas générer de vidéo tant qu'un fournisseur réel "
                "n'est pas configuré : voir le README."
            )
        url = f"{API_BASE}{chemin}"
        data = json.dumps(corps).encode("utf-8") if corps is not None else None
        requete = urllib.request.Request(
            url,
            data=data,
            method=methode,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(requete, timeout=30) as reponse:
                return json.loads(reponse.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")
            raise EchecGenerationClip(
                f"Replicate a refusé la requête ({e.code}) : {detail}"
            ) from e
        except urllib.error.URLError as e:
            raise EchecGenerationClip(
                f"Impossible de joindre Replicate : {e.reason}"
            ) from e

    def _image_en_data_uri(self, chemin_image: str) -> str:
        import base64
        import mimetypes

        type_mime, _ = mimetypes.guess_type(chemin_image)
        type_mime = type_mime or "image/png"
        contenu = Path(chemin_image).read_bytes()
        encode = base64.b64encode(contenu).decode("ascii")
        return f"data:{type_mime};base64,{encode}"

    # ---------------------------------------------------------------
    # Interface VideoEngine
    # ---------------------------------------------------------------

    def lancer(self, demande: DemandeClip) -> str:
        entrees = {
            "input_image": self._image_en_data_uri(demande.chemin_image),
            "prompt": demande.description,
            # Les noms de paramètres varient selon le modèle Replicate
            # précis : à ajuster selon la fiche du modèle choisi dans
            # config.REPLICATE_MODELE_IMAGE_VERS_VIDEO.
            "num_frames": max(1, demande.duree_secondes * 24),
            "width": demande.largeur,
            "height": demande.hauteur,
        }
        if demande.graine is not None:
            entrees["seed"] = demande.graine

        reponse = self._requete(
            "POST",
            "/predictions",
            {"version": self.modele, "input": entrees},
        )
        id_tache = reponse.get("id")
        if not id_tache:
            raise EchecGenerationClip(
                f"Réponse Replicate inattendue, pas d'identifiant de tâche : {reponse}"
            )
        return id_tache

    def verifier(self, id_tache: str, dossier_sortie: str) -> ResultatClip:
        reponse = self._requete("GET", f"/predictions/{id_tache}")
        statut = reponse.get("status")

        if statut in ("starting", "processing"):
            return ResultatClip(statut=StatutClip.EN_COURS, id_tache_fournisseur=id_tache)

        if statut == "succeeded":
            sortie = reponse.get("output")
            url_video = sortie[0] if isinstance(sortie, list) else sortie
            if not url_video:
                return ResultatClip(
                    statut=StatutClip.ECHEC,
                    id_tache_fournisseur=id_tache,
                    message_erreur="Succès annoncé par Replicate mais aucun fichier renvoyé.",
                )
            chemin = self._telecharger(url_video, dossier_sortie, id_tache)
            return ResultatClip(
                statut=StatutClip.TERMINE,
                chemin_fichier=chemin,
                id_tache_fournisseur=id_tache,
            )

        if statut in ("failed", "canceled"):
            return ResultatClip(
                statut=StatutClip.ECHEC,
                id_tache_fournisseur=id_tache,
                message_erreur=reponse.get("error") or f"Statut Replicate : {statut}",
            )

        return ResultatClip(statut=StatutClip.EN_ATTENTE, id_tache_fournisseur=id_tache)

    def _telecharger(self, url: str, dossier_sortie: str, id_tache: str) -> str:
        Path(dossier_sortie).mkdir(parents=True, exist_ok=True)
        destination = Path(dossier_sortie) / f"{id_tache}.mp4"
        try:
            urllib.request.urlretrieve(url, destination)
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            raise EchecGenerationClip(
                f"Échec du téléchargement du clip généré : {e}"
            ) from e
        return str(destination)
