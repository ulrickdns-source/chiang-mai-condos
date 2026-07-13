#!/usr/bin/env python3
# Consolide tous les data/allcondo_*.json (condos) + enrichit avec les condos
# existants de master.json (notes Google, photos, coords, desc). -> condos_master.json
import json, glob, os, re, unicodedata
from collections import Counter, defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
ZONES = ["Nimman","Santitham","Chang Phueak","Huay Kaew","Jet Yod","Old City",
         "Suthep / CMU","Doi Suthep","Central Festival","Superhighway","Riverside","Nong Hoi","Autres"]
ZPREF = {z:i for i,z in enumerate(ZONES)}

def norm(name):
    s = unicodedata.normalize("NFKD", str(name)).encode("ascii","ignore").decode().lower()
    s = re.sub(r"\(.*?\)"," ", s)          # retire le contenu entre parenthèses
    s = s.replace("&"," and ").replace("@"," ")
    s = re.sub(r"\bd[\s\-']?condo\b","dcondo", s)
    s = re.sub(r"\bd[\s\-']?vieng\b","dvieng", s)
    s = re.sub(r"[^a-z0-9 ]"," ", s)
    s = re.sub(r"\s+"," ", s).strip()
    drop = {"condominium","condo","chiang","mai","chiangmai","the","at","by","for","rent","cm",
            "condotel","chiangmai","chiang-mai","company","limited","public","co","ltd"}
    toks = [t for t in s.split() if t not in drop]
    key = " ".join(toks).strip() or s
    ALIAS = {
        "supalai monte 1":"supalai monte viang",
        "supalai monte vaing":"supalai monte viang",
        "supalai monte ii":"supalai monte 2",
        "astra luxury suite":"astra",
    }
    return ALIAS.get(key, key)

def as_int(v):
    try:
        if v in (None,""): return None
        return int(round(float(v)))
    except: return None

def clean_zone(z):
    z=(z or "").strip()
    if z in ZPREF: return z
    zl=z.lower()
    for k in ZPREF:
        if k.lower() in zl: return k
    return "Autres"

# marques/mots = condo sûr (pour classer les entrées de la base existante)
CONDO_RE = re.compile(r"condo|condominium|palm springs|punna|hillside|escent|supalai|astra|nimmana|"
    r"twin peaks|peaks avenue|peaks garden|dcondo|d\s?condo|one plus|the next|galare|galae|"
    r"himma garden|the trio|the vidi|play cond|sky breeze|chom doi|the unique|casa condo|the prio|"
    r"karnkanok|base height|d.?vieng|rimping|the fore|ping plus|ping live|jigsaw|treasure prime|"
    r"glory cond|believe nimman|the nine|natura green|prime square|convention cond|liv.?nimman|"
    r"srithana|the star hill|the empire|the bliss|mountain front|green tower|hill park|trams|"
    r"supalai monte|serene lake|north 3|north 5|pp condominium|vieng ping|j.c. hill|jc hill|the 8|promt|the prompt", re.I)

# 1) pool = tous les allcondo_*.json
pool = {}
raw_count = 0
for f in sorted(glob.glob(os.path.join(DATA,"allcondo_*.json"))):
    try: arr=json.load(open(f))
    except Exception as e: print("skip",f,e); continue
    for x in arr:
        nm=x.get("name")
        if not nm: continue
        raw_count+=1
        k=norm(nm)
        if len(k)<2: continue
        rec = pool.get(k)
        cur = {
            "name":nm, "zone":clean_zone(x.get("zone")), "district":x.get("district") or "",
            "year_completed":as_int(x.get("year_completed")),
            "rent_min":as_int(x.get("rent_min")), "rent_max":as_int(x.get("rent_max")),
            "bedrooms":str(x.get("bedrooms") or ""), "developer":str(x.get("developer") or ""),
            "google_rating":x.get("google_rating"), "google_reviews":as_int(x.get("google_reviews")),
            "source":x.get("source") or "",
        }
        if not rec:
            pool[k]=cur; continue
        # merge
        if len(cur["name"])<len(rec["name"]) and cur["name"]: rec["name"]=cur["name"]
        if ZPREF.get(cur["zone"],99)<ZPREF.get(rec["zone"],99): rec["zone"]=cur["zone"]
        if not rec["district"] and cur["district"]: rec["district"]=cur["district"]
        if rec["year_completed"] is None and cur["year_completed"]: rec["year_completed"]=cur["year_completed"]
        if cur["rent_min"] is not None: rec["rent_min"]=min(rec["rent_min"],cur["rent_min"]) if rec["rent_min"] is not None else cur["rent_min"]
        if cur["rent_max"] is not None: rec["rent_max"]=max(rec["rent_max"] or 0,cur["rent_max"])
        if len(cur["bedrooms"])>len(rec["bedrooms"]): rec["bedrooms"]=cur["bedrooms"]
        if not rec["developer"] and cur["developer"]: rec["developer"]=cur["developer"]
        if rec["google_rating"] is None and cur["google_rating"] is not None:
            rec["google_rating"]=cur["google_rating"]; rec["google_reviews"]=cur["google_reviews"]
        if not rec["source"] and cur["source"]: rec["source"]=cur["source"]

print("Entrees brutes allcondo:",raw_count,"| uniques pool:",len(pool))

# 2) enrichissement depuis la base existante (condos uniquement)
base=[]
try: base=json.load(open(os.path.join(BASE,"master.json")))
except Exception as e: print("WARN master:",e)
base_by_norm={norm(x["name"]):x for x in base}

enriched=0; added=0
for k,rec in pool.items():
    b=base_by_norm.get(k)
    if b:
        enriched+=1
        rec["google_rating"]=rec["google_rating"] if rec["google_rating"] is not None else b.get("google_rating")
        if rec["google_rating"] is not None and rec.get("google_reviews") is None:
            rec["google_reviews"]=b.get("google_reviews")
        rec["image_url"]=b.get("image_url")
        rec["lat"]=b.get("lat"); rec["lng"]=b.get("lng"); rec["geo_approx"]=b.get("geo_approx")
        rec["desc"]=b.get("desc") or b.get("notes") or ""
        rec["nomad_score"]=as_int(b.get("nomad_score")) or 3
        rec["area"]=b.get("area") or rec["district"]
        if ZPREF.get(clean_zone(b.get("zone")),99)<ZPREF.get(rec["zone"],99): rec["zone"]=clean_zone(b.get("zone"))
    else:
        rec.setdefault("image_url",None); rec.setdefault("lat",None); rec.setdefault("lng",None)
        rec["geo_approx"]=True; rec["nomad_score"]=3
        rec["area"]=rec["district"]
        d=[]
        if rec["developer"]: d.append(rec["developer"])
        if rec["year_completed"]: d.append("livré "+str(rec["year_completed"]))
        rec["desc"]="Condominium" + (" · "+" · ".join(d) if d else "")

# 3) ajoute les condos de la base ABSENTS du pool (s'ils sont bien des condos)
for b in base:
    k=norm(b["name"])
    if k in pool: continue
    if not CONDO_RE.search(b["name"]): continue   # on ne garde que les vrais condos
    added+=1
    pool[k]={
        "name":b["name"], "zone":clean_zone(b.get("zone")), "district":b.get("area") or "",
        "year_completed":None, "rent_min":as_int(b.get("rent_min")), "rent_max":as_int(b.get("rent_max")),
        "bedrooms":b.get("bedrooms") or "", "developer":"",
        "google_rating":b.get("google_rating"), "google_reviews":as_int(b.get("google_reviews")),
        "source":(b.get("sources") or [b.get("source")])[0] if (b.get("sources") or b.get("source")) else "",
        "image_url":b.get("image_url"), "lat":b.get("lat"), "lng":b.get("lng"),
        "geo_approx":b.get("geo_approx",True), "desc":b.get("desc") or b.get("notes") or "",
        "nomad_score":as_int(b.get("nomad_score")) or 3, "area":b.get("area") or "",
    }
print("enrichis via base:",enriched,"| condos base ajoutes:",added)

out=list(pool.values())
# nettoyage bornes
for r in out:
    if r.get("rent_min") is not None and r.get("rent_max") is not None and r["rent_min"]>r["rent_max"]:
        r["rent_min"],r["rent_max"]=r["rent_max"],r["rent_min"]
    gr=r.get("google_rating")
    try: r["google_rating"]=round(float(gr),1) if gr is not None and 0<float(gr)<=5 else None
    except: r["google_rating"]=None
    if r["google_rating"] is None: r["google_reviews"]=None

# tri : note Google d'abord, puis récence, puis score
out.sort(key=lambda x:(-(1 if x.get("google_rating") else 0), -(x.get("google_rating") or 0),
                       -(x.get("year_completed") or 0), -(x.get("nomad_score") or 0), x["name"].lower()))

json.dump(out, open(os.path.join(BASE,"condos_master.json"),"w"), ensure_ascii=False, indent=1)
# remplace master.json par la version condos-only (pour geocode + generate)
json.dump(out, open(os.path.join(BASE,"master.json"),"w"), ensure_ascii=False, indent=1)

print("\n=== CONDOS-ONLY ===")
print("TOTAL condos:",len(out))
print("avec année:",sum(1 for x in out if x.get("year_completed")))
print("avec note Google:",sum(1 for x in out if x.get("google_rating") is not None))
print("avec photo:",sum(1 for x in out if x.get("image_url")))
print("avec prix:",sum(1 for x in out if x.get("rent_min") or x.get("rent_max")))
print("récents 2020+:",sum(1 for x in out if (x.get("year_completed") or 0)>=2020))
print("zones:",dict(Counter(x["zone"] for x in out)))
