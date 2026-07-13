#!/usr/bin/env python3
# Géocodage HORS-LIGNE des condos par sous-quartier (clusters reconnaissables)
# -> data/geocode_cache.json {name:{lat,lng,approx,via}}.  Rapide, sans réseau.
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
CACHE = os.path.join(DATA, "geocode_cache.json")

# ancres de sous-quartiers (lat, lng)
A = {
 "maya":(18.8021,98.9676), "nimman_n":(18.8000,98.9690), "nimman_s":(18.7940,98.9665),
 "nimman":(18.7965,98.9672), "santitham":(18.8045,98.9786), "changphueak":(18.8030,98.9832),
 "jetyod":(18.8130,98.9735), "huaykaew":(18.8045,98.9605), "ksk":(18.7950,98.9792),
 "suandok":(18.7912,98.9612), "cmu":(18.8030,98.9532), "suthep_s":(18.7800,98.9460),
 "doisuthep":(18.8080,98.9300), "central":(18.8078,99.0160), "superhwy":(18.8060,99.0040),
 "nightbazaar":(18.7860,98.9990), "watket":(18.7930,99.0015), "nonghoi":(18.7690,99.0035),
 "maehia":(18.7560,98.9430), "oldcity":(18.7880,98.9870),
 # ceintures de maisons/villas (banlieues)
 "hangdong":(18.6900,98.9210), "namphrae":(18.7250,98.9250), "banwaen":(18.6650,98.9000),
 "maerim":(18.9160,98.9370), "maesa":(18.9050,98.8850), "rimtai":(18.9250,98.9450),
 "sansai":(18.8600,99.0400), "maejo":(18.8930,99.0140), "sanphisuea":(18.8300,99.0200),
 "sankamphaeng":(18.7450,99.1180), "bosang":(18.7570,99.0680), "doisaket":(18.9160,99.1360),
 "saraphi":(18.6870,99.0360), "canalroad":(18.7700,99.0450),
}
# centres de zone (fallback)
ZC = {
 "Nimman":A["nimman"], "Santitham":A["santitham"], "Chang Phueak":A["changphueak"],
 "Huay Kaew":A["huaykaew"], "Jet Yod":A["jetyod"], "Old City":A["oldcity"],
 "Suthep / CMU":A["cmu"], "Doi Suthep":A["doisuthep"], "Central Festival":A["central"],
 "Superhighway":A["superhwy"], "Riverside":A["watket"], "Nong Hoi":A["nonghoi"],
 "Hang Dong":A["hangdong"], "Mae Rim":A["maerim"], "San Sai":A["sansai"], "San Kamphaeng":A["sankamphaeng"],
 "Autres":(18.7800,98.9700),
}
# règles mots-clés -> ancre (ordre = priorité)
RULES = [
 (("one nimman","maya","huay kaew soi","nimman soi 6","nimman soi 8"), "maya"),
 (("soi 11","soi 13","soi 15","soi 17","soi 12","soi 14","soi 16"), "nimman_n"),
 (("nimman soi 1","nimman soi 3","nimman soi 5","nimman soi 7","nimman soi 9","soi 2"), "nimman_s"),
 (("kad suan kaew","suan kaew"), "ksk"),
 (("suan dok","suandok"), "suandok"),
 (("cmu","chiang mai university"," university","campus","kiang mor","kiangmor"), "cmu"),
 (("umong","wat u","mae hia","maehia","convention"), "maehia"),
 (("doi suthep","mountain view","national park","mountain front"), "doisuthep"),
 (("central festival","cpn","escent"), "central"),
 (("fa ham","faham","superhighway","super highway","ping condo","dcondo ping","d condo ping","dcondo sign","d condo sign","dcondo rin"), "superhwy"),
 (("night bazaar","chang khlan","chang klan","changklan","loi kroh","astra","twin peaks","galare"), "nightbazaar"),
 (("wat ket","watket","riverside","river"), "watket"),
 (("nong hoi","nonghoi","mahidol"), "nonghoi"),
 (("jed yod","jet yod","jedyod","jetyod"), "jetyod"),
 (("santitham","wat suntidham","suntidham"), "santitham"),
 (("chotana","chang phueak","changphueak","changphuak","nakornping"), "changphueak"),
 (("old city","sriphum","si phum","koomuang","kampangdin","moat","tha phae"), "oldcity"),
 (("huay kaew","huaykaew","hillside"), "huaykaew"),
 (("suthep",), "suthep_s"),
 # banlieues maisons/villas
 (("nam phrae","namphrae"), "namphrae"),
 (("ban waen","banwaen"), "banwaen"),
 (("hang dong","hangdong"), "hangdong"),
 (("mae sa","maesa"), "maesa"),
 (("rim tai","rimtai","rim nuea"), "rimtai"),
 (("mae rim","maerim","huay tueng thao"), "maerim"),
 (("mae jo","maejo"), "maejo"),
 (("san phi suea","sanphisuea"), "sanphisuea"),
 (("san sai","sansai","nong chom"), "sansai"),
 (("bo sang","bosang"), "bosang"),
 (("doi saket","doisaket"), "doisaket"),
 (("saraphi","sarapee"), "saraphi"),
 (("canal road","choeng doi"), "canalroad"),
 (("san kamphaeng","sankamphaeng","kamphaeng"), "sankamphaeng"),
 (("nimman","nimmana","punna","palm springs"), "nimman"),
]

def jit(name, amp):
    h=0
    for c in name: h=(h*131+ord(c))&0xffffffff
    dx=((h&0xffff)/0xffff-0.5)*2*amp
    dy=(((h>>16)&0xffff)/0xffff-0.5)*2*amp
    return dy,dx

master = json.load(open(os.path.join(BASE,"master.json")))
cache={}
for c in master:
    nm=c["name"]; zone=c.get("zone","Autres")
    hay=(nm+" "+str(c.get("area",""))).lower()
    anchor=None; via="zone"
    for kws,a in RULES:
        if any(k in hay for k in kws):
            anchor=A[a]; via="kw:"+a; break
    if anchor is None:
        anchor=ZC.get(zone, ZC["Autres"]); via="zone:"+zone
    dy,dx=jit(nm,0.0034)  # ~350 m de dispersion
    cache[nm]={"lat":round(anchor[0]+dy,6),"lng":round(anchor[1]+dx,6),"approx":True,"via":via}

json.dump(cache, open(CACHE,"w"), ensure_ascii=False, indent=0)
from collections import Counter
viak=Counter(v["via"].split(":")[0] for v in cache.values())
print("géocodés:",len(cache),"| par méthode:",dict(viak))
