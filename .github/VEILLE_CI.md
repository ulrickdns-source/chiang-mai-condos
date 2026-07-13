# Routine de veille — exécution CLOUD (GitHub Actions)

Ce fichier est lu par le job planifié `.github/workflows/veille.yml` qui tourne
**chaque semaine sur les serveurs GitHub** (donc PC éteint). Objectif : détecter de
NOUVEAUX condos/maisons à louer à Chiang Mai, régénérer `data.js`, committer, pousser
→ le site GitHub Pages se met à jour tout seul.

## Contraintes CI (importantes)
- **Pas de sous-agents** (Task/Agent/background) : ils sont tués en mode headless.
  Tu fais TOUT toi-même, **séquentiellement**, dans cette seule session.
- Budget limité (turns/temps). Vise l'efficacité, pas l'exhaustivité : quelques vrais
  nouveaux biens valent mieux qu'un run qui explose le budget.
- **Anti-hallucination absolue** : ne jamais inventer un bien, un prix, une note Google
  ou une URL d'image. `null` si tu n'as pas la vraie donnée.

## Étapes (à exécuter dans l'ordre)
1. Tu es à la racine du repo. Lis `SOURCES.md` (sources exploitables) et le début de
   `data.js` (état actuel, champ `type` : "condo"/"house").
2. **Découverte ciblée** (synchrone, sources du groupe A de SOURCES.md qui répondent aux
   bots : Perfect Homes `perfecthomes.co.th`, Thailand-Property `thailand-property.com`,
   PropertyScout `propertyscout.co.th`, Renthub `renthub.in.th`). Avec WebSearch + WebFetch,
   cherche des annonces **récentes** de condos ET de maisons/villas à louer à Chiang Mai,
   tous budgets. Concentre-toi sur des biens qui ne sont PAS déjà dans `data.js`.
   Écris ce que tu trouves (schéma ci-dessous) :
   - condos → `data/raw_ci.json`
   - maisons/villas → `data/rawhouse_ci.json`
   (écrase le contenu de la semaine précédente : `data.js` sert déjà de mémoire.)
3. Lance le pipeline :
   ```bash
   python3 consolidate.py && python3 geocode.py && python3 generate_datajs.py
   ```
   `generate_datajs.py` stampe automatiquement `first_seen`/`is_new` : les biens dont la
   clé est absente de `data/first_seen.json` reçoivent la date du jour et le flag « nouveauté ».
4. Vérifie rapidement (0 doublon, budget) avec la commande Node de `CHANGELOG.md`.
5. Ajoute une ligne en tête de l'historique de `CHANGELOG.md` :
   `- AAAA-MM-JJ (CI) : N biens (Δ), X nouveautés, Y condos / Z maisons.`
6. **Ne touche pas** à `index.html`.
7. Si (et seulement si) tu as trouvé de vrais nouveaux biens, laisse les fichiers modifiés
   (`data.js`, `data/first_seen.json`, `data/*_ci.json`, `CHANGELOG.md`) : l'étape suivante
   du workflow committe et pousse. Sinon, ne modifie rien (« aucune nouveauté cette semaine »).

## Schéma d'un bien (JSON)
`name, zone, area, rent_min, rent_max, bedrooms, desc (FR ≤140c), nomad_score (1-5),
google_rating (réel/null), google_reviews (int/null), image_url (og:image réelle/null),
source (URL réelle), type ("condo"|"house")`

Zones valides : Nimman, Santitham, Chang Phueak, Huay Kaew, Jet Yod, Old City,
Suthep / CMU, Doi Suthep, Central Festival, Superhighway, Riverside, Nong Hoi,
Hang Dong, Mae Rim, San Sai, San Kamphaeng, Autres.
