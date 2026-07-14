#!/usr/bin/env python3
# Fusionne master.json + enrich_*.json -> data.js (window.CONDOS)
import json, glob, os, re, unicodedata, datetime, base64
from collections import Counter

def upscale_photo(u):
    """thailand-property : monte les vignettes 490px à 780px (taille max servie par le CDN)."""
    if not isinstance(u,str) or "img.thailand-property.com/" not in u: return u
    try:
        b64=u.rsplit("/",1)[1]
        d=json.loads(base64.b64decode(b64+"="*(-len(b64)%4)))
        rz=d.get("edits",{}).get("resize",{})
        w=rz.get("width")
        if w and w<780:
            rz["width"]=780; rz["height"]=520; rz["fit"]="cover"  # variante exacte servie par le CDN
            nb=base64.b64encode(json.dumps(d,separators=(",",":")).encode()).decode().rstrip("=")
            return "https://img.thailand-property.com/"+nb
    except Exception: return u
    return u

def is_ugly(u):
    """bandeaux d'agence perfecthomes (overlay texte) = moches -> à écarter si mieux dispo."""
    return isinstance(u,str) and "perfecthomes.co.th" in u and re.search(r"banner", u, re.I) is not None

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

# fallback année/promoteur depuis condos_master.json (lecture seule ; ne touche pas master.json)
try:
    cm = json.load(open(os.path.join(BASE,"condos_master.json")))
    cm_by = {norm(x["name"]): x for x in cm}
    for x in master:
        src = cm_by.get(norm(x["name"]))
        if not src: continue
        if not x.get("year_completed") and src.get("year_completed"): x["year_completed"]=src["year_completed"]
        if not x.get("developer") and src.get("developer"): x["developer"]=src["developer"]
except Exception as e:
    print("WARN condos_master:", e)

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
    if "hqfix" in os.path.basename(f): continue   # traité séparément (remplacement)
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
        # galerie de photos
        if isinstance(e.get("photos"),list):
            good=[u for u in e["photos"] if isinstance(u,str) and u.startswith("http") and not u.lower().endswith(".svg")]
            if good:
                m["photos"] = list(dict.fromkeys((m.get("photos") or []) + good))
        # liens facebook / site officiel
        if not m.get("facebook") and isinstance(e.get("facebook"),str) and e["facebook"].startswith("http"):
            m["facebook"] = e["facebook"]
        if not m.get("website") and isinstance(e.get("website"),str) and e["website"].startswith("http"):
            m["website"] = e["website"]

# ---- remplacement de photos moches (data/enrich_hqfix_*.json) : remplace la galerie ----
for f in sorted(glob.glob(os.path.join(DATA,"enrich_hqfix_*.json"))):
    try: arr = json.load(open(f))
    except Exception as e: print("skip",f,e); continue
    for e in arr:
        m = by_name.get(e.get("name")) or by_norm.get(norm(e.get("name","")))
        if not m: continue
        good=[u for u in (e.get("photos") or []) if isinstance(u,str) and u.startswith("http") and not u.lower().endswith(".svg")]
        if good:
            m["photos"]=good           # remplace par la galerie propre
            m["image_url"]=good[0]      # nouvelle vignette

# ---- correction de prix double-source (data/pricefix_*.json) : override rent + note ----
for f in sorted(glob.glob(os.path.join(DATA,"pricefix_*.json"))):
    try: arr = json.load(open(f))
    except Exception as e: print("skip",f,e); continue
    for e in arr:
        m = by_name.get(e.get("name")) or by_norm.get(norm(e.get("name","")))
        if not m: continue
        applied=False
        try:
            if e.get("rent_min") is not None: m["rent_min"]=int(e["rent_min"]); applied=True
            if e.get("rent_max") is not None: m["rent_max"]=int(e["rent_max"]); applied=True
        except: pass
        if e.get("price_note"): m["price_note"]=e["price_note"]
        if applied: m["price_verified"]=True

# garde-fou : une image réutilisée par trop d'immeubles = générique -> on retire
imgc = Counter(x["image_url"] for x in master if x.get("image_url"))
GENERIC = {u for u,c in imgc.items() if c >= 4}
for x in master:
    if x.get("image_url") in GENERIC:
        x["image_url"] = None
    # galerie unifiée : image principale en tête, sans génériques, dédupliquée
    photos = x.get("photos") or []
    if x.get("image_url") and x["image_url"] not in photos:
        photos = [x["image_url"]] + photos
    photos = [upscale_photo(p) for p in dict.fromkeys(photos) if p not in GENERIC]
    # écarte les bandeaux d'agence si de vraies photos existent à côté
    clean = [p for p in photos if not is_ugly(p)]
    photos = clean if clean else photos
    x["photos"] = photos[:8]
    x["image_url"] = upscale_photo(x["image_url"]) if x.get("image_url") else (photos[0] if photos else None)
    if x.get("image_url") and x["image_url"] not in x["photos"] and x["photos"]:
        x["image_url"] = x["photos"][0]
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
fields = ["name","zone","area","rent_min","rent_max","price_note","price_verified","bedrooms","desc","nomad_score","google_rating","google_reviews","image_url","photos","facebook","website","source","lat","lng","geo_approx","year_completed","developer","type","first_seen","is_new"]
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
