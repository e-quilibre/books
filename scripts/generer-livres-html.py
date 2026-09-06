#!/usr/bin/env python3
"""Régénère le bloc LIVRES de ma-bibliotheque.html à partir de livres.json.

livres.json est la source de vérité unique des données d'inventaire :
toute modification s'y fait, puis ce script la reporte dans l'app.
"""
import json, re
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"

ORDRE = ["t", "r", "re", "a", "isbn", "isbnAuto", "th", "s", "c", "dbl", "q"]

d = json.load(open(SRC / "livres.json"))

def js_livre(l):
    parts = []
    for k in ORDRE:
        if k not in l:
            continue
        if k == "isbn" and not l[k]:
            continue  # "" = inconnu : on n'écrit rien dans l'app
        parts.append(f"{k}:{json.dumps(l[k], ensure_ascii=False)}")
    return "{" + ", ".join(parts) + "}"

lignes = []
etagere = None
for l in d["livres"]:
    if l["s"] != etagere:
        etagere = l["s"]
        lignes.append(f"\n/* ─── ÉTAGÈRE {etagere} ─────────────────────────────────────────────── */")
    lignes.append(js_livre(l) + ",")
bloc = "const LIVRES = [\n" + "\n".join(lignes) + "\n];"

h = open(SRC / "ma-bibliotheque.html").read()
h2, n = re.subn(r"const LIVRES = \[.*?\n\];", lambda m: bloc, h, count=1, flags=re.S)
assert n == 1, "bloc LIVRES introuvable dans le HTML"
open(SRC / "ma-bibliotheque.html", "w").write(h2)
print(f"{len(d['livres'])} livres écrits dans src/ma-bibliotheque.html")
