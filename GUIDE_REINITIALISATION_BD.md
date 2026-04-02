# Guide de réinitialisation de la base de données
### DFC Manager — Procédure complète de remise à zéro

---

## Quand utiliser ce guide ?

- La base de données `db.sqlite3` a été supprimée ou corrompue
- Tu veux repartir d'une base propre
- Tu déploies l'application sur un nouveau poste ou serveur

---

## Fichiers indispensables à conserver

Avant toute chose, vérifie que tu as bien ces fichiers. **Sans eux, la réinitialisation est impossible.**

```
__APP_DJANGO_v2\
├── fixtures\
│   ├── roles.json                          ← Rôles utilisateurs
│   ├── sous_directions.json                ← SDCC et SDPCC de base
│   ├── sections.json                       ← Sections de base
│   ├── type_documents.json                 ← Types de documents
│   ├── comptes_comptables.json             ← Plan comptable
│   └── regles_alerte_bg.json              ← Règles d'alerte Balance Générale
├── import_collaborateurs.py               ← Script import collaborateurs
├── import_activites.py                    ← Script import activités
├── Liste_collaborateurs_DFC_*.xlsx        ← Fichier source collaborateurs
├── Classeur4.xlsx                         ← Fichier source activités
├── manage.py                              ← ⚠️ Ne pas écraser
├── init_projet.py                         ← ⚠️ Ne pas écraser
└── run_server.py                          ← ⚠️ Ne pas écraser
```

---

## Procédure manuelle étape par étape

### Étape 1 — Ouvrir un terminal dans le dossier de l'application

```bat
cd C:\Users\arthur.gue\OneDrive - GS2E\Documents\DOC ARTHUR\DOC CIE\__APP_DJANGO_v2
```

---

### Étape 2 — Supprimer l'ancienne base de données

```bat
del db.sqlite3
```

> Si le fichier n'existe pas, ce n'est pas grave — continuer.

---

### Étape 3 — Recréer toutes les tables

```bat
python manage.py migrate
```

> Tu dois voir une liste de migrations s'afficher avec `OK` à côté de chacune.

---

### Étape 4 — Charger les données de base

Exécuter ces commandes **dans cet ordre exact** :

```bat
python manage.py loaddata fixtures\roles.json
```
```bat
python manage.py loaddata fixtures\sous_directions.json
```
```bat
python manage.py loaddata fixtures\sections.json
```
```bat
python manage.py loaddata fixtures\type_documents.json
```
```bat
python manage.py loaddata fixtures\comptes_comptables.json
```
```bat
python manage.py loaddata fixtures\regles_alerte_bg.json
```

> Chaque commande doit afficher : `Installed X object(s) from 1 fixture(s)`

---

### Étape 5 — Créer le compte administrateur

```bat
python init_projet.py
```

> Compte créé : **admin / admin123**

---

### Étape 6 — Importer les collaborateurs

Vérifier que le fichier Excel des collaborateurs est bien dans le dossier `__APP_DJANGO_v2\` puis lancer :

```bat
python import_collaborateurs.py
```

> Le script crée les sous-directions, sections et comptes utilisateurs.
> Mot de passe par défaut pour tous : **cie2026**

---

### Étape 7 — Importer les activités

Vérifier que `Classeur4.xlsx` est bien dans le dossier `__APP_DJANGO_v2\` puis lancer :

```bat
python import_activites.py
```

> Le script crée les 12 sous-directions, 51 dossiers et 166 activités.

---

### Étape 8 — Démarrer le serveur

```bat
python run_server.py
```

> L'application est accessible sur : `http://127.0.0.1:8000`

---

## Procédure automatique (fichier bat)

Pour ne pas retaper toutes ces commandes à chaque fois, crée un fichier `reinitialiser.bat` dans le dossier `__APP_DJANGO_v2\` avec ce contenu :

```bat
@echo off
title DFC Manager - Reinitialisation complete
cd /d "%~dp0"

echo ============================================
echo    DFC Manager - Reinitialisation
echo ============================================
echo.

echo Suppression de la base de donnees...
del db.sqlite3 2>nul
echo.

echo [1/8] Creation des tables...
python manage.py migrate
echo.

echo [2/8] Chargement des roles...
python manage.py loaddata fixtures\roles.json

echo [3/8] Chargement des sous-directions...
python manage.py loaddata fixtures\sous_directions.json

echo [4/8] Chargement des sections...
python manage.py loaddata fixtures\sections.json

echo [5/8] Chargement des types de documents...
python manage.py loaddata fixtures\type_documents.json

echo [6/8] Chargement des comptes et regles...
python manage.py loaddata fixtures\comptes_comptables.json
python manage.py loaddata fixtures\regles_alerte_bg.json
echo.

echo [7/8] Creation du compte administrateur...
python init_projet.py
echo.

echo [8/8] Import des collaborateurs et activites...
python import_collaborateurs.py
python import_activites.py
echo.

echo ============================================
echo    Reinitialisation terminee !
echo    Lancez run_server.py pour demarrer
echo ============================================
pause
```

> **Pour l'utiliser** : double-clic sur `reinitialiser.bat`

---

## Comptes créés après réinitialisation

| Compte | Mot de passe | Rôle |
|---|---|---|
| `admin` | `admin123` | Administrateur |
| `prenom.nom` | `cie2026` | Selon catégorie Excel |

---

## En cas d'erreur

### "No module named 'config'"
Le terminal n'est pas dans le bon dossier. Vérifier avec :
```bat
cd C:\Users\arthur.gue\OneDrive - GS2E\Documents\DOC ARTHUR\DOC CIE\__APP_DJANGO_v2
```

### "Fichier introuvable" sur le fichier Excel
Copier le fichier Excel directement dans le dossier `__APP_DJANGO_v2\`.

### "UNIQUE constraint failed"
La base n'a pas été correctement supprimée. Vérifier que `db.sqlite3` n'existe plus et recommencer depuis l'étape 2.

### "Installed 0 objects" sur un loaddata
Le fichier fixture est vide ou mal formé. Vérifier que le fichier `.json` correspondant est bien dans le dossier `fixtures\`.
