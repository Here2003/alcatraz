# VideoIA

Transforme une image en vidéo animée, en vrai : aucune vidéo n'est jamais
simulée. Sans fournisseur de génération vidéo configuré, l'application
refuse de générer plutôt que de prétendre avoir produit un résultat.

## Lancer l'application

```bash
pip install -r requirements.txt
export REPLICATE_API_TOKEN="ton_jeton_replicate"
streamlit run app.py
```

Sans `REPLICATE_API_TOKEN`, l'interface se lance normalement (tu peux régler
tous les paramètres), mais la génération est refusée avec un message clair.

## Pourquoi Replicate par défaut

[Replicate](https://replicate.com) héberge plusieurs modèles image→vidéo
derrière une seule API HTTP. `config.REPLICATE_MODELE_IMAGE_VERS_VIDEO`
choisit le modèle précis ; change-le selon ce qui est disponible et
correspond à ton besoin (qualité, durée par clip, coût).

Pour brancher un autre fournisseur (Runway, Luma, Kling, un modèle
auto-hébergé...) : crée `engine/<nom>_engine.py` avec une classe qui hérite
de `engine.base.VideoEngine` (deux méthodes à implémenter : `lancer` et
`verifier`), puis ajoute-la dans `engine/registry.py`. Rien d'autre dans
l'application n'a besoin de changer.

## Pourquoi 30 minutes n'est pas un seul appel API

Les modèles de génération image→vidéo actuels produisent quelques secondes
par appel (voir `config.DUREE_MAX_CLIP_UNIQUE_SECONDES`). Une vidéo de 30
minutes est donc découpée en jusqu'à 180 segments (`pipeline/segmenter.py`),
générés un par un, puis assemblés avec FFmpeg (`pipeline/assembler.py`).

Implications réelles, affichées à l'utilisateur dans l'interface :

- **Temps** : chaque segment prend un temps de traitement réel côté
  fournisseur ; pour 180 segments, ça peut représenter plusieurs heures.
- **Coût** : chaque segment est un appel API facturé par le fournisseur.
  `config.ESTIMATION_COUT_USD_PAR_SEGMENT` est un ordre de grandeur à
  corriger avec les tarifs réels du modèle choisi.
- **Stockage** : chaque segment est conservé sur disque jusqu'à
  l'assemblage final (`data/segments/<job_id>/`).
- **Cohérence visuelle** : chaque segment repart de la même image source
  (et, quand le moteur le permet, de la même graine), mais rien ne garantit
  qu'un modèle de génération ne dérive pas sur une longue séquence. Ce n'est
  pas résolu par ce projet, seulement atténué.

Une limite de sécurité (`config.NB_SEGMENTS_MAX`) empêche un job de dépasser
240 segments par erreur de configuration.

## Reprise après erreur

Chaque segment est enregistré en base (`storage/db.py`, SQLite) avec son
statut. Si un segment échoue après plusieurs tentatives
(`pipeline/job_manager.NB_TENTATIVES_MAX_PAR_SEGMENT`), le job passe au
statut `interrompu` et s'arrête — sans perdre les segments déjà générés. Le
bouton « Reprendre » (barre latérale de l'application) relance
`pipeline.job_manager.executer_job`, qui saute les segments déjà terminés et
ne régénère (donc ne repaie) que ce qui manque.

## Structure du projet

```
app.py                  Interface Streamlit
config.py                Paramètres, limites, estimations
engine/
  base.py                Interface VideoEngine (contrat à respecter)
  replicate_engine.py     Implémentation réelle (API Replicate)
  registry.py             Choix du moteur actif
pipeline/
  segmenter.py            Découpe une durée cible en segments
  job_manager.py           Orchestration + reprise
  assembler.py             Assemblage FFmpeg (concaténation ou transitions)
storage/
  db.py                    Jobs, segments, historique (SQLite)
data/                      Images importées, segments, vidéos finales (créé au lancement)
```

## Limites connues de cette version

- Un seul fournisseur réel est implémenté (Replicate). D'autres demandent
  d'écrire leur propre `engine/*.py`.
- La description de l'animation est réutilisée telle quelle pour chaque
  segment ; un découpage en véritables « scènes » différentes (prompt
  différent par segment) peut être ajouté dans `pipeline/segmenter.py` sans
  toucher au reste.
- L'« utilisateur » est un identifiant de session simple (pas de compte ni
  de mot de passe) : à remplacer par une vraie authentification avant un
  usage multi-utilisateurs en production.
- `assembler_par_concatenation` exige des segments au même encodage, ce qui
  est le cas normal en sortie du même moteur avec les mêmes paramètres ;
  `assembler_avec_transitions` est plus tolérant mais plus lent.
