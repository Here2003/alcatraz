"""
Configuration centrale de VideoIA.

Rien ici ne doit jamais prétendre qu'une vidéo a été générée si elle ne l'a
pas été : les limites ci-dessous sont utilisées à la fois par l'interface
(pour avertir l'utilisateur) et par le pipeline (pour refuser une demande
irréaliste plutôt que de simuler un résultat).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# --------------------------------------------------
# Emplacements
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("VIDEOIA_DATA_DIR", BASE_DIR / "data"))
UPLOADS_DIR = DATA_DIR / "uploads"
SEGMENTS_DIR = DATA_DIR / "segments"
OUTPUTS_DIR = DATA_DIR / "outputs"
DB_PATH = DATA_DIR / "videoia.sqlite3"

for d in (DATA_DIR, UPLOADS_DIR, SEGMENTS_DIR, OUTPUTS_DIR):
    d.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# Formats proposés à l'utilisateur
# --------------------------------------------------

DUREES_DISPONIBLES = {
    "10 secondes": 10,
    "30 secondes": 30,
    "1 minute": 60,
    "5 minutes": 5 * 60,
    "10 minutes": 10 * 60,
    "20 minutes": 20 * 60,
    "30 minutes": 30 * 60,
}

FORMATS_DISPONIBLES = {
    "Vertical 9:16": (1080, 1920),
    "Horizontal 16:9": (1920, 1080),
    "Carré 1:1": (1080, 1080),
}

QUALITES_DISPONIBLES = {
    "Standard (720p, rapide, moins cher)": {"hauteur_max": 720, "cle": "standard"},
    "Haute (1080p)": {"hauteur_max": 1080, "cle": "haute"},
}

# --------------------------------------------------
# Limites réalistes du moteur vidéo
# --------------------------------------------------

# Durée d'un clip que le moteur image→vidéo sait produire en un seul appel.
# Les modèles actuels (fin 2025) génèrent quelques secondes par appel : au
#-delà, VideoIA doit obligatoirement passer par la génération en segments.
DUREE_MAX_CLIP_UNIQUE_SECONDES = 10

# Au-delà de cette durée totale, le nombre de segments et le coût deviennent
# tels que VideoIA affiche un avertissement fort et demande une confirmation
# explicite avant de lancer la génération.
SEUIL_AVERTISSEMENT_SECONDES = 5 * 60

# Estimation de coût/temps par segment, affichée à l'utilisateur. Ce sont des
# ORDRES DE GRANDEUR à ajuster une fois un fournisseur réel branché (voir
# engine/replicate_engine.py) : ne jamais les présenter comme des montants
# garantis.
ESTIMATION_SECONDES_TRAITEMENT_PAR_SEGMENT = 60
ESTIMATION_COUT_USD_PAR_SEGMENT = 0.08

# Nombre maximal de segments qu'un job peut contenir, même si l'utilisateur
# choisit 30 minutes : protège contre un budget et un temps de génération
# totalement déraisonnables tant qu'aucune limite métier n'a été fixée.
NB_SEGMENTS_MAX = 240


@dataclass(frozen=True)
class ParametresGeneration:
    description: str
    duree_cible_secondes: int
    format_nom: str
    qualite_nom: str
    duree_segment_secondes: int = DUREE_MAX_CLIP_UNIQUE_SECONDES

    @property
    def resolution(self) -> tuple[int, int]:
        return FORMATS_DISPONIBLES[self.format_nom]

    @property
    def nb_segments(self) -> int:
        import math

        return max(1, math.ceil(self.duree_cible_secondes / self.duree_segment_secondes))

    @property
    def estimation_secondes(self) -> int:
        return self.nb_segments * ESTIMATION_SECONDES_TRAITEMENT_PAR_SEGMENT

    @property
    def estimation_cout_usd(self) -> float:
        return round(self.nb_segments * ESTIMATION_COUT_USD_PAR_SEGMENT, 2)


# --------------------------------------------------
# Fournisseur de génération vidéo
# --------------------------------------------------

# Nom du moteur actif. "replicate" appelle une vraie API (voir
# engine/replicate_engine.py) ; il faut un jeton pour qu'il fonctionne.
# Aucun autre moteur de ce fichier ne doit produire de fausse vidéo.
MOTEUR_VIDEO = os.environ.get("VIDEOIA_ENGINE", "replicate")

REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN", "")

# Modèle Replicate utilisé pour l'image→vidéo. Remplaçable sans toucher au
# reste de l'application : voir engine/replicate_engine.py.
REPLICATE_MODELE_IMAGE_VERS_VIDEO = os.environ.get(
    "VIDEOIA_REPLICATE_MODEL",
    "stability-ai/stable-video-diffusion",
)
