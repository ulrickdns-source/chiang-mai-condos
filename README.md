# 🏙️ Veille Condos & Maisons · Chiang Mai

Base de données locale + mini-site pour suivre les **condos ET maisons/villas** à louer à
Chiang Mai, ciblés pour une **nomade digitale**. Condos : budget ~3 000–50 000 ฿/mois.
Maisons/villas : **tout budget** (jusqu'à ~200 000 ฿/mois). Filtre Tous / Condos / Maisons dans l'UI.

## Ouvrir le site
Double-clique sur **`index.html`** (s'ouvre dans ton navigateur).
> ⚠️ Si les cartes n'apparaissent pas en `file://` (sécurité navigateur), lance un mini-serveur :
> ```bash
> cd ~/chiang-mai-condos && python3 -m http.server 8799
> ```
> puis ouvre http://localhost:8799/index.html

## Ce qu'il y a dedans
- **`index.html`** — le site : header sombre moderne, **carte interactive Leaflet** avec les 253 condos
  épinglés (couleur par quartier, popups prix/note, suit les filtres), recherche, filtres par zone, filtre
  budget, tri (note Google / prix / coup de cœur), cases « avec photo » / « avec note Google ». Chaque condo
  est une **carte avec photo réelle**, sa **note Google Maps + nombre d'avis** (alerte orange quand très peu
  d'avis), une description courte et un lien **Maps**. + barre repliable de **liens Facebook préremplis**.
- **`data.js`** — les données (**253 immeubles uniques vérifiés**, dont 32 avec vraie note Google et 173 avec photo).
  C'est ce fichier que la routine régénère.
- **`REFRESH_PROMPT.md`** — instructions exactes du pipeline de veille.
- **`consolidate.py`** / **`generate_datajs.py`** — scripts du pipeline (dédup + fusion/génération de `data.js`).
- **`master.json`** — liste maître dédoublonnée (intermédiaire). **`data/raw_*.json`**, **`data/enrich_*.json`** — sorties brutes des agents.
- **`CHANGELOG.md`** — historique des mises à jour.

> **Note importante** : toutes les notes ne sont pas couvertes — seuls ~32 immeubles ont une vraie fiche
> Google Maps trouvable (les petits apparts/mansions n'en ont pas). Les autres affichent « Sans avis Google »
> plutôt qu'une note inventée. Idem photos : ~173/253 ont une vraie photo, les autres un visuel de remplacement.

## Zones couvertes
Nimman · Santitham · Chang Phueak · Huay Kaew · Jet Yod · Old City · Suthep/CMU ·
Doi Suthep · Central Festival · Superhighway · Riverside · Nong Hoi · Autres.

## La routine automatique
Une tâche planifiée (`refresh-condos-chiangmai`) tourne **le 1er et le 15 de chaque mois à 9h**
(≈ toutes les 2 semaines). À chaque passage elle relance la recherche sur les portails, dédoublonne,
et réécrit `data.js` avec la nouvelle date. Elle tourne **quand l'app est ouverte** ; si elle était
fermée au moment prévu, elle se lance au prochain démarrage.

- Voir / modifier la fréquence : demande-moi, ou via les tâches planifiées de l'app.
- Sources : DDproperty, Hipflat, FazWaz, Thailand-Property, Renthub, PerfectHomes, NomadRental, guides nomades.

## Note sur Facebook
Le scraping automatique des groupes FB n'est ni fiable ni autorisé (login, anti-bot, CGU).
Le site fournit donc des **liens préremplis** vers les bons groupes/recherches : un clic et tu vois les posts du jour.

## Note sur les prix
Les montants sont des **fourchettes mensuelles indicatives** (selon le type d'unité).
Toujours confirmer l'unité exacte et la dispo auprès de l'agent / du portail avant de t'engager.
