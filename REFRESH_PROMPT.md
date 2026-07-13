# Instructions de la veille automatique — CONDOS Chiang Mai (condos-only)

Référence suivie par la tâche planifiée `refresh-condos-chiangmai`.
Objectif : maintenir une base la plus exhaustive possible des **CONDOMINIUMS** de Chiang Mai
(zone raisonnable, ~15 min de Nimman), budget affiché jusqu'à 50 000 ฿, et régénérer `data.js`.
**Uniquement des condominiums** — pas d'apartment/mansion/serviced/hometel/coliving/hôtel/maison.
**Règle absolue : jamais halluciner.** Un condo n'est inscrit que s'il est vu sur une vraie page ;
tout champ incertain (année, prix, note, promoteur) = null. Mieux vaut vide que faux.

## Schéma d'un condo (dans data.js)
`name, zone, area, rent_min, rent_max, bedrooms, desc, nomad_score, google_rating, google_reviews,
image_url, source, lat, lng, geo_approx, year_completed, developer`
Zones : Nimman, Santitham, Chang Phueak, Huay Kaew, Jet Yod, Old City, Suthep / CMU, Doi Suthep,
Central Festival, Superhighway, Riverside, Nong Hoi, Autres.

## Pipeline à chaque exécution
1. `cd /Users/ulrick/chiang-mai-condos` ; `rm -f data/allcondo_*.json data/enrich_*.json`.
   Garde `master_backup_precondos.json` (base enrichie : notes Google/photos/coords) comme source d'enrichissement.
2. **Ratissage condos** : lance ~10-12 sous-agents general-purpose EN PARALLÈLE qui parcourent les
   ANNUAIRES DE PROJETS CONDOS des portails (Hipflat, FazWaz, DDproperty, Dotproperty, Thailand-Property,
   PropertyScout/Baania) par district (Suthep, Chang Phueak, Fa Ham, Wat Ket, Chang Khlan, Nong Hoi, Si Phum…)
   ET par promoteur (Sansiri/dcondo, CPN/Escent, Supalai, Ornsirin, Palm Springs, Punna, Hillside, Karnkanok, Peaks…).
   Chaque agent ÉCRIT son tableau JSON (schéma : name, district, zone, year_completed, rent_min, rent_max,
   bedrooms, google_rating, google_reviews, developer, source) dans `data/allcondo_<i>.json`. CONDOS ONLY,
   jamais inventer, null si incertain, source URL obligatoire.
3. `python3 consolidate_condos.py` → dédoublonne tous les allcondo_*.json + fusionne avec
   `master_backup_precondos.json` (garde notes Google/photos/coords/desc des condos connus) → `condos_master.json`
   ET écrase `master.json` avec la version condos-only.
4. `python3 geocode.py` (hors-ligne, place chaque condo par sous-quartier pour la carte).
5. `python3 generate_datajs.py` → fusionne enrich + coords, écrit `data.js` (lastUpdated = date du jour,
   budgetMin 3000 / budgetMax 50000, condosOnly:true, avec year_completed + developer).
6. Valide en Node (0 doublon flagrant, parse OK). Ajoute une ligne au CHANGELOG :
   `- AAAA-MM-JJ : N condos (Δ), X avec année, Y notes Google, Z photos`.
7. NE PAS toucher à index.html.

## Enrichissement optionnel (si budget/temps)
- Notes Google : agents WebSearch "<name> Chiang Mai condo google maps rating reviews" (note Google
  explicite uniquement, jamais Booking/Agoda/Trip) → `data/enrich_<i>.json` {name, google_rating, google_reviews, image_url}.
- Photos : og:image réel via WebFetch du `source`.
