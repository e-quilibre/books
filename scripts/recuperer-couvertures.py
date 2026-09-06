#!/usr/bin/env python3
"""Télécharge les couvertures des livres dans couvertures/<isbn>.jpg.

Pour chaque livre avec ISBN et sans image locale : l'URL de vignette de la
fiche Google Books (par ISBN exact, avec la clé), sinon Open Library. Les
ISBN sans couverture nulle part sont mémorisés dans un cache local (exclu
du dépôt) pour ne pas être retentés à chaque passe.

Les images vivent dans le dépôt : c'est ce qui rend l'affichage possible
hors ligne, via le cache du service worker.
"""
import json, os, time, urllib.request
from pathlib import Path

ICI = Path(__file__).resolve().parent        # scripts/ : clé et caches
SRC = ICI.parent / "src"                     # données et app
COUV = SRC / "images" / "couvertures"

CLE = os.environ.get("GOOGLE_BOOKS_KEY", "")
if not CLE and os.path.exists(ICI / "cle-google-books.txt"):
    CLE = open(ICI / "cle-google-books.txt").read().strip()

CACHE = ICI / "cache-couvertures-introuvables.txt"
connus = set(open(CACHE).read().split()) if os.path.exists(CACHE) else set()
os.makedirs(COUV, exist_ok=True)


def requete(url):
    req = urllib.request.Request(url, headers={"User-Agent": "bibliotheque-perso"})
    for attente in (0, 5, 15):
        if attente:
            time.sleep(attente)
        try:
            with urllib.request.urlopen(req) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (500, 502, 503, 504):
                continue
            return None
        except Exception:
            continue
    return None


def url_vignette_google(isbn):
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}&country=FR"
    if CLE:
        url += f"&key={CLE}"
    data = requete(url)
    if not data:
        return ""
    items = json.loads(data).get("items") or []
    liens = items[0].get("volumeInfo", {}).get("imageLinks", {}) if items else {}
    u = liens.get("thumbnail") or liens.get("smallThumbnail") or ""
    return u.replace("http://", "https://").replace("&edge=curl", "")


def enregistrer(url, chemin):
    data = requete(url)
    if not data or len(data) < 2000:  # pixel vide ou page d'erreur
        return False
    open(chemin, "wb").write(data)
    return True


d = json.load(open(SRC / "livres.json"))
faits = sans = deja = 0
for l in d["livres"]:
    isbn = l.get("isbn", "")
    if not isbn:
        continue
    chemin = COUV / f"{isbn}.jpg"
    if os.path.exists(chemin):
        deja += 1
        continue
    if isbn in connus:
        sans += 1
        continue
    ok = False
    u = url_vignette_google(isbn)
    if u:
        ok = enregistrer(u, chemin)
    if not ok:
        ok = enregistrer(f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg?default=false", chemin)
    if ok:
        faits += 1
        print("✓", l["t"][:60])
    else:
        connus.add(isbn)
        sans += 1
        print("(pas de couverture)", l["t"][:60])
    time.sleep(0.6)

open(CACHE, "w").write("\n".join(sorted(connus)) + "\n")
print(f"\n{faits} couvertures téléchargées · {deja} déjà présentes · {sans} introuvables")
