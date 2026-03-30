# CIE Manager — Documentation Développeur
**DFC / CIE — Plateforme de Gestion Opérationnelle & Comptable**
Version 2.0 — 2026

---

## Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Structure des répertoires](#2-structure-des-répertoires)
3. [Description des applications](#3-description-des-applications)
4. [Fichiers clés à connaître](#4-fichiers-clés-à-connaître)
5. [Greffer une nouvelle application](#5-greffer-une-nouvelle-application)
6. [Règles et conventions](#6-règles-et-conventions)
7. [Commandes utiles](#7-commandes-utiles)

---

## 1. Vue d'ensemble

CIE Manager est une application web Django déployée en interne (LAN) à la DFC/CIE.
Elle centralise la gestion des activités, dossiers, arrêtés comptables et le suivi
par sous-direction.

| Élément | Valeur |
|---|---|
| Framework | Django 4.x + DRF |
| Base de données | SQLite (dev) |
| Serveur | Waitress (Windows, sans droits admin) |
| Frontend | Bootstrap 5 + Chart.js |
| Tâches planifiées | Celery + Redis |
| Fuseau horaire | Africa/Abidjan (GMT+0) |

---

## 2. Structure des répertoires

```
cie_manager/                          ← Racine du projet
│
├── config/                           ← Configuration Django
│   ├── settings.py                   ← BDD, apps installées, Celery, email...
│   ├── urls.py                       ← Routes principales (point d'entrée URLs)
│   ├── wsgi.py                       ← Interface WSGI pour Waitress
│   └── celery.py                     ← Configuration Celery
│
├── apps/                             ← Toutes les applications métier
│   │
│   ├── authentication/               ← Utilisateurs, rôles, login/logout
│   │   ├── models.py                 ← Utilisateur (AbstractUser), Role
│   │   ├── views.py                  ← LoginView, LogoutView, ProfilView
│   │   ├── urls.py                   ← /auth/login/ /auth/logout/ /auth/profil/
│   │   ├── admin.py
│   │   └── apps.py
│   │
│   ├── organisation/                 ← Structure DFC : SD, Sections, PIP, Comptes
│   │   ├── models.py                 ← SousDirection, Section, UtilisateurSection,
│   │   │                                PIP, CompteComptable, SousDirectionCompte
│   │   ├── views.py                  ← CRUD SD, Sections, PIP, Comptes, Audio
│   │   ├── urls.py                   ← /organisation/...
│   │   ├── forms.py                  ← SousDirectionForm, SectionForm, PIPForm
│   │   ├── admin.py
│   │   ├── context_processors.py     ← Injecte sous_directions_sidebar partout
│   │   └── modules/
│   │       ├── sdcc/                 ← Vues spécifiques SDCC (Phase 3)
│   │       │   ├── urls.py
│   │       │   └── views.py
│   │       └── sdpcc/                ← Vues spécifiques SDPCC (Phase 3)
│   │           ├── urls.py
│   │           └── views.py
│   │
│   ├── operations/                   ← Dossiers, Activités, Documents — cœur du système
│   │   ├── models.py                 ← Dossier, Activite, ActiviteActeur,
│   │   │                                ActivitePIP, CommentaireActivite,
│   │   │                                HistoriqueActivite, AlerteMail,
│   │   │                                TypeDocument, DocumentActivite
│   │   ├── views.py                  ← Toutes les vues + API JSON dashboard
│   │   ├── urls.py                   ← /operations/...
│   │   ├── forms.py                  ← ActiviteForm, DossierForm, CloreForm...
│   │   ├── services.py               ← ActiviteService (toute la logique métier)
│   │   ├── notifications.py          ← AlerteMailService (6 types d'emails)
│   │   ├── signals.py                ← Historique automatique via post_save
│   │   ├── tasks.py                  ← Celery : clonage mensuel + rappels J-7/J-3/J-1
│   │   ├── admin.py
│   │   └── templatetags/
│   │       └── operations_extras.py  ← Filtres custom Django : |abs_value, |subtract
│   │
│   ├── comptabilite/                 ← Balance Générale, Grand Livre (Phase 3)
│   │   ├── models.py
│   │   ├── views.py
│   │   └── urls.py
│   │
│   └── dashboard/                    ← Tableau de bord global
│       ├── views.py                  ← DashboardView (stats filtrées par rôle + période)
│       ├── urls.py                   ← / (racine)
│       └── models.py
│
├── templates/                        ← Tous les templates HTML
│   ├── base.html                     ← Layout principal (sidebar + topbar)
│   ├── base_auth.html                ← Layout page de connexion
│   │
│   ├── partials/                     ← Composants réutilisables inclus via {% include %}
│   │   ├── sidebar_nav.html          ← Navigation gauche (générée dynamiquement)
│   │   ├── filtre_periode.html       ← Filtre Année/Trimestre (dashboard, list, kanban)
│   │   └── filtre_periode_sd.html    ← Filtre Année/Trimestre (fiche SD)
│   │
│   ├── authentication/
│   │   ├── login.html
│   │   └── profil.html
│   │
│   ├── organisation/
│   │   ├── portail/
│   │   │   └── sd_portail.html       ← Page liste des SD avec cards
│   │   ├── sous_direction/
│   │   │   ├── detail.html           ← Fiche SD complète
│   │   │   └── form.html             ← Formulaire créer/modifier SD
│   │   ├── section/
│   │   │   ├── list.html
│   │   │   ├── detail.html
│   │   │   └── form.html
│   │   └── pip/
│   │       ├── list.html
│   │       └── form.html
│   │
│   ├── operations/
│   │   ├── dossier/
│   │   │   ├── list.html             ← Liste avec filtre SD
│   │   │   ├── detail.html
│   │   │   └── form.html
│   │   ├── activite/
│   │   │   ├── list.html             ← Liste avec recherche + filtres
│   │   │   ├── detail.html           ← Fiche complète : jauge, timeline, documents
│   │   │   ├── kanban.html           ← Kanban drag & drop
│   │   │   └── form.html             ← Création avec membres dynamiques
│   │   └── coming_soon.html          ← Placeholder modules P3
│   │
│   └── dashboard/
│       └── index.html                ← Tableau de bord avec filtres
│
├── static/                           ← Fichiers statiques (CSS, JS, images)
│   ├── css/
│   ├── js/
│   └── images/
│
├── media/                            ← Fichiers uploadés par les utilisateurs
│   ├── photos/                       ← Photos de profil utilisateurs
│   ├── audio/sd/                     ← Audios de présentation des SD
│   └── documents/activites/          ← Documents liés aux activités
│
├── fixtures/                         ← Données initiales au format JSON
│   ├── roles.json                    ← 8 rôles (admin, dfc, da, sd, chef, cadre...)
│   ├── sous_directions.json          ← SDCC + SDPCC
│   ├── sections.json                 ← 5 sections réparties entre les SD
│   ├── type_documents.json           ← 15 types de documents (Balance, Grand Livre...)
│   └── comptes_comptables.json       ← 25 comptes comptables DFC/CIE
│
├── apps/operations/migrations/       ← Migrations de la base de données
│   ├── 0001_initial.py               ← Migration initiale
│   └── 0002_*.py                     ← Évolutions des modèles
│
├── manage.py                         ← Point d'entrée Django CLI
├── init_projet.py                    ← Script d'initialisation complète
├── seed_data.py                      ← Données de test réalistes
├── run_server.py                     ← Lancement Waitress (LAN)
├── start.bat                         ← Démarrage Windows (double-clic)
├── init_projet.bat                   ← Initialisation Windows (première fois)
└── requirements.txt                  ← Dépendances Python
```

---

## 3. Description des applications

### `authentication` — Gestion des utilisateurs

Contient le modèle `Utilisateur` qui étend `AbstractUser` de Django avec :
- `role` (FK vers `Role`) : Admin, DFC, DA, SD, Chef, Cadre, Maîtrise, Visiteur
- `matricule`, `telephone`, `photo`, `est_actif_cie`

Les méthodes clés sur `Utilisateur` :
- `get_section()` → retourne la section principale
- `get_sous_direction()` → retourne la SD via la section
- `peut_voir_sous_direction(sd)` → contrôle d'accès

---

### `organisation` — Structure organisationnelle

Modèles principaux :

| Modèle | Rôle |
|---|---|
| `SousDirection` | SDCC et SDPCC sont des **instances** de ce modèle, pas des apps |
| `Section` | Rattachée à une SousDirection |
| `UtilisateurSection` | Pivot utilisateur ↔ section |
| `PIP` | Partenaires d'échange |
| `CompteComptable` | Référentiel des comptes (411, 706, etc.) |
| `SousDirectionCompte` | Pivot SD ↔ CompteComptable |

> ⚠️ **Règle fondamentale** : Ne jamais créer d'apps Django `sdcc` ou `sdpcc`.
> Ces deux entités sont des enregistrements en base dans la table `SousDirection`.

---

### `operations` — Cœur du système

Modèles principaux :

| Modèle | Rôle |
|---|---|
| `Dossier` | Conteneur d'activités, rattaché à une Section |
| `Activite` | Activité avec 4 dates, statut, avancement, clôture motivée |
| `ActiviteActeur` | Pivot activité ↔ utilisateur (responsable ou acteur) |
| `CommentaireActivite` | Timeline de suivi avec type et avancement déclaré |
| `HistoriqueActivite` | Journal automatique de toutes les modifications |
| `TypeDocument` | Référentiel des documents/rendus attendus |
| `DocumentActivite` | Document attendu sur une activité avec état d'avancement |

**Statuts d'une activité** (transitions) :

```
Ouverte → En cours → En attente → Clôturée
              ↑           ↓
              └───────────┘ (retour possible)
```

- Passage `Ouverte → En cours` : automatique si avancement > 0%
- Passage `→ Clôturée` : uniquement via le formulaire de clôture avec motif

**Logique métier centralisée dans `ActiviteService`** :
- `creer()`, `mettre_a_jour()`, `clore()`, `reporter_date()`, `cloner()`
- **Ne jamais modifier le statut ou l'avancement directement** — toujours passer par le service

---

### `dashboard` — Tableau de bord

La vue `DashboardView` calcule toutes les statistiques en tenant compte :
- Du rôle de l'utilisateur (accès global vs périmètre SD)
- Du filtre SD sélectionné (Admin/DFC/DA uniquement)
- Du filtre Année/Trimestre (arrêtés comptables)

---

## 4. Fichiers clés à connaître

### `apps/operations/views.py` — Helpers de périmètre

```python
ROLES_GLOBAUX  = ('admin', 'dfc', 'da')   # accès à toutes les SD
ROLES_CREATION = ('admin', 'dfc', 'da', 'sd')  # peuvent créer des activités

def get_user_sd(user)
    # Retourne None si accès global, ou la SD de l'utilisateur

def filtre_qs_par_sd(qs, user, champ_sd='section__sous_direction')
    # Filtre automatiquement un queryset selon le périmètre de l'utilisateur

def appliquer_filtre_periode(qs, annee, trimestre)
    # Filtre par année et/ou trimestre comptable (T1=Jan-Mar, T2=Avr-Jun...)

def get_qs_activites(user)
    # Retourne les activités visibles par l'utilisateur
```

### `apps/organisation/context_processors.py`

Injecte `sous_directions_sidebar` dans **tous** les templates.
La sidebar est générée dynamiquement depuis la base — toute nouvelle SD
créée en admin apparaît automatiquement dans le menu.

### `templates/partials/filtre_periode.html`

Composant réutilisable à inclure avec :
```html
{% include "partials/filtre_periode.html" %}
```
Affiche les boutons T1/T2/T3/T4 + le select Année.
Nécessite `annees_dispo`, `trimestres`, `filtre_annee`, `filtre_trimestre` dans le contexte.

### `apps/operations/templatetags/operations_extras.py`

Filtres Django personnalisés. À charger dans les templates avec :
```html
{% load operations_extras %}
{{ valeur|abs_value }}
{{ valeur|subtract:5 }}
```

---

## 5. Greffer une nouvelle application

Exemple complet : ajouter une app **`reporting`** pour les rapports PDF.

### Étape 1 — Créer l'app

```bat
venv\Scripts\activate
python manage.py startapp reporting apps/reporting
```

### Étape 2 — Déclarer dans `config/settings.py`

```python
INSTALLED_APPS = [
    ...
    'apps.authentication',
    'apps.organisation',
    'apps.operations',
    'apps.comptabilite',
    'apps.dashboard',
    'apps.reporting',    # ← ajouter ici
]
```

### Étape 3 — Créer `apps/reporting/apps.py`

```python
from django.apps import AppConfig

class ReportingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.reporting'
    verbose_name = 'Reporting'
```

### Étape 4 — Créer les modèles (`apps/reporting/models.py`)

```python
from django.db import models

class Rapport(models.Model):
    titre          = models.CharField(max_length=200)
    # Référencer une autre app avec une string pour éviter les imports circulaires
    sous_direction = models.ForeignKey(
        'organisation.SousDirection',
        on_delete=models.CASCADE,
        related_name='rapports'
    )
    periode        = models.CharField(max_length=7)   # ex: 2026-T1
    created_at     = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titre} — {self.periode}"
```

```bat
python manage.py makemigrations reporting
python manage.py migrate
```

### Étape 5 — Créer les vues (`apps/reporting/views.py`)

```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from .models import Rapport
# Réutiliser les helpers de périmètre existants
from apps.operations.views import get_user_sd, filtre_qs_par_sd

class RapportListView(LoginRequiredMixin, ListView):
    model = Rapport
    template_name = 'reporting/list.html'
    context_object_name = 'rapports'

    def get_queryset(self):
        qs = Rapport.objects.all().select_related('sous_direction')
        # Filtrer selon le périmètre de l'utilisateur
        return filtre_qs_par_sd(qs, self.request.user, 'sous_direction')
```

### Étape 6 — Créer les URLs (`apps/reporting/urls.py`)

```python
from django.urls import path
from . import views

app_name = 'reporting'

urlpatterns = [
    path('',          views.RapportListView.as_view(),   name='liste'),
    path('<int:pk>/', views.RapportDetailView.as_view(), name='detail'),
]
```

### Étape 7 — Brancher dans `config/urls.py`

```python
urlpatterns = [
    path('admin/',        admin.site.urls),
    path('auth/',         include('apps.authentication.urls')),
    path('organisation/', include('apps.organisation.urls')),
    path('operations/',   include('apps.operations.urls')),
    path('comptabilite/', include('apps.comptabilite.urls')),
    path('sdcc/',         include('apps.organisation.modules.sdcc.urls')),
    path('sdpcc/',        include('apps.organisation.modules.sdpcc.urls')),
    path('reporting/',    include('apps.reporting.urls')),   # ← ajouter
    path('',              include('apps.dashboard.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### Étape 8 — Créer les templates

```
templates/reporting/
    list.html
    detail.html
```

Structure minimale d'un template :
```html
{% extends "base.html" %}
{% load operations_extras %}   {# si vous avez besoin des filtres custom #}

{% block title %}Rapports{% endblock %}
{% block page_title %}Rapports{% endblock %}

{% block content %}
  {# Inclure le filtre période si pertinent #}
  {% include "partials/filtre_periode.html" %}

  {# Contenu de la page #}
{% endblock %}
```

### Étape 9 — Ajouter dans la sidebar (`templates/partials/sidebar_nav.html`)

```html
<div class="nav-section">Reporting</div>
<a href="{% url 'reporting:liste' %}"
   class="nav-link {% if request.resolver_match.app_name == 'reporting' %}active{% endif %}">
  <i class="bi bi-file-earmark-bar-graph"></i> Rapports
</a>
```

### Étape 10 — Déclarer dans l'admin (`apps/reporting/admin.py`)

```python
from django.contrib import admin
from .models import Rapport

@admin.register(Rapport)
class RapportAdmin(admin.ModelAdmin):
    list_display = ['titre', 'sous_direction', 'periode', 'created_at']
    list_filter  = ['sous_direction', 'periode']
```

---

## 6. Règles et conventions

### Nommage

| Élément | Convention | Exemple |
|---|---|---|
| Models | PascalCase singulier | `ActiviteActeur` |
| Vues | PascalCase + suffixe | `ActiviteListView` |
| URLs | snake_case avec namespace | `operations:activite_list` |
| Templates | `app/action.html` | `operations/activite/list.html` |
| Fixtures | snake_case | `type_documents.json` |

### Relations entre apps

```python
# ✓ Correct — string pour éviter les imports circulaires en ForeignKey
activite = models.ForeignKey('operations.Activite', on_delete=models.CASCADE)

# ✓ Correct — import direct dans les vues et services
from apps.organisation.models import SousDirection

# ✗ Incorrect — import circulaire potentiel au niveau des modèles
from apps.operations.models import Activite  # dans organisation/models.py
```

### RBAC — Contrôle d'accès

Toujours utiliser les helpers centralisés :

```python
from apps.operations.views import get_user_sd, filtre_qs_par_sd, ROLES_GLOBAUX

# Dans une vue
def get_queryset(self):
    qs = MonModel.objects.all()
    return filtre_qs_par_sd(qs, self.request.user)

# Vérifier le rôle
if request.user.role and request.user.role.code in ROLES_GLOBAUX:
    # accès total
```

### Logique métier

- Toute modification de statut/avancement d'une activité **doit** passer par `ActiviteService`
- Ne jamais appeler `activite.save()` directement pour modifier le statut
- Les emails sont envoyés via `AlerteMailService` uniquement

### Migrations

```bat
# ✓ Toujours spécifier l'app
python manage.py makemigrations operations --name="description_courte"

# ✗ Ne jamais faire sans argument (risque de conflits entre apps)
python manage.py makemigrations
```

### Templates et JSON

```html
{# ✓ Toujours ajouter |safe pour les données JSON dans <script> #}
const DATA = {{ ma_variable_json|safe }};

{# ✗ Sans |safe, Django échappe les guillemets et le JSON est invalide #}
const DATA = {{ ma_variable_json }};
```

### Filtres template

```html
{# ✓ Correct — load APRÈS extends #}
{% extends "base.html" %}
{% load operations_extras %}

{# ✗ Incorrect — load AVANT extends provoque une TemplateSyntaxError #}
{% load operations_extras %}
{% extends "base.html" %}
```

---

## 7. Commandes utiles

### Démarrage quotidien

```bat
venv\Scripts\activate
python run_server.py
```

### Première installation

```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python init_projet.py
python manage.py loaddata fixtures/type_documents.json
python manage.py loaddata fixtures/comptes_comptables.json
python seed_data.py
python run_server.py
```

### Réinitialisation complète (base de données)

```bat
del db.sqlite3
del apps\operations\migrations\0002_*.py
del apps\operations\migrations\0003_*.py
python manage.py makemigrations operations --name="operations_v2"
python manage.py migrate
python init_projet.py
python manage.py loaddata fixtures/type_documents.json
python manage.py loaddata fixtures/comptes_comptables.json
python seed_data.py
```

### Gestion des migrations

```bat
:: Créer une migration pour une app spécifique
python manage.py makemigrations operations --name="add_nouveau_champ"

:: Appliquer toutes les migrations
python manage.py migrate

:: Voir l'état des migrations
python manage.py showmigrations

:: Annuler une migration (revenir à l'état précédent)
python manage.py migrate operations 0001
```

### Gestion des données

```bat
:: Créer un superutilisateur
python manage.py createsuperuser

:: Exporter des données en fixture
python manage.py dumpdata operations.TypeDocument --indent=2 > fixtures/type_documents.json

:: Charger des fixtures
python manage.py loaddata fixtures/roles.json

:: Lancer le shell Django (tests rapides)
python manage.py shell
```

### Vérification et debug

```bat
:: Vérifier la configuration (0 erreur = OK)
python manage.py check

:: Voir les URLs disponibles
python manage.py show_urls

:: Collecter les fichiers statiques (production)
python manage.py collectstatic
```

---

*CIE Manager — Document de référence développeur — DFC/CIE v2.0 — 2026*
