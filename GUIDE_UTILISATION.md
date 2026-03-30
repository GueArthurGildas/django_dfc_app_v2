# Guide d'utilisation — CIE Manager

### Direction Financière et Comptable · Compagnie Ivoirienne d'Électricité

\---

## Démarrage rapide

### Lancer l'application

```bat
cd \_\_APP\_DJANGO\_v2
venv\\Scripts\\activate
python run\_server.py
```

Ouvrir dans le navigateur : **http://127.0.0.1:8000**

### Première installation (base vide)

```bat
python manage.py migrate
python manage.py loaddata fixtures/roles.json
python manage.py loaddata fixtures/sous\_directions.json
python manage.py loaddata fixtures/sections.json
python manage.py loaddata fixtures/type\_documents.json
python manage.py loaddata fixtures/comptes\_comptables.json
python init\_projet.py
python seed\_data.py
```

\---

## Comptes utilisateurs

|Identifiant|Mot de passe|Rôle|Périmètre|
|-|-|-|-|
|`admin`|`admin123`|Administrateur|Global|
|`directeur.dfc`|`cie2026`|Directeur Financier|Global|
|`directeur.adjoint`|`cie2026`|Directeur Adjoint|Global|
|`sd.sdcc`|`cie2026`|Sous-Directeur|SDCC uniquement|
|`sd.sdpcc`|`cie2026`|Sous-Directeur|SDPCC uniquement|
|`chef.facturation`|`cie2026`|Chef de Section|SDCC / SC-FACT|
|`chef.comptabilite`|`cie2026`|Chef de Section|SDPCC / SC-COMPTA|
|`cadre.facturation1`|`cie2026`|Cadre|SDCC / SC-FACT|
|`cadre.comptabilite1`|`cie2026`|Cadre|SDPCC / SC-COMPTA|

\---

## Hiérarchie des rôles et droits

|Niveau|Rôle|Peut créer activités|Voit toutes les SD|
|-|-|-|-|
|1|Administrateur|✅|✅|
|2|Directeur Financier (DFC)|✅|✅|
|3|Directeur Adjoint (DA)|✅|✅|
|4|Sous-Directeur|✅|❌ Sa SD seulement|
|5|Chef de Section|❌|❌ Sa SD seulement|
|6|Cadre|❌|❌ Sa SD seulement|
|7|Agent de Maîtrise|❌|❌ Sa SD seulement|
|8|Visiteur|❌|❌ Sa SD seulement|

\---

## Fonctionnalités par module

### 🏠 Dashboard (`/`)

* **4 taux clés** : Complétion, Délais, Retard, Avancement moyen
* **Filtre SD** (Admin/DFC/DA uniquement) : voir une SD spécifique
* **Filtre période** : par année et trimestre comptable (T1/T2/T3/T4)
* **Mes activités** : focus sur les activités où vous êtes responsable ou acteur
* **Activités urgentes** : échéances dans les 7 prochains jours

### 🏢 Sous-Directions (`/organisation/sous-directions/`)

* Vue portail avec les cards des deux SD (SDCC et SDPCC)
* Bouton **Activités** sur chaque card → filtre direct sur la liste
* Cliquer sur une SD → fiche détail

**Fiche Sous-Direction :**

* Description avec effet **typewriter** (écriture en temps réel)
* **Audio de présentation** : lecteur custom (play/pause/seek/durée)

  * Upload réservé à l'admin via le bouton "Uploader un audio"
* **Statistiques filtrables** par année et trimestre (pie chart mis à jour)
* **Membres** de l'équipe avec photos et grades
* **Dossiers** de la SD groupés par section avec barre de progression
* **Comptes comptables** suivis avec bouton d'ajout inline
* **PIP** (Partenaires Institutionnels et Prestataires)

### 📁 Dossiers (`/operations/dossiers/`)

* Liste en cards avec filtre par Sous-Direction
* Chaque card affiche : taux de complétion, nombre d'activités, section
* Créer un dossier : le formulaire filtre automatiquement les sections selon votre SD

### ✅ Activités (`/operations/activites/`)

**Créer une activité** (Sous-Directeur / DA / DFC uniquement) :

1. Sélectionner un **dossier** → la section et SD sont héritées automatiquement
2. Les **membres** de la SD apparaissent pour sélectionner :

   * **Responsable(s)** : portent l'activité
   * **Acteurs** : participants
3. Sélectionner les **documents attendus** à produire
4. Renseigner les dates (ouverture, butoir, intermédiaire optionnelle)

**Filtres disponibles :**

* Barre de **recherche** (titre, dossier, section, SD)
* **Statut** : Ouverte / En cours / En attente / Clôturée
* **Sous-Direction**
* **Année** et **Trimestre** (T1/T2/T3/T4)
* **Mes activités** : uniquement celles où vous êtes impliqué

**Fiche activité :**

|Bloc|Action|
|-|-|
|Statut + Avancement|Boutons radio + slider → soumission met à jour le statut|
|Documents attendus|Switch d'état (Non commencé → En cours → Finalisé → Validé)|
|Acteurs|Ajouter / Retirer / Changer le rôle inline|
|Clôture|Sélection du motif (5 options colorées) + commentaire|
|Clonage|Visible si type = "Mensuelle récurrente" — clone pour le mois suivant|

**Statuts et transitions :**

```
Ouverte → En cours (auto si avancement > 0%)
En cours → En attente (manuel)
En cours → Clôturée (via le formulaire de clôture avec motif)
Clôturée → Cloner (si mensuelle récurrente)
```

### 📋 Kanban (`/operations/activites/kanban/`)

* 4 colonnes : Ouverte / En cours / En attente / Clôturée
* **Drag \& drop** pour déplacer une activité et changer son statut
* Filtre par **SD**, **année** et **trimestre**

### 🔔 Alertes (cloche en haut)

La cloche s'allume en orange avec le nombre d'alertes quand :

* Une activité est **en retard** (date butoir dépassée)
* Une activité est **urgente** (échéance dans 7 jours)

Cliquer → dropdown avec la liste des activités concernées.

### 🤖 ARIA — Assistant IA

Cliquer sur **ARIA** (bouton violet en haut) → panel latéral.

* Connecté à **Ollama local** (gemma2:9b)
* Spécialisé en comptabilité SYSCOHADA, finance d'entreprise, gestion du stress
* Pose des questions pour approfondir la conversation
* **Aucune sauvegarde** : chaque session repart de zéro

Exemples de questions :

* "Comment lire une Balance Générale ?"
* "Explique-moi le lettrage comptable"
* "Quelle est la différence entre le Grand Livre et la Balance ?"
* "Comment gérer le stress en période d'arrêté ?"

> ⚠️ Ollama doit tourner en local : `ollama serve` avant de lancer l'appli.

### 📢 Annonces administrateur

Depuis `/admin/` → **Annonces** → Créer une annonce avec :

* Titre + Description + Image (optionnelle)
* Période d'affichage (date début / date fin)
* L'annonce s'affiche à tous les utilisateurs connectés sous forme de **modal animé**
* Elle n'apparaît qu'une fois par session (mémorisée en session navigateur)

\---

## Administration (`/admin/`)

Accessible uniquement avec le compte `admin`.

### Créer un utilisateur

1. **Authentication → Utilisateurs → Ajouter**
2. Remplir : nom d'utilisateur + mot de passe → **Enregistrer et continuer**
3. Sur la fiche : prénom, nom, email, matricule, rôle, cocher "Est actif CIE"
4. En bas → **Affectations aux sections** → Ajouter la section + cocher "Est principale"
5. **Enregistrer**

### Gérer le référentiel

|Référentiel|Où|Usage|
|-|-|-|
|Types de documents|Operations → Types de documents|Documents attendus par activité|
|Comptes comptables|Organisation → Comptes comptables|Comptes à affecter aux SD|
|PIP|Organisation → PIPs|Partenaires par SD|
|Rôles|Authentication → Rôles|Niveaux d'accès|

\---

## Arrêtés comptables — Workflow recommandé

Chaque trimestre (T1 = Jan-Mar, T2 = Avr-Jun, T3 = Jul-Sep, T4 = Oct-Déc) :

1. Le **Sous-Directeur** crée les activités d'arrêté dans le dossier correspondant
2. Il désigne les **responsables** et **acteurs** pour chaque document à produire
3. Les **cadres** mettent à jour l'état des documents depuis leur fiche activité
4. Les **Chefs de section** suivent l'avancement via le dashboard filtré sur le trimestre
5. À la fin : clôture de l'activité avec le motif (Objectif atteint / Partiellement / etc.)
6. L'activité mensuelle est **clonée** pour le mois suivant en un clic

\---

## Résolution des problèmes fréquents

|Problème|Cause|Solution|
|-|-|-|
|`Conflicting migrations`|Plusieurs `0002\_\*.py` dans un app|Supprimer les `0002\_\*` et `0003\_\*`, refaire `makemigrations --name="vX"`|
|`duplicate column`|Migration déjà appliquée|`python manage.py migrate operations 0002\_xxx --fake`|
|ARIA ne répond pas|Ollama non démarré|Lancer `ollama serve` dans un terminal|
|Badge alertes à 0|Normal si aucun retard|Il s'allume automatiquement|
|Audio écrase les données SD|Bug corrigé — utiliser la vue dédiée|Mettre à jour `organisation/views.py`|
|<br /><br />|||









maintenance probleme :



venv\\Scripts\\activate



:: 1. Supprimer la base

del db.sqlite3



:: 2. Lister toutes les migrations operations pour voir ce qu'il y a

dir apps\\operations\\migrations\\



:: 3. Garder UNIQUEMENT 0001\_initial\_operations.py

::    Supprimer TOUT le reste dans apps\\operations\\migrations\\ sauf \_\_init\_\_.py et 0001\_\*

del apps\\operations\\migrations\\0002\_\*.py

del apps\\operations\\migrations\\0003\_\*.py



:: 4. Recréer UNE SEULE migration propre

python manage.py makemigrations operations --name="v2\_complet"



:: 5. Appliquer

python manage.py migrate



:: 6. Données initiales

python init\_projet.py

python manage.py loaddata fixtures/type\_documents.json

python manage.py loaddata fixtures/comptes\_comptables.json

python seed\_data.py

