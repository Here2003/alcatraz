"""
Point d'entrée unique pour obtenir le moteur vidéo actif.

Changer de fournisseur se fait en un point : ajouter une entrée ici (et un
fichier engine/<nom>_engine.py qui implémente VideoEngine), jamais en
modifiant le pipeline ou l'interface.
"""

from __future__ import annotations

from config import MOTEUR_VIDEO
from engine.base import VideoEngine


def obtenir_moteur() -> VideoEngine:
    if MOTEUR_VIDEO == "replicate":
        from engine.replicate_engine import MoteurReplicate

        return MoteurReplicate()

    raise ValueError(
        f"Moteur vidéo inconnu : {MOTEUR_VIDEO!r}. Ajoute une entrée dans "
        "engine/registry.py pour le prendre en charge."
    )
