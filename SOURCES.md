# Sources — condos & maisons à louer à Chiang Mai

Classées par utilité **pour la veille**. La colonne « Bot » indique si la source est
exploitable par la routine automatique (fetch direct) ou seulement à la main.

---

## A. Portails exploitables automatiquement (cœur de la routine) ✅

Ce sont ceux que les agents de découverte arrivent réellement à lire ; la routine s'appuie dessus.

| Source | URL | Type | Bot | Notes |
|---|---|---|---|---|
| **Perfect Homes Chiang Mai** | perfecthomes.co.th | Condos + maisons/villas | ✅ | Listings détaillés, og:images fiables, segment milieu/haut de gamme. Le plus régulier. |
| **Thailand-Property** | thailand-property.com | Condos + maisons | ✅ | Gros volume, pages projet, tout budget. Images parfois dures à extraire. |
| **PropertyScout** | propertyscout.co.th | Maisons/townhouses + condos | ✅ | og:images fiables, bon pour les maisons en ville. |
| **Renthub** | renthub.in.th | Condos + apparts | ✅ (partiel) | Thaï, bon pour le budget 5–15k. |
| **Propertyhub** | propertyhub.in.th | Condos par projet | ✅ (partiel) | Utile pour compléter par nom de résidence. |
| **Hongpak** | hongpak.in.th | Apparts/condos près CMU | ✅ (partiel) | Zone Suthep/CMU. |

## B. Portails « humains » — excellents mais bloquent les bots (403) 🔒

À consulter à la main : ce sont les plus riches en photos et en annonces fraîches,
mais ils renvoient HTTP 403 au fetch automatique. **Ne pas compter dessus pour la routine.**

| Source | URL | Pourquoi le consulter |
|---|---|---|
| **FazWaz** | fazwaz.com | Le plus complet (condos + villas), filtres fins, beaucoup de photos. |
| **Hipflat** | hipflat.com | Fiches projet condo + historique de prix. |
| **DDproperty** | ddproperty.com | Le plus gros portail de Thaïlande, volume maximal. |
| **Dot Property** | dotproperty.co.th | Bon complément, annonces agences. |
| **108 Siam** | 108siam.com | Annonces locales. |

## C. Temps réel / annonces fraîches (jour le jour) 📣

Là où apparaissent les nouveautés avant les portails. Consultation manuelle
(scraping FB non fiable/non autorisé) — des liens préremplis sont déjà dans le site.

- **Facebook — groupes** : « Chiang Mai Houses/Condos for Rent », « Chiang Mai Friends »,
  « Nimman / Santitham for rent », « Expats in Chiang Mai ».
- **Facebook Marketplace** → catégorie locations.
- **Google Maps** : chercher le nom d'un projet/village → note, avis, photos réelles.
- **Reddit** r/chiangmai (occasionnel, retours d'expats).

## D. Agences (maisons & villas, longue durée / haut de gamme) 🏡

- **Lanna Estate** — lannaestate.com
- **Chiangmai-Properties** — chiangmai-properties.com
- **Nice Home Chiang Mai**
- **Baan Thai Property**
- **Prakard** — prakard.com (petites annonces de particuliers)

---

### Ce que la routine utilise
La routine automatique cible en priorité le **groupe A** (Perfect Homes, Thailand-Property,
PropertyScout, Renthub, Propertyhub, Hongpak). Les groupes B/C/D sont documentés ici pour
la **vérification manuelle** et pour ajouter à la main un bien repéré ailleurs
(il suffit de l'ajouter à un `data/rawhouse_*.json` ou `data/raw_*.json` puis de relancer le pipeline).

### Règle d'or (anti-hallucination)
On n'invente **jamais** un immeuble, un prix, une note Google ou une URL d'image.
Note = Google Maps uniquement (sinon `null`). Photo = og:image réelle de la page source (sinon `null`).
