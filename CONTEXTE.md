# Bibliothèque personnelle — contexte du projet

## Ce que c'est

Un inventaire de ma bibliothèque professionnelle (management, produit, design,
lean, organisations), et un outil pour la consulter. Trois usages, dans cet ordre
d'importance :

1. **Ne pas racheter un livre que j'ai déjà**, typiquement debout en librairie.
2. **Trouver quel livre consulter** quand je me pose une question précise.
3. **Naviguer** dans les thématiques et retrouver ce que contient un livre.

## État au 6 septembre 2026

- 168 livres inventoriés sur 4 étagères
- 274 questions rédigées (« à consulter quand tu te demandes… »)
- 143 résumés rédigés — 25 livres sans résumé, en attente des résumés
  éditeur (`recuperer-resumes-editeur.py`, tributaire du quota Google Books)
- **0 titre non vérifié** : les 27 titres douteux ont tous été confirmés
  livre en main le 5 septembre 2026, avec leurs titres complets d'éditeur
- 30 ISBN renseignés (saisis livre en main, clés de contrôle validées)
- **7 livres personnels retirés de l'inventaire public** le 6 septembre
  (étagère 3 : développement personnel et spiritualité). Ils restent sur
  l'étagère physique : pour eux, le verdict anti-doublon dira à tort
  « Rien à ce titre » — limite acceptée, le dépôt étant public.

## L'outil

`ma-bibliotheque.html` — un fichier unique, sans dépendance réseau au chargement,
ouvrable depuis un téléphone. Il contient les données en dur et l'interface.

Fonctions :
- recherche insensible aux accents et à la casse, sur titre, auteur et questions
- verdict anti-doublon (« Tu l'as déjà » + étagère) dès 3 caractères
- bande de tranches colorées par thème, cliquable pour filtrer
- onglet Questions : les 280 questions triées, chacune menant à son livre
- onglet À vérifier : vide depuis la vérification complète ; accueillera
  d'éventuels futurs ajouts douteux (`c` à 0)
- enrichissement en lot depuis Google Books (ISBN, couverture, résumé éditeur)
- notes personnelles, corrections de titre/auteur, export et import JSON

`livres.json` — **la source de vérité unique des données d'inventaire.**
Toute modification s'y fait (à la main ou par script), puis
`generer-livres-html.py` la reporte dans le bloc `LIVRES` du HTML — ne
jamais éditer ce bloc directement. `recuperer-resumes-editeur.py` remplit
le champ `re` depuis Google Books par ISBN exact, quand le quota le permet.

Depuis septembre 2026, l'outil est aussi une PWA installable sur l'écran
d'accueil (cible : iPhone). Fichiers associés :

- `manifest.webmanifest` — nom, icônes, affichage plein écran
- `sw.js` — service worker : le HTML passe d'abord par le réseau (les mises à
  jour arrivent seules), le cache prend le relais hors ligne ; les appels
  Google Books ne sont pas interceptés
- `icone-180.png`, `icone-192.png`, `icone-512.png` — générées par script
  (tranches de livres aux couleurs des thèmes)

Le fichier HTML reste ouvrable tel quel en local : le service worker ne
s'enregistre qu'en HTTP(S).

## Modèle de données

Un livre :

| champ | sens |
|---|---|
| `t` | titre |
| `a` | auteur |
| `isbn` | ISBN-13, chaîne de chiffres seuls ; `""` = inconnu |
| `th` | identifiant de thème (voir `themes`) |
| `s` | numéro d'étagère (1 à 4) |
| `c` | 1 = titre et auteur fiables, 0 = à vérifier |
| `q` | questions auxquelles le livre répond |
| `r` | résumé rédigé (affiché en noir) |
| `re` | résumé éditeur récupéré par ISBN (affiché en gris, absent si `r`) |
| `dbl` | mention de doublon, le cas échéant |

Les données personnelles (notes, ISBN, couvertures, corrections) vivent dans le
navigateur, séparément, indexées sur le couple titre + auteur d'origine. Corriger
un titre ne fait donc pas perdre la note associée.

## Le circuit des ISBN

Les ISBN se remplissent depuis l'outil (saisie à la main livre en main, ou
« Retrouver la fiche ») et vivent dans le localStorage du téléphone. Pour les
faire entrer dans les données d'inventaire : « Exporter mes notes » produit
`biblio-notes.json`, à déposer dans le dossier du projet — il est dans le
`.gitignore` et sert de fichier d'échange. La fusion des ISBN dans
`livres.json` et le HTML se fera à partir de ce fichier (script à écrire au
premier export).

Schéma dans `livres.json` : un champ `isbn` par livre — chaîne, ISBN-13
chiffres seuls. Le champ est présent partout avec `""` pour « inconnu »
(emplacement à remplir directement dans le fichier, livre en main — les
livres y suivent l'ordre des étagères) ; `""` est traité comme absent par
l'app et les scripts. Deux canaux de saisie, à réconcilier par le script de
fusion : le fichier JSON édité sur l'ordinateur, et l'app sur le téléphone
(export `biblio-notes.json`). L'app lit déjà `l.isbn` en repli de `p.isbn`
(vignettes, carte, enrichissement) : les ISBN du JSON seront actifs dès la
régénération du bloc `LIVRES`.

Règle de provenance : **seuls les ISBN relevés livre en main entrent dans
`livres.json`.** Ceux trouvés par l'enrichissement en lot (recherche floue
titre+auteur) sont marqués `isbnAuto` dans le localStorage et signalés dans
la carte ; ils suffisent pour afficher une couverture mais restent hors de
l'inventaire tant qu'ils ne sont pas confirmés — le risque étant l'autre
édition, voire l'autre livre. Le script de fusion validera la clé de
contrôle de chaque ISBN, normalisera en ISBN-13, signalera les doublons
d'ISBN, écartera les `isbnAuto`, puis **régénérera le bloc `LIVRES` du HTML
depuis `livres.json`**, qui devient la source de vérité unique (fin de la
double saisie des données).

Sources de fiches, dans l'ordre :

1. **Google Books** — fiches les plus complètes sur le fonds francophone
   professionnel, mais quota journalier anonyme par IP (~1000 requêtes,
   remis à zéro vers 9h heure française). Sert aussi à l'enrichissement en lot.
2. **Open Library** — sans clé ni quota strict, CORS ouvert, mais fiches
   parfois incomplètes (auteur manquant) et fonds FR pro mal couvert. Utilisée
   uniquement en correspondance exacte par ISBN (repli de « Retrouver la
   fiche », et couvertures à l'affichage) : sa recherche par titre a été
   testée et disqualifiée — 1 résultat pertinent sur 3, des faux positifs.
3. **BnF (SRU)** — piste non exploitée : excellente couverture FR, mais XML
   MARC à parser ; candidate pour un futur script côté ordinateur, pas pour
   le navigateur.

## Décisions prises, et pourquoi

**Les ISBN ne sont pas écrits en dur.** Ils ne peuvent pas être connus de mémoire
sans risque d'invention, et un ISBN faux est pire qu'un champ vide : il pointe
vers un autre livre. Ils sont récupérés depuis Google Books, dans le navigateur.

**Les résumés sont rédigés, pas repris des éditeurs.** Un argumentaire commercial
ne dit pas si le livre est daté, redondant ou excellent. Les résumés récupérés
automatiquement sont affichés en gris pour les distinguer.

**Le thème « management » a été scindé.** Une catégorie de plus de dix titres ne
discrimine plus rien. D'où : manager au quotidien, leadership, culture et
collaboration, recrutement, organisations. 17 thèmes au total.

**Le Lean a sa propre catégorie** — une dizaine de titres, trop pour être fondu
dans « organisations ».

**Pas de localStorage comme unique filet.** Un bouton d'export JSON existe, parce
qu'un navigateur peut vider son stockage sans prévenir.

**Distribution en PWA plutôt que store ou fichier local.** Sur iPhone, un
fichier HTML local n'a pas de stockage persistant (Safari n'ouvre pas de
fichier arbitraire, l'aperçu Fichiers ne garde rien). La PWA exige un
hébergement HTTPS, mais seulement comme canal de distribution : une fois
installée, elle tourne en local et survit à la disparition de l'hébergeur.
L'hébergeur est interchangeable ; le vrai attachement est le **domaine** —
le localStorage y est lié, changer de domaine impose un export/import des
notes.

## Limites connues, à ne pas oublier

- **L'inventaire n'est pas garanti complet.** Il vient de la lecture de photos de
  tranches. Un livre absent de la liste ne prouve pas qu'il n'est pas sur
  l'étagère. C'est la faiblesse principale pour l'usage anti-doublon, et seul un
  scan des codes-barres la lèverait.
- **25 livres n'ont pas de résumé rédigé** — surtout les anciens titres
  douteux, fraîchement vérifiés. Trois résumés (Ury, Encyclopédie visuelle,
  Hamant) ont été rédigés d'après une connaissance générale de ces livres,
  comme les 147 d'origine : à relire.
- **Les questions sont écrites d'après une connaissance générale de ces livres,
  pas d'après ma lecture.** Elles sont un point de départ à réécrire.
- **Les couvertures sont des URL**, pas des images stockées : elles ne
  s'affichent qu'avec une connexion.
- **La PWA n'est pas encore hébergée ni testée sur iPhone.** Les fichiers sont
  prêts, mais l'installation réelle (Safari → Partager → Sur l'écran
  d'accueil) reste à valider une fois l'outil publié en HTTPS.
- **L'outil n'est plus strictement monofichier** : le service worker doit être
  un fichier séparé (contrainte de la spec). Publier = déposer les 6 fichiers
  au même endroit.

## Vérification des 27 titres douteux — terminée

Les 27 titres lus sur photos ont tous été confirmés livre en main le
5 septembre 2026 (titres complets, auteurs, ISBN). Corrections notables par
rapport aux déductions initiales : Marcel Verta → Venturino · Yves Chapiaou
→ Chapleau (Intelligence collective) et → Bernard Cohen-Hadad (L'avenir
appartient aux PME) · Sandrine Bardaux → Bordes · « Kaess » → Anna Glaser
et Véronique Steyer · « Comment négocier avec soi-même » → « Être en accord
avec soi-même » (Ury) · Leading Product est bien de François de Bodinat,
qui signe aussi Réussir l'entretien professionnel.

## Pistes suivantes

- Scanner les codes-barres pour fiabiliser l'inventaire et détecter les manquants
- Réécrire les questions livre par livre, après relecture
- Suivi des prêts (qui a quoi depuis quand)
- Marquer les livres lus, en cours, non lus
