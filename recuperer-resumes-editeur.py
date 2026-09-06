#!/usr/bin/env python3
"""Récupère les résumés éditeur (champ re) depuis Google Books, par ISBN exact.

Ne touche que les livres qui ont un ISBN et ni résumé rédigé (r) ni résumé
éditeur (re). L'ISBN étant une clé exacte, aucun risque de fausse
correspondance. S'arrête proprement si l'API refuse (quota journalier
anonyme, remis à zéro vers 9h heure française).

Après coup : python3 generer-livres-html.py pour reporter dans l'app.
"""
import json, os, time, urllib.request

# Clé d'API : fichier cle-google-books.txt (dans .gitignore) ou variable
# d'environnement GOOGLE_BOOKS_KEY. Sans clé, le quota anonyme partagé de
# Google est presque toujours épuisé — voir CONTEXTE.md.
CLE = os.environ.get("GOOGLE_BOOKS_KEY", "")
if not CLE and os.path.exists("cle-google-books.txt"):
    CLE = open("cle-google-books.txt").read().strip()
if not CLE:
    print("Aucune clé trouvée (cle-google-books.txt ou GOOGLE_BOOKS_KEY) — tentative sans clé, échec probable.")

d = json.load(open("livres.json"))
faits = sans = 0
for l in d["livres"]:
    if not l.get("isbn") or l.get("r") or l.get("re"):
        continue
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{l['isbn']}&country=FR"
    if CLE:
        url += f"&key={CLE}"
    try:
        with urllib.request.urlopen(url) as r:
            rep = json.load(r)
    except Exception as e:
        print(f"ARRÊT — l'API a refusé ({e}). Rien de perdu : relancer plus tard.")
        break
    items = rep.get("items") or []
    desc = items[0].get("volumeInfo", {}).get("description", "") if items else ""
    if desc:
        l["re"] = desc[:500]
        faits += 1
        print("re ←", l["t"][:60])
    else:
        sans += 1
        print("(pas de description)", l["t"][:60])
    time.sleep(0.7)

open("livres.json", "w").write(json.dumps(d, indent=1, ensure_ascii=False) + "\n")
print(f"{faits} résumés éditeur ajoutés, {sans} fiches sans description.")
