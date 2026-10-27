"""
Découpe une demande de vidéo longue en segments courts, parce que les
moteurs image→vidéo actuels ne savent produire que quelques secondes par
appel (voir config.DUREE_MAX_CLIP_UNIQUE_SECONDES).

La cohérence visuelle entre segments n'est jamais garantie par ce découpage
seul : chaque segment repart de la MÊME image source et, quand le moteur le
permet, de la même graine aléatoire (voir engine/base.py, DemandeClip.graine)
pour limiter les écarts de style. C'est une atténuation, pas une garantie.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from config import DUREE_MAX_CLIP_UNIQUE_SECONDES, NB_SEGMENTS_MAX


@dataclass
class PlanSegment:
    position: int
    description: str
    duree_secondes: int


def planifier_segments(
    description_globale: str, duree_cible_secondes: int,
    duree_segment_secondes: int = DUREE_MAX_CLIP_UNIQUE_SECONDES,
) -> list[PlanSegment]:
    """
    Construit la liste des segments à générer. Pour l'instant, la même
    description est répétée sur chaque segment (le moteur part toujours de
    l'image initiale) ; un découpage par "scènes" plus fin peut être ajouté
    en remplaçant `description` par segment ici, sans toucher au reste du
    pipeline.
    """
    if duree_cible_secondes <= 0:
        raise ValueError("La durée cible doit être positive.")
    if duree_segment_secondes <= 0:
        raise ValueError("La durée de segment doit être positive.")

    nb_segments = math.ceil(duree_cible_secondes / duree_segment_secondes)
    if nb_segments > NB_SEGMENTS_MAX:
        raise ValueError(
            f"Cette durée demanderait {nb_segments} segments, au-delà de la "
            f"limite de sécurité ({NB_SEGMENTS_MAX}). Réduis la durée cible "
            "ou augmente la limite dans config.py en connaissance de cause."
        )

    plan = []
    reste = duree_cible_secondes
    for position in range(nb_segments):
        duree = min(duree_segment_secondes, reste)
        plan.append(PlanSegment(
            position=position,
            description=description_globale,
            duree_secondes=duree,
        ))
        reste -= duree
    return plan
