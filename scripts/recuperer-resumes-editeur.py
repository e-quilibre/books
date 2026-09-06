#!/usr/bin/env python3
"""Récupère les résumés éditeur (champ re) depuis Google Books, par ISBN exact.

Ne touche que les livres qui ont un ISBN et ni résumé rédigé (r) ni résumé
éditeur (re). L'ISBN étant une clé exacte, aucun risque de fausse
correspondance. Les erreurs passagères (503) sont réessayées puis passées ;
les fiches sans description sont mémorisées dans un cache local (exclu du
dépôt) pour ne pas être re-interrogées.

Après coup : python3 generer-livres-html.py pour reporter dans l'app.
"""
import json, os, time, urllib.request
from pathlib import Path

ICI = Path(__file__).resolve().parent        # scripts/ : clé et caches
SRC = ICI.parent / "src"                     # données et app

# Clé d'API : fichier cle-google-books.txt (dans .gitignore) ou variable
# d'environnement GOOGLE_BOOKS_KEY. Sans clé, le quota anonyme partagé de
# Google est presque toujours épuisé — voir docs/CONTEXTE.md.
CLE = os.environ.get("GOOGLE_BOOKS_KEY", "")
if not CLE and os.path.exists(ICI / "cle-google-books.txt"):
    CLE = open(ICI / "cle-google-books.txt").read().strip()
if not CLE:
    print("Aucune clé trouvée (cle-google-books.txt ou GOOGLE_BOOKS_KEY) — tentative sans clé, échec probable.")

CACHE = ICI / "cache-resumes-introuvables.txt"
connus_vides = set()
if os.path.exists(CACHE):
    connus_vides = set(open(CACHE).read().split())

def interroger(isbn):
    """Renvoie la description (str, peut être vide) ou None si l'API reste injoignable."""
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}&country=FR"
    if CLE:
        url += f"&key={CLE}"
    for attente in (0, 5, 15):
        if attente:
            time.sleep(attente)
        try:
            with urllib.request.urlopen(url) as r:
                rep = json.load(r)
            items = rep.get("items") or []
            return items[0].get("volumeInfo", {}).get("description", "") if items else ""
        except urllib.error.HTTPError as e:
            if e.code in (500, 502, 503, 504):
                continue  # passager : on réessaie
            print(f"ARRÊT — l'API a refusé (HTTP {e.code}). Rien de perdu : relancer plus tard.")
            raise SystemExit(1)
        except Exception:
            continue
    return None

d = json.load(open(SRC / "livres.json"))
faits = sans = erreurs = 0
for l in d["livres"]:
    if not l.get("isbn") or l.get("r") or l.get("re") or l["isbn"] in connus_vides:
        continue
    desc = interroger(l["isbn"])
    if desc is None:
        erreurs += 1
        print("(injoignable, passé)", l["t"][:60])
    elif desc:
        l["re"] = desc[:500]
        faits += 1
        print("re ←", l["t"][:60])
    else:
        sans += 1
        connus_vides.add(l["isbn"])
        print("(pas de description)", l["t"][:60])
    time.sleep(0.7)

open(SRC / "livres.json", "w").write(json.dumps(d, indent=1, ensure_ascii=False) + "\n")
open(CACHE, "w").write("\n".join(sorted(connus_vides)) + "\n")
print(f"{faits} résumés éditeur ajoutés · {sans} fiches sans description (mémorisées) · {erreurs} injoignables.")
