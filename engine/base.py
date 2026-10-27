"""
Interface commune à tout moteur de génération vidéo.

Un moteur sait faire une seule chose : à partir d'une image et d'une
description, produire UN clip court (quelques secondes). C'est le pipeline
(pipeline/job_manager.py) qui enchaîne plusieurs clips pour former une vidéo
longue. Séparer les deux permet de changer de fournisseur (Replicate, Runway,
Luma, un modèle auto-hébergé...) sans toucher au reste de l'application : il
suffit d'écrire une nouvelle classe qui hérite de VideoEngine.

RÈGLE ABSOLUE : un moteur ne doit jamais renvoyer un statut "terminé" sans
avoir réellement reçu un fichier vidéo du fournisseur. En cas de doute,
erreur ou API non configurée : lever une exception, jamais fabriquer un faux
succès.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class StatutClip(str, Enum):
    EN_ATTENTE = "en_attente"
    EN_COURS = "en_cours"
    TERMINE = "termine"
    ECHEC = "echec"


@dataclass
class DemandeClip:
    """Ce qu'on demande au moteur pour produire UN segment."""

    chemin_image: str
    description: str
    duree_secondes: int
    largeur: int
    hauteur: int
    qualite_cle: str
    graine: int | None = None  # pour tenter de garder un style cohérent


@dataclass
class ResultatClip:
    statut: StatutClip
    chemin_fichier: str | None = None
    id_tache_fournisseur: str | None = None
    message_erreur: str | None = None


class MoteurVideoNonConfigure(RuntimeError):
    """Levée quand un moteur est choisi mais n'a pas ses identifiants/API."""


class EchecGenerationClip(RuntimeError):
    """Levée quand le fournisseur a répondu, mais en échec."""


class VideoEngine(ABC):
    """
    Un moteur de génération image → vidéo.

    Le cycle d'usage attendu, côté pipeline, est :
        tache = moteur.lancer(demande)       # démarre la génération
        statut = moteur.verifier(tache)       # interrogé périodiquement
        # quand statut.statut == TERMINE : statut.chemin_fichier existe
    Cette séparation lancer/vérifier colle à la façon dont fonctionnent les
    API de génération vidéo réelles (asynchrones, par nature).
    """

    nom: str

    @abstractmethod
    def lancer(self, demande: DemandeClip) -> str:
        """
        Démarre la génération d'un clip et renvoie un identifiant de tâche
        côté fournisseur. Ne doit pas bloquer jusqu'à la fin de la
        génération.
        """

    @abstractmethod
    def verifier(self, id_tache: str, dossier_sortie: str) -> ResultatClip:
        """
        Interroge l'état d'une tâche. Si elle est terminée, télécharge le
        fichier vidéo dans `dossier_sortie` et renvoie son chemin exact.
        """

    def generer_bloquant(
        self, demande: DemandeClip, dossier_sortie: str,
        intervalle_secondes: float = 3.0, timeout_secondes: float = 600.0,
    ) -> ResultatClip:
        """
        Pratique pour les tests ou un usage simple : lance puis attend.
        Le pipeline de production préfère lancer()/verifier() séparément
        pour ne jamais bloquer l'interface.
        """
        import time

        id_tache = self.lancer(demande)
        attendu = 0.0
        while attendu < timeout_secondes:
            resultat = self.verifier(id_tache, dossier_sortie)
            if resultat.statut in (StatutClip.TERMINE, StatutClip.ECHEC):
                return resultat
            time.sleep(intervalle_secondes)
            attendu += intervalle_secondes
        return ResultatClip(
            statut=StatutClip.ECHEC,
            id_tache_fournisseur=id_tache,
            message_erreur="Délai dépassé en attendant le fournisseur.",
        )
