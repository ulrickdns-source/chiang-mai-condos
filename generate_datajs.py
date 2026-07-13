#!/usr/bin/env python3
# Fusionne master.json + enrich_*.json -> data.js (window.CONDOS)
import json, glob, os, re, unicodedata, datetime
from collections import Counter

TODAY = datetime.date.today().isoformat()

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")

def norm(name):
    s = unicodedata.normalize("NFKD", str(name)).encode("ascii","ignore").decode().lower()
    s = s.replace("&"," and ").replace("@"," ")
    s = re.sub(r"\bd[\s\-]?condo\b","d condo", s)
    s = re.sub(r"[^a-z0-9 ]"," ", s)
    s = re.sub(r"\s+"," ", s).strip()
    drop = {"condominium","condo","chiang","mai","chiangmai","the","at","by","for","rent","cm"}
    toks = [t for t in s.split() if t not in drop]
    return " ".join(toks).strip() or s

master = json.load(open(os.path.join(BASE,"master.json")))
by_name = {x["name"]: x for x in master}
by_norm = {norm(x["name"]): x for x in master}

# coordonnées (géocodage)
geo = {}
gc = os.path.join(DATA,"geocode_cache.json")
if os.path.exists(gc):
    try: geo = json.load(open(gc))
    except: geo = {}
for x in master:
    g = geo.get(x["name"])
    if g and g.get("lat"):
        x["lat"]=g["lat"]; x["lng"]=g["lng"]; x["geo_approx"]=bool(g.get("approx"))
    else:
        x["lat"]=None; x["lng"]=None; x["geo_approx"]=True

# applique l'enrichissement (match exact puis normalise)
for f in sorted(glob.glob(os.path.join(DATA,"enrich_*.json"))):
    try: arr = json.load(open(f))
    except Exception as e: print("skip",f,e); continue
    for e in arr:
        m = by_name.get(e.get("name")) or by_norm.get(norm(e.get("name","")))
        if not m: continue
        if m.get("google_rating") is None and e.get("google_rating") is not None:
            try:
                m["google_rating"] = round(float(e["google_rating"]),1)
                gr = e.get("google_reviews")
                m["google_reviews"] = int(gr) if gr not in (None,"") else None
            except: pass
        if not m.get("image_url") and isinstance(e.get("image_url"),str) and e["image_url"].startswith("http") and not e["image_url"].lower().endswith(".svg"):
            m["image_url"] = e["image_url"]

# garde-fou : une image réutilisée par trop d'immeubles = générique -> on retire
imgc = Counter(x["image_url"] for x in master if x.get("image_url"))
GENERIC = {u for u,c in imgc.items() if c >= 4}
for x in master:
    if x.get("image_url") in GENERIC:
        x["image_url"] = None
    # bornes note
    if x.get("google_rating") is not None and not (0 < x["google_rating"] <= 5):
        x["google_rating"]=None; x["google_reviews"]=None

# ---- suivi des NOUVEAUTÉS : first_seen persistant + flag is_new ----
# data/first_seen.json = { cle_normalisee : "YYYY-MM-DD" }.  À la 1re exécution
# (fichier absent), tous les biens existants sont datés en baseline (jamais "new").
# Aux exécutions suivantes, toute clé inconnue = nouveau bien -> daté du jour, is_new.
NEW_WINDOW_DAYS = 30
FS_PATH = os.path.join(DATA, "first_seen.json")
try: first_seen = json.load(open(FS_PATH))
except Exception: first_seen = {}
baseline_run = (len(first_seen) == 0)
_today = datetime.date.today()
def _is_recent(ds):
    try: return (_today - datetime.date.fromisoformat(ds)).days <= NEW_WINDOW_DAYS
    except Exception: return False
for x in master:
    k = norm(x["name"])
    if k in first_seen:
        fs = first_seen[k]
    else:
        fs = "1970-01-01" if baseline_run else TODAY
        first_seen[k] = fs
    x["first_seen"] = fs
    x["is_new"] = (not baseline_run) and _is_recent(fs)
# purge des clés disparues depuis longtemps (garde l'index compact)
present = {norm(x["name"]) for x in master}
first_seen = {k:v for k,v in first_seen.items() if k in present}
json.dump(first_seen, open(FS_PATH,"w"), ensure_ascii=False, indent=0)
n_new = sum(1 for x in master if x.get("is_new"))
print("nouveautes (is_new):", n_new, "| baseline_run:", baseline_run)

# tri final : note Google d'abord (desc), puis score nomade, puis avec photo
def keyf(x):
    gr = x.get("google_rating") or 0
    return (-(1 if x.get("google_rating") else 0), -gr, -x.get("nomad_score",0), 0 if x.get("image_url") else 1, x["name"].lower())
master.sort(key=keyf)

# écrit data.js
fields = ["name","zone","area","rent_min","rent_max","bedrooms","desc","nomad_score","google_rating","google_reviews","image_url","source","lat","lng","geo_approx","year_completed","developer","type","first_seen","is_new"]
def clean(x):
    d={k:(x.get(k) if x.get(k) not in ("",) else None) for k in fields}
    # loyer 0 = inconnu -> null (sinon filtré comme < budget et affiché « – 0 ฿ »)
    for rk in ("rent_min","rent_max"):
        if not d.get(rk): d[rk]=None
    return d

lines = []
lines.append("// ============================================================")
lines.append("//  VEILLE CONDOS CHIANG MAI — base de donnees locale")
lines.append("//  Genere le : " + TODAY)
lines.append("//  Budget cible : 7 000 - 30 000 THB / mois")
lines.append("//  %d biens uniques verifies (condos + maisons/villas) — portails + guides nomades." % len(master))
lines.append("//  Notes Google Maps + avis recuperees ou trouvables ; null sinon (jamais inventees).")
lines.append("// ============================================================")
lines.append("")
withr = sum(1 for x in master if x.get("google_rating") is not None)
withi = sum(1 for x in master if x.get("image_url"))
n_condo = sum(1 for x in master if x.get("type","condo") == "condo")
n_house = sum(1 for x in master if x.get("type") == "house")
lines.append("window.CONDOS_META = {")
lines.append('  lastUpdated: "%s",' % TODAY)
lines.append("  budgetMin: 3000, budgetMax: 150000, condosOnly: false,")
lines.append("  total: %d, condos: %d, houses: %d, withRating: %d, withImage: %d," % (len(master), n_condo, n_house, withr, withi))
lines.append('  source: "Portails immobiliers (DDproperty, Hipflat, FazWaz, Thailand-Property, Renthub, PerfectHomes) + guides nomades. Condos + maisons/villas. Notes = Google Maps quand disponibles."')
lines.append("};")
lines.append("")
lines.append("window.CONDOS = [")
for x in master:
    lines.append("  " + json.dumps(clean(x), ensure_ascii=False) + ",")
lines.append("];")
open(os.path.join(BASE,"data.js"),"w").write("\n".join(lines)+"\n")

zc = Counter(x["zone"] for x in master)
print("TOTAL:", len(master), "| avec note Google:", withr, "| avec image:", withi)
print("images generiques retirees:", len(GENERIC))
print("zones:", dict(zc))
