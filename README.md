# CIE Manager — P1 Fondations
**DFC / CIE — Plateforme de Gestion Opérationnelle & Comptable**

## Installation

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Initialiser (migrations + fixtures + admin)
python init_projet.py

# 3. Lancer le serveur
python run_server.py           # Waitress — accès LAN  http://0.0.0.0:8000
# ou
python manage.py runserver     # Dev uniquement
```

## Compte admin par défaut
- **Identifiant** : `admin`
- **Mot de passe** : `admin123`
- **Email** : admin@cie-manager.ci

## Structure du projet
```
cie_manager/
├── config/          → settings, urls, wsgi, celery
├── apps/
│   ├── authentication/  → Utilisateur custom, login, rôles
│   ├── organisation/    → SousDirection, Section, PIP (SDCC/SDPCC en base)
│   ├── operations/      → [P2] Dossiers, Activités, Kanban
│   ├── comptabilite/    → [P3] Balance Générale, Grand Livre
│   └── dashboard/       → Tableau de bord KPI
├── templates/       → base.html, sidebar dynamique, tous les templates
├── fixtures/        → roles.json, sous_directions.json, sections.json
├── static/          → CSS, JS, images
├── init_projet.py   → Script d'initialisation complet
└── run_server.py    → Lancement Waitress (LAN, sans droits admin)
```

## Données pré-chargées
- 8 rôles : Admin, DFC, DA, SD, Chef de Section, Cadre, Maîtrise, Visiteur
- 2 Sous-Directions : SDCC + SDPCC (instances en base, pas des apps)
- 5 Sections réparties entre SDCC et SDPCC
- 1 superutilisateur admin

## Ce qui est livré dans P1
- [x] Modèle Utilisateur custom (AbstractUser + rôle + matricule)
- [x] Authentification login/logout/profil
- [x] Models SousDirection, Section, UtilisateurSection, PIP
- [x] CRUD complet Organisation (SD, Sections, PIP)
- [x] Sidebar dynamique générée depuis la base de données
- [x] Dashboard avec KPI + Chart.js (prêt pour P2)
- [x] Base.html responsive Bootstrap 5 + charte CIE
- [x] Context processor sidebar_context
- [x] Admin Django configuré
- [x] Script Waitress (accès LAN sans droits admin)
- [x] SQLite en développement

## Prochaine étape — P2
Module Activités : models Dossier/Activite/Acteur, ActiviteService,
vue Kanban drag & drop, timeline commentaires, jauge de progression,
alertes email, Celery Beat clonage mensuel.
