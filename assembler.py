"""
Assemble une liste de clips vidéo en une seule vidéo finale, avec FFmpeg.

Deux modes :
- concaténation directe (copie de flux, rapide) quand tous les clips ont
  déjà le même encodage ;
- ré-encodage avec un fondu enchaîné entre chaque clip, plus lent mais plus
  propre visuellement et tolérant des clips hétérogènes.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


class EchecAssemblage(RuntimeError):
    pass


def _verifier_ffmpeg():
    if shutil.which("ffmpeg") is None:
        raise EchecAssemblage(
            "ffmpeg est introuvable sur le serveur : impossible d'assembler "
            "la vidéo finale. Installe ffmpeg et réessaie."
        )


def assembler_par_concatenation(chemins_clips: list[str], chemin_sortie: str) -> str:
    """
    Concaténation rapide (sans ré-encodage). Exige que les clips partagent
    déjà le même codec/résolution/fréquence d'images — c'est le cas normal
    quand ils sortent tous du même moteur avec les mêmes paramètres.
    """
    _verifier_ffmpeg()
    if not chemins_clips:
        raise EchecAssemblage("Aucun clip à assembler.")

    Path(chemin_sortie).parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as liste:
        for chemin in chemins_clips:
            chemin_abs = str(Path(chemin).resolve()).replace("'", "'\\''")
            liste.write(f"file '{chemin_abs}'\n")
        chemin_liste = liste.name

    commande = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", chemin_liste, "-c", "copy", chemin_sortie,
    ]
    resultat = subprocess.run(commande, capture_output=True, text=True)
    Path(chemin_liste).unlink(missing_ok=True)

    if resultat.returncode != 0:
        raise EchecAssemblage(
            f"Échec de la concaténation FFmpeg :\n{resultat.stderr[-2000:]}"
        )
    return chemin_sortie


def assembler_avec_transitions(
    chemins_clips: list[str], chemin_sortie: str, duree_fondu_secondes: float = 0.5,
) -> str:
    """
    Ré-encode et enchaîne les clips avec un fondu croisé (filtre xfade
    audio+vidéo). Plus coûteux en calcul, mais fonctionne même si les clips
    ne sont pas parfaitement identiques en encodage.
    """
    _verifier_ffmpeg()
    if not chemins_clips:
        raise EchecAssemblage("Aucun clip à assembler.")
    if len(chemins_clips) == 1:
        return assembler_par_concatenation(chemins_clips, chemin_sortie)

    Path(chemin_sortie).parent.mkdir(parents=True, exist_ok=True)

    durees = [_duree_clip(c) for c in chemins_clips]

    entrees = []
    for chemin in chemins_clips:
        entrees += ["-i", chemin]

    filtres = []
    label_video_precedent = "0:v"
    label_audio_precedent = "0:a"
    decalage = durees[0] - duree_fondu_secondes

    for i in range(1, len(chemins_clips)):
        label_video_sortie = f"v{i}"
        label_audio_sortie = f"a{i}"
        filtres.append(
            f"[{label_video_precedent}][{i}:v]xfade=transition=fade:"
            f"duration={duree_fondu_secondes}:offset={decalage}[{label_video_sortie}]"
        )
        filtres.append(
            f"[{label_audio_precedent}][{i}:a]acrossfade=d={duree_fondu_secondes}"
            f"[{label_audio_sortie}]"
        )
        label_video_precedent = label_video_sortie
        label_audio_precedent = label_audio_sortie
        if i < len(chemins_clips) - 1:
            decalage += durees[i] - duree_fondu_secondes

    commande = [
        "ffmpeg", "-y", *entrees,
        "-filter_complex", ";".join(filtres),
        "-map", f"[{label_video_precedent}]",
        "-map", f"[{label_audio_precedent}]",
        chemin_sortie,
    ]
    resultat = subprocess.run(commande, capture_output=True, text=True)
    if resultat.returncode != 0:
        raise EchecAssemblage(
            f"Échec de l'assemblage avec transitions :\n{resultat.stderr[-2000:]}"
        )
    return chemin_sortie


def _duree_clip(chemin: str) -> float:
    resultat = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", chemin,
        ],
        capture_output=True, text=True,
    )
    try:
        return float(resultat.stdout.strip())
    except ValueError as e:
        raise EchecAssemblage(f"Impossible de lire la durée de {chemin}") from e
