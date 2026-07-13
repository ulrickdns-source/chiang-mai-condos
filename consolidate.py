#!/usr/bin/env python3
# Consolide les fichiers raw_*.json + les CONDOS existants de data.js
# en une liste maître dédoublonnée -> master.json
import json, re, glob, os, unicodedata, subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")

ZONES = ["Nimman","Santitham","Chang Phueak","Huay Kaew","Jet Yod","Old City",
         "Suthep / CMU","Doi Suthep","Central Festival","Superhighway","Riverside","Nong Hoi",
         "Hang Dong","Mae Rim","San Sai","San Kamphaeng","Autres"]
# priorité (plus petit = prioritaire) pour choisir la zone quand un immeuble a plusieurs tags
ZP = {z:i for i,z in enumerate(ZONES)}
ZP_PREF = {"Nimman":0,"Jet Yod":1,"Suthep / CMU":2,"Santitham":3,"Huay Kaew":4,
           "Chang Phueak":5,"Old City":6,"Doi Suthep":7,"Central Festival":8,
           "Superhighway":9,"Riverside":10,"Nong Hoi":11,
           "Hang Dong":12,"Mae Rim":13,"San Sai":14,"San Kamphaeng":15,"Autres":16}

def norm(name):
    s = unicodedata.normalize("NFKD", str(name)).encode("ascii","ignore").decode().lower()
    s = s.replace("&"," and ").replace("@"," ")
    s = re.sub(r"\bd[\s\-]?condo\b","d condo", s)   # dcondo -> d condo
    s = re.sub(r"[^a-z0-9 ]"," ", s)
    s = re.sub(r"\s+"," ", s).strip()
    # retire mots non distinctifs
    drop = {"condominium","condo","chiang","mai","chiangmai","the","at","by","for","rent","cm"}
    toks = [t for t in s.split() if t not in drop]
    s = " ".join(toks).strip()
    return s or unicodedata.normalize("NFKD",str(name)).encode("ascii","ignore").decode().lower().strip()

def clean_zone(z):
    z = (z or "").strip()
    if z in ZP: return z
    zl = z.lower()
    for k in ZP:
        if k.lower() in zl: return k
    if "cmu" in zl or "suthep" in zl: return "Suthep / CMU"
    if "phueak" in zl or "phuak" in zl: return "Chang Phueak"
    if "khlan" in zl or "klan" in zl or "river" in zl or "ping" in zl: return "Riverside"
    if "nimman" in zl: return "Nimman"
    if "hang dong" in zl or "hangdong" in zl or "namphrae" in zl or "nam phrae" in zl or "ban waen" in zl: return "Hang Dong"
    if "mae rim" in zl or "maerim" in zl or "rim tai" in zl or "mae sa" in zl: return "Mae Rim"
    if "san sai" in zl or "sansai" in zl or "san phi suea" in zl or "mae jo" in zl or "maejo" in zl: return "San Sai"
    if "kamphaeng" in zl or "kamphang" in zl or "bo sang" in zl or "bosang" in zl or "doi saket" in zl or "saraphi" in zl or "sarapee" in zl: return "San Kamphaeng"
    return "Autres"

def as_int(v, d=0):
    try: return int(round(float(v)))
    except: return d

records = []

# 1) existants depuis data.js
try:
    out = subprocess.check_output(["node","-e",
        "const fs=require('fs'),vm=require('vm');const c={window:{}};vm.createContext(c);"
        "vm.runInContext(fs.readFileSync('%s','utf8'),c);"
        "process.stdout.write(JSON.stringify(c.window.CONDOS||[]))" % os.path.join(BASE,"data.js")])
    for x in json.loads(out):
        records.append({
            "name":x.get("name"), "zone":clean_zone(x.get("zone")), "area":x.get("area",""),
            "rent_min":as_int(x.get("rent_min")), "rent_max":as_int(x.get("rent_max")),
            "bedrooms":str(x.get("bedrooms") or ""), "desc":str(x.get("notes") or x.get("desc") or ""),
            "nomad_score":as_int(x.get("nomad_score"),3),
            "google_rating":x.get("google_rating"), "google_reviews":x.get("google_reviews"),
            "image_url":x.get("image_url"), "source":(x.get("sources") or [None])[0] if x.get("sources") else x.get("source"),
            "type":x.get("type") or "condo",
        })
    print("existants data.js:", len(records))
except Exception as e:
    print("WARN data.js:", e)

# 2) fichiers raw (raw_*.json = condos ; rawhouse_*.json = maisons)
for f in sorted(glob.glob(os.path.join(DATA,"raw_*.json"))) + sorted(glob.glob(os.path.join(DATA,"rawhouse_*.json"))):
    is_house = os.path.basename(f).startswith("rawhouse_")
    try:
        arr = json.load(open(f))
    except Exception as e:
        print("skip", f, e); continue
    for x in arr:
        if not x.get("name"): continue
        records.append({
            "name":x.get("name"), "zone":clean_zone(x.get("zone")), "area":x.get("area",""),
            "rent_min":as_int(x.get("rent_min")), "rent_max":as_int(x.get("rent_max")),
            "bedrooms":str(x.get("bedrooms") or ""), "desc":str(x.get("desc") or ""),
            "nomad_score":as_int(x.get("nomad_score"),3),
            "google_rating":x.get("google_rating"), "google_reviews":x.get("google_reviews"),
            "image_url":x.get("image_url"), "source":x.get("source"),
            "type":(x.get("type") or ("house" if is_house else "condo")),
        })
print("total brut (avec existants):", len(records))

def good_img(u):
    return isinstance(u,str) and u.startswith("http") and not u.lower().endswith(".svg")

# 3) dedup/merge
merged = {}
for r in records:
    k = norm(r["name"])
    if len(k) < 2: continue
    if k not in merged:
        merged[k] = dict(r)
        continue
    m = merged[k]
    # zone : garde la plus prioritaire
    if ZP_PREF.get(r["zone"],99) < ZP_PREF.get(m["zone"],99):
        m["zone"] = r["zone"]
    # nom : garde le plus court "propre" (souvent le nom officiel) sauf si vide
    if r["name"] and len(r["name"]) < len(m["name"]):
        m["name"] = r["name"]
    # loyers : union
    if r["rent_min"]>0: m["rent_min"] = min(m["rent_min"] or r["rent_min"], r["rent_min"])
    m["rent_max"] = max(m["rent_max"], r["rent_max"])
    m["nomad_score"] = max(m["nomad_score"], r["nomad_score"])
    if len(r.get("desc") or "") > len(m.get("desc") or ""): m["desc"]=r["desc"]
    if len(r.get("bedrooms") or "") > len(m.get("bedrooms") or ""): m["bedrooms"]=r["bedrooms"]
    if len(str(r.get("area") or "")) > len(str(m.get("area") or "")): m["area"]=r["area"]
    if m.get("google_rating") is None and r.get("google_rating") is not None:
        m["google_rating"]=r["google_rating"]; m["google_reviews"]=r.get("google_reviews")
    if not good_img(m.get("image_url")) and good_img(r.get("image_url")):
        m["image_url"]=r["image_url"]
    if not m.get("source") and r.get("source"): m["source"]=r["source"]

out = []
for m in merged.values():
    m["type"] = m.get("type") or "condo"
    is_house = m["type"] == "house"
    # nettoyage final ; plafond loyer plus haut pour les maisons/villas (tout budget)
    m["rent_min"] = max(0, as_int(m["rent_min"]))
    m["rent_max"] = min(300000 if is_house else 60000, as_int(m["rent_max"]))
    if m["rent_min"] and m["rent_max"] and m["rent_min"]>m["rent_max"]:
        m["rent_min"], m["rent_max"] = m["rent_max"], m["rent_min"]
    # filtre budget : les CONDOS gardent la fourchette large ; les MAISONS = tout budget (aucun filtre)
    if not is_house:
        if m["rent_max"] and m["rent_max"] < 3000: continue
        if m["rent_min"] and m["rent_min"] > 60000: continue
    if not good_img(m.get("image_url")): m["image_url"]=None
    gr = m.get("google_rating")
    try: m["google_rating"]= round(float(gr),1) if gr is not None else None
    except: m["google_rating"]=None
    m["google_reviews"] = as_int(m["google_reviews"], None) if m.get("google_reviews") not in (None,"") else None
    if isinstance(m["google_reviews"],int) and m["google_reviews"]<=0: m["google_reviews"]=None
    out.append(m)

# tri : score nomade puis présence note/photo
out.sort(key=lambda x:(-x["nomad_score"], ZP_PREF.get(x["zone"],99), x["name"].lower()))

json.dump(out, open(os.path.join(BASE,"master.json"),"w"), ensure_ascii=False, indent=1)

# stats
from collections import Counter
zc = Counter(x["zone"] for x in out)
tc = Counter(x.get("type","condo") for x in out)
print("UNIQUES:", len(out))
print("types:", dict(tc))
print("avec note Google:", sum(1 for x in out if x["google_rating"] is not None))
print("avec image:", sum(1 for x in out if x["image_url"]))
print("zones:", dict(zc))
