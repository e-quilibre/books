#!/usr/bin/env python3
"""Cherche les ISBN manquants sur Google Books, par titre + auteur (recherche floue).

Une recherche floue peut renvoyer un autre livre ou une autre édition :
ce script n'écrit donc JAMAIS directement dans livres.json. Il produit
propositions-isbn.json (exclu du dépôt), où chaque proposition porte un
verdict — « concordant » si le titre et l'auteur trouvés recoupent les
nôtres, « douteux » sinon — et un booléen `retenir`, prérempli en
conséquence, à relire et corriger à la main.

  python3 chercher-isbn.py              # cherche et écrit les propositions
  python3 chercher-isbn.py --appliquer  # reporte les propositions retenues
                                        # dans livres.json (marquées isbnAuto)

Après application : python3 generer-livres-html.py pour reporter dans l'app.
"""
import json, os, re, sys, time, unicodedata, urllib.parse, urllib.request

from pathlib import Path

ICI = Path(__file__).resolve().parent        # scripts/ : clé et propositions
SRC = ICI.parent / "src"                     # données et app

PROPOSITIONS = ICI / "propositions-isbn.json"

CLE = os.environ.get("GOOGLE_BOOKS_KEY", "")
if not CLE and os.path.exists(ICI / "cle-google-books.txt"):
    CLE = open(ICI / "cle-google-books.txt").read().strip()


def norm(s):
    s = unicodedata.normalize("NFD", (s or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()


def noms_famille(auteurs):
    """Derniers mots de chaque auteur « Prénom Nom », normalisés."""
    noms = []
    for a in re.split(r"[,&]| et ", auteurs or ""):
        mots = norm(a).split()
        if mots:
            noms.append(mots[-1])
    return noms


def interroger(url):
    for attente in (0, 5, 15):
        if attente:
            time.sleep(attente)
        try:
            with urllib.request.urlopen(url) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (500, 502, 503, 504):
                continue
            print(f"ARRÊT — l'API a refusé (HTTP {e.code}).")
            raise SystemExit(1)
        except Exception:
            continue
    return None


def chercher():
    d = json.load(open(SRC / "livres.json"))
    props, sans, injoignables = [], 0, 0
    a_faire = [l for l in d["livres"] if not l.get("isbn")]
    print(f"{len(a_faire)} livres sans ISBN à chercher.\n")
    for n, l in enumerate(a_faire, 1):
        titre_court = re.split(r"[(:]", l["t"])[0].strip()
        q = f'intitle:"{titre_court}" inauthor:"{noms_famille(l["a"])[0] if noms_famille(l["a"]) else ""}"'
        url = ("https://www.googleapis.com/books/v1/volumes?q=" + urllib.parse.quote(q)
               + "&maxResults=3&country=FR" + (f"&key={CLE}" if CLE else ""))
        rep = interroger(url)
        if rep is None:
            injoignables += 1
            print(f"[{n}/{len(a_faire)}] (injoignable, passé) {l['t'][:50]}")
            continue
        meilleur = None
        for item in rep.get("items") or []:
            v = item.get("volumeInfo", {})
            ids = v.get("industryIdentifiers") or []
            isbn = next((i["identifier"] for i in ids if i["type"] == "ISBN_13"), "")
            if not isbn:
                continue
            t_trouve = v.get("title", "") + " " + v.get("subtitle", "")
            titre_ok = norm(titre_court) in norm(t_trouve) or norm(t_trouve).startswith(norm(titre_court))
            auteur_ok = any(nf in norm(" ".join(v.get("authors") or [])) for nf in noms_famille(l["a"]))
            candidat = {
                "titre": v.get("title", "") + (" : " + v["subtitle"] if v.get("subtitle") else ""),
                "auteurs": ", ".join(v.get("authors") or []),
                "date": (v.get("publishedDate") or "")[:4],
                "isbn": isbn,
                "concorde": titre_ok and auteur_ok,
            }
            if candidat["concorde"]:
                meilleur = candidat
                break
            meilleur = meilleur or candidat
        if not meilleur:
            sans += 1
            print(f"[{n}/{len(a_faire)}] (aucune fiche avec ISBN) {l['t'][:50]}")
        else:
            verdict = "concordant" if meilleur.pop("concorde") else "douteux"
            props.append({"t": l["t"], "a": l["a"], "verdict": verdict,
                          "retenir": verdict == "concordant", "trouve": meilleur})
            print(f"[{n}/{len(a_faire)}] {verdict:10} {l['t'][:40]:42} → {meilleur['titre'][:40]} ({meilleur['auteurs'][:25]})")
        time.sleep(0.7)
    json.dump(props, open(PROPOSITIONS, "w"), indent=1, ensure_ascii=False)
    nc = sum(1 for p in props if p["verdict"] == "concordant")
    print(f"\n{nc} concordants · {len(props)-nc} douteux · {sans} sans fiche · {injoignables} injoignables")
    print(f"Relire {PROPOSITIONS} (champ `retenir`), puis : python3 chercher-isbn.py --appliquer")


def appliquer():
    props = json.load(open(PROPOSITIONS))
    d = json.load(open(SRC / "livres.json"))
    par_cle = {(l["t"], l["a"]): l for l in d["livres"]}
    faits = 0
    for p in props:
        if not p.get("retenir"):
            continue
        l = par_cle.get((p["t"], p["a"]))
        if l is None or l.get("isbn"):
            continue
        l["isbn"] = p["trouve"]["isbn"]
        l["isbnAuto"] = 1  # provenance : fiche concordante, pas relevé sur le livre
        faits += 1
    open(SRC / "livres.json", "w").write(json.dumps(d, indent=1, ensure_ascii=False) + "\n")
    print(f"{faits} ISBN appliqués (marqués isbnAuto). Puis : python3 generer-livres-html.py")


if __name__ == "__main__":
    appliquer() if "--appliquer" in sys.argv else chercher()
