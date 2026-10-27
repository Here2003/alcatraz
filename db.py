"""
Stockage des jobs, segments et historique.

SQLite suffit largement ici : une table "jobs" (une vidéo demandée par un
utilisateur) et une table "segments" (chaque clip qui la compose), ce qui
permet de reprendre un job interrompu segment par segment plutôt que de tout
relancer depuis le début.
"""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from pathlib import Path

from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    utilisateur TEXT NOT NULL,
    description TEXT NOT NULL,
    duree_cible_secondes INTEGER NOT NULL,
    format_nom TEXT NOT NULL,
    qualite_nom TEXT NOT NULL,
    chemin_image TEXT NOT NULL,
    statut TEXT NOT NULL,
    message_erreur TEXT,
    chemin_video_finale TEXT,
    cree_le REAL NOT NULL,
    maj_le REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS segments (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL REFERENCES jobs(id),
    position INTEGER NOT NULL,
    description TEXT NOT NULL,
    duree_secondes INTEGER NOT NULL,
    statut TEXT NOT NULL,
    id_tache_fournisseur TEXT,
    chemin_fichier TEXT,
    message_erreur TEXT,
    nb_tentatives INTEGER NOT NULL DEFAULT 0,
    maj_le REAL NOT NULL,
    UNIQUE(job_id, position)
);
"""


@contextmanager
def connexion():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def initialiser():
    with connexion() as conn:
        conn.executescript(SCHEMA)


# --------------------------------------------------
# Jobs
# --------------------------------------------------

def creer_job(
    utilisateur: str, description: str, duree_cible_secondes: int,
    format_nom: str, qualite_nom: str, chemin_image: str,
) -> str:
    job_id = str(uuid.uuid4())
    maintenant = time.time()
    with connexion() as conn:
        conn.execute(
            """INSERT INTO jobs (
                id, utilisateur, description, duree_cible_secondes,
                format_nom, qualite_nom, chemin_image, statut,
                message_erreur, chemin_video_finale, cree_le, maj_le
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'en_attente', NULL, NULL, ?, ?)""",
            (job_id, utilisateur, description, duree_cible_secondes,
             format_nom, qualite_nom, chemin_image, maintenant, maintenant),
        )
    return job_id


def ajouter_segments(job_id: str, segments: list[tuple[int, str, int]]):
    """segments : liste de (position, description, duree_secondes)."""
    maintenant = time.time()
    with connexion() as conn:
        conn.executemany(
            """INSERT INTO segments (
                id, job_id, position, description, duree_secondes,
                statut, maj_le
            ) VALUES (?, ?, ?, ?, ?, 'en_attente', ?)""",
            [
                (str(uuid.uuid4()), job_id, position, description, duree, maintenant)
                for position, description, duree in segments
            ],
        )


def maj_statut_job(job_id: str, statut: str, message_erreur: str | None = None,
                   chemin_video_finale: str | None = None):
    with connexion() as conn:
        conn.execute(
            """UPDATE jobs SET statut = ?, message_erreur = ?,
               chemin_video_finale = COALESCE(?, chemin_video_finale),
               maj_le = ? WHERE id = ?""",
            (statut, message_erreur, chemin_video_finale, time.time(), job_id),
        )


def maj_segment(segment_id: str, **champs):
    champs["maj_le"] = time.time()
    colonnes = ", ".join(f"{c} = ?" for c in champs)
    with connexion() as conn:
        conn.execute(
            f"UPDATE segments SET {colonnes} WHERE id = ?",
            (*champs.values(), segment_id),
        )


def incrementer_tentatives(segment_id: str):
    with connexion() as conn:
        conn.execute(
            "UPDATE segments SET nb_tentatives = nb_tentatives + 1, maj_le = ? WHERE id = ?",
            (time.time(), segment_id),
        )


def obtenir_job(job_id: str) -> dict | None:
    with connexion() as conn:
        ligne = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return dict(ligne) if ligne else None


def obtenir_segments(job_id: str) -> list[dict]:
    with connexion() as conn:
        lignes = conn.execute(
            "SELECT * FROM segments WHERE job_id = ? ORDER BY position", (job_id,)
        ).fetchall()
        return [dict(l) for l in lignes]


def historique_utilisateur(utilisateur: str, limite: int = 50) -> list[dict]:
    with connexion() as conn:
        lignes = conn.execute(
            """SELECT * FROM jobs WHERE utilisateur = ?
               ORDER BY cree_le DESC LIMIT ?""",
            (utilisateur, limite),
        ).fetchall()
        return [dict(l) for l in lignes]


def jobs_reprenables(utilisateur: str) -> list[dict]:
    """Jobs interrompus (ni terminés ni en échec définitif) de cet utilisateur."""
    with connexion() as conn:
        lignes = conn.execute(
            """SELECT * FROM jobs WHERE utilisateur = ?
               AND statut IN ('en_attente', 'en_cours', 'interrompu')
               ORDER BY cree_le DESC""",
            (utilisateur,),
        ).fetchall()
        return [dict(l) for l in lignes]
