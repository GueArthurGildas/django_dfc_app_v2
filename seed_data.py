"""
Script de données de test — CIE Manager
Crée des utilisateurs, dossiers et activités réalistes pour la DFC/CIE.
Usage : python seed_data.py
"""
import os, sys, django
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.authentication.models import Utilisateur, Role
from apps.organisation.models import Section, SousDirection, UtilisateurSection, PIP
from apps.operations.models import Dossier, Activite, ActiviteActeur
from django.utils import timezone

today = date.today()

print("=== Seed Data — CIE Manager ===\n")

# ── 1. UTILISATEURS ──────────────────────────────────────────────────────────
print("1. Création des utilisateurs...")

USERS = [
    # SDCC
    dict(username='kouassi.ahou',    password='cie2026', first_name='Kouassi',   last_name='AHOU',       matricule='SDCC-001', role_code='sd',      section_code='SC-FACT',  email='k.ahou@cie.ci'),
    dict(username='bamba.coulibaly',  password='cie2026', first_name='Bamba',     last_name='COULIBALY',  matricule='SDCC-002', role_code='chef',    section_code='SC-FACT',  email='b.coulibaly@cie.ci'),
    dict(username='aya.kone',         password='cie2026', first_name='Aya',       last_name='KONE',       matricule='SDCC-003', role_code='cadre',   section_code='SC-FACT',  email='a.kone@cie.ci'),
    dict(username='ibrahim.traore',   password='cie2026', first_name='Ibrahim',   last_name='TRAORE',     matricule='SDCC-004', role_code='cadre',   section_code='SC-FACT',  email='i.traore@cie.ci'),
    dict(username='mariam.diallo',    password='cie2026', first_name='Mariam',    last_name='DIALLO',     matricule='SDCC-005', role_code='maitrise',section_code='SC-RECOV', email='m.diallo@cie.ci'),
    dict(username='serge.yao',        password='cie2026', first_name='Serge',     last_name='YAO',        matricule='SDCC-006', role_code='chef',    section_code='SC-RECOV', email='s.yao@cie.ci'),
    dict(username='fatoumata.bah',    password='cie2026', first_name='Fatoumata', last_name='BAH',        matricule='SDCC-007', role_code='cadre',   section_code='SC-COM',   email='f.bah@cie.ci'),
    dict(username='eric.assoumou',    password='cie2026', first_name='Éric',      last_name='ASSOUMOU',   matricule='SDCC-008', role_code='cadre',   section_code='SC-COM',   email='e.assoumou@cie.ci'),
    # SDPCC
    dict(username='adjoua.niamke',    password='cie2026', first_name='Adjoua',    last_name='NIAMKE',     matricule='SDPCC-001',role_code='sd',      section_code='SC-COMPTA',email='a.niamke@cie.ci'),
    dict(username='brou.konan',       password='cie2026', first_name='Brou',      last_name='KONAN',      matricule='SDPCC-002',role_code='chef',    section_code='SC-COMPTA',email='b.konan@cie.ci'),
    dict(username='alice.gnagne',     password='cie2026', first_name='Alice',     last_name='GNAGNE',     matricule='SDPCC-003',role_code='cadre',   section_code='SC-COMPTA',email='a.gnagne@cie.ci'),
    dict(username='patrick.koffi',    password='cie2026', first_name='Patrick',   last_name='KOFFI',      matricule='SDPCC-004',role_code='cadre',   section_code='SC-COMPTA',email='p.koffi@cie.ci'),
    dict(username='rosine.akre',      password='cie2026', first_name='Rosine',    last_name='AKRE',       matricule='SDPCC-005',role_code='maitrise',section_code='SC-PROJ',  email='r.akre@cie.ci'),
    dict(username='jean.kouadio',     password='cie2026', first_name='Jean',      last_name='KOUADIO',    matricule='SDPCC-006',role_code='chef',    section_code='SC-PROJ',  email='j.kouadio@cie.ci'),
    # Direction
    dict(username='directeur.dfc',    password='cie2026', first_name='Kofi',      last_name='MENSAH',     matricule='DFC-001',  role_code='dfc',     section_code='SC-COMPTA',email='dfc@cie.ci'),
    dict(username='da.adjoint',       password='cie2026', first_name='Sylvestre', last_name='OKOU',       matricule='DFC-002',  role_code='da',      section_code='SC-COMPTA',email='da@cie.ci'),
]

created_users = {}
for u in USERS:
    if Utilisateur.objects.filter(username=u['username']).exists():
        user = Utilisateur.objects.get(username=u['username'])
        print(f"  ~ Existant : {user.nom_complet}")
    else:
        role    = Role.objects.get(code=u['role_code'])
        section = Section.objects.get(code=u['section_code'])
        user = Utilisateur.objects.create_user(
            username=u['username'], password=u['password'],
            first_name=u['first_name'], last_name=u['last_name'],
            email=u['email'], matricule=u['matricule'],
            role=role, est_actif_cie=True
        )
        UtilisateurSection.objects.get_or_create(
            utilisateur=user, section=section,
            defaults={'est_principale': True}
        )
        print(f"  + Créé : {user.nom_complet} ({role.libelle} — {section.code})")
    created_users[u['username']] = user

# Affecter les SD aux responsables
SousDirection.objects.filter(code='SDCC').update(responsable=created_users['kouassi.ahou'])
SousDirection.objects.filter(code='SDPCC').update(responsable=created_users['adjoua.niamke'])

# ── 2. PIP ───────────────────────────────────────────────────────────────────
print("\n2. Création des PIP...")

PIPS = [
    dict(code='SOGEPE',  libelle='Société de Gestion du Patrimoine de l\'État', email='sogepe@sogepe.ci',    sd_code='SDPCC'),
    dict(code='TRESOR',  libelle='Direction Générale du Trésor',                email='tresor@finances.ci',   sd_code='SDPCC'),
    dict(code='CIE-DG',  libelle='Direction Générale CIE',                      email='dg@cie.ci',            sd_code='SDCC'),
    dict(code='ANELEC',  libelle='Autorité Nationale de Régulation',            email='contact@anelec.ci',    sd_code='SDCC'),
    dict(code='BNI',     libelle='Banque Nationale d\'Investissement',          email='bni@bni.ci',           sd_code='SDPCC'),
    dict(code='CI-ENERG',libelle='CI-Energies',                                 email='contact@ci-energies.ci',sd_code='SDCC'),
]

created_pips = {}
for p in PIPS:
    sd = SousDirection.objects.get(code=p['sd_code'])
    pip, created = PIP.objects.get_or_create(
        code=p['code'],
        defaults={'libelle': p['libelle'], 'email': p['email'], 'sous_direction': sd}
    )
    created_pips[p['code']] = pip
    print(f"  {'+ Créé' if created else '~ Existant'} : {pip.code}")

# ── 3. DOSSIERS ──────────────────────────────────────────────────────────────
print("\n3. Création des dossiers...")

sec = {s.code: s for s in Section.objects.all()}

DOSSIERS = [
    # SDCC
    dict(titre='Arrêté Mensuel SDCC',       description='Dossier de suivi des arrêtés mensuels de la facturation et du recouvrement.',  section_code='SC-FACT',  resp='bamba.coulibaly'),
    dict(titre='Suivi Smart Vending',        description='Suivi des opérations Smart Vending et contrôle des caisses CIE.',             section_code='SC-FACT',  resp='aya.kone'),
    dict(titre='PEPT — Programme Élec. PT',  description='Programme Électricité Pour Tous : suivi des raccordements et facturation.',   section_code='SC-RECOV', resp='serge.yao'),
    dict(titre='Recouvrement Clients',       description='Suivi du recouvrement des créances clients et gestion des impayés.',          section_code='SC-RECOV', resp='serge.yao'),
    dict(titre='Chiffre d\'Affaires Énergie',description='Analyse et reporting mensuel du chiffre d\'affaires énergie.',               section_code='SC-COM',   resp='fatoumata.bah'),
    # SDPCC
    dict(titre='Arrêté Mensuel SDPCC',       description='Dossier de suivi des arrêtés comptables mensuels de la SDPCC.',              section_code='SC-COMPTA',resp='brou.konan'),
    dict(titre='Balance Générale & Grand Livre', description='Dépôt et contrôle de la Balance Générale et du Grand Livre mensuels.',   section_code='SC-COMPTA',resp='alice.gnagne'),
    dict(titre='Lettrage Comptable',         description='Opérations de lettrage des comptes tiers et comptes de liaison.',            section_code='SC-COMPTA',resp='patrick.koffi'),
    dict(titre='Projets Comptables SOGEPE',  description='Suivi des projets comptables en lien avec SOGEPE et le Trésor.',             section_code='SC-PROJ',  resp='jean.kouadio'),
]

created_dossiers = {}
for d in DOSSIERS:
    section = sec[d['section_code']]
    resp    = created_users[d['resp']]
    dos, created = Dossier.objects.get_or_create(
        titre=d['titre'],
        defaults={'description': d['description'], 'section': section, 'responsable': resp}
    )
    created_dossiers[d['titre']] = dos
    print(f"  {'+ Créé' if created else '~ Existant'} : {dos.titre[:50]}")

# ── 4. ACTIVITÉS ─────────────────────────────────────────────────────────────
print("\n4. Création des activités...")

def make_date(delta_days):
    return today + timedelta(days=delta_days)

ACTIVITES = [
    # ── SDCC — Facturation ──────────────────────────────────────────────────
    dict(
        titre='Édition de la Balance Facturation Janvier 2026',
        dossier='Arrêté Mensuel SDCC',
        statut='cloturee', avancement=100,
        date_ouverture=make_date(-45), date_butoir=make_date(-30),
        date_realisation=make_date(-32), est_dans_delai=True,
        description='Éditer et valider la balance de facturation du mois de janvier 2026.',
        responsable='bamba.coulibaly', acteurs=['aya.kone'],
    ),
    dict(
        titre='Édition de la Balance Facturation Février 2026',
        dossier='Arrêté Mensuel SDCC',
        statut='cloturee', avancement=100,
        date_ouverture=make_date(-15), date_butoir=make_date(-5),
        date_realisation=make_date(-7), est_dans_delai=True,
        description='Éditer et valider la balance de facturation du mois de février 2026.',
        responsable='bamba.coulibaly', acteurs=['aya.kone', 'ibrahim.traore'],
    ),
    dict(
        titre='Édition de la Balance Facturation Mars 2026',
        dossier='Arrêté Mensuel SDCC',
        statut='en_cours', avancement=60,
        date_ouverture=make_date(-5), date_butoir=make_date(5),
        date_realisation=None, est_dans_delai=None,
        description='Éditer et valider la balance de facturation du mois de mars 2026.',
        responsable='bamba.coulibaly', acteurs=['aya.kone'],
    ),
    dict(
        titre='Contrôle Caisse Smart Vending — Zone Abidjan Nord',
        dossier='Suivi Smart Vending',
        statut='en_cours', avancement=40,
        date_ouverture=make_date(-10), date_butoir=make_date(-2),  # EN RETARD
        date_realisation=None, est_dans_delai=None,
        description='Contrôle physique des caisses Smart Vending de la zone Abidjan Nord.',
        responsable='aya.kone', acteurs=['ibrahim.traore'],
    ),
    dict(
        titre='Rapprochement Smart Vending vs Système Facturation',
        dossier='Suivi Smart Vending',
        statut='ouverte', avancement=0,
        date_ouverture=make_date(-3), date_butoir=make_date(10),
        date_realisation=None, est_dans_delai=None,
        description='Rapprochement des encaissements Smart Vending avec les données du système de facturation.',
        responsable='aya.kone', acteurs=['bamba.coulibaly'],
    ),
    dict(
        titre='Suivi Raccordements PEPT — Trimestre 1 2026',
        dossier='PEPT — Programme Élec. PT',
        statut='cloturee', avancement=100,
        date_ouverture=make_date(-60), date_butoir=make_date(-20),
        date_realisation=make_date(-25), est_dans_delai=True,
        description='Comptabilisation et suivi des raccordements PEPT du T1 2026.',
        responsable='serge.yao', acteurs=['mariam.diallo'],
    ),
    dict(
        titre='Recouvrement Impayés > 90 jours',
        dossier='Recouvrement Clients',
        statut='en_cours', avancement=30,
        date_ouverture=make_date(-20), date_butoir=make_date(-5),  # EN RETARD
        date_realisation=None, est_dans_delai=None,
        description='Action de recouvrement sur les créances clients de plus de 90 jours.',
        responsable='serge.yao', acteurs=['mariam.diallo'],
    ),
    dict(
        titre='Reporting CA Énergie — Janvier 2026',
        dossier="Chiffre d'Affaires Énergie",
        statut='cloturee', avancement=100,
        date_ouverture=make_date(-50), date_butoir=make_date(-35),
        date_realisation=make_date(-40), est_dans_delai=True,
        description='Élaboration du reporting mensuel du CA énergie pour janvier 2026.',
        responsable='fatoumata.bah', acteurs=['eric.assoumou'],
    ),
    dict(
        titre='Reporting CA Énergie — Février 2026',
        dossier="Chiffre d'Affaires Énergie",
        statut='cloturee', avancement=100,
        date_ouverture=make_date(-20), date_butoir=make_date(-8),
        date_realisation=make_date(-6), est_dans_delai=False,  # HORS DELAI
        description='Élaboration du reporting mensuel du CA énergie pour février 2026.',
        responsable='fatoumata.bah', acteurs=['eric.assoumou'],
    ),
    dict(
        titre='Reporting CA Énergie — Mars 2026',
        dossier="Chiffre d'Affaires Énergie",
        statut='ouverte', avancement=15,
        date_ouverture=make_date(-2), date_butoir=make_date(12),
        date_realisation=None, est_dans_delai=None,
        description='Élaboration du reporting mensuel du CA énergie pour mars 2026.',
        responsable='fatoumata.bah', acteurs=['eric.assoumou'],
    ),

    # ── SDPCC — Comptabilité ─────────────────────────────────────────────────
    dict(
        titre='Arrêté Comptable Janvier 2026',
        dossier='Arrêté Mensuel SDPCC',
        statut='cloturee', avancement=100,
        date_ouverture=make_date(-55), date_butoir=make_date(-30),
        date_realisation=make_date(-32), est_dans_delai=True,
        description='Réalisation de l\'arrêté comptable complet du mois de janvier 2026.',
        responsable='brou.konan', acteurs=['alice.gnagne', 'patrick.koffi'],
    ),
    dict(
        titre='Arrêté Comptable Février 2026',
        dossier='Arrêté Mensuel SDPCC',
        statut='en_cours', avancement=75,
        date_ouverture=make_date(-20), date_butoir=make_date(3),
        date_realisation=None, est_dans_delai=None,
        description='Réalisation de l\'arrêté comptable complet du mois de février 2026.',
        responsable='brou.konan', acteurs=['alice.gnagne'],
    ),
    dict(
        titre='Dépôt Balance Générale — Janvier 2026',
        dossier='Balance Générale & Grand Livre',
        statut='cloturee', avancement=100,
        date_ouverture=make_date(-50), date_butoir=make_date(-28),
        date_realisation=make_date(-30), est_dans_delai=True,
        description='Dépôt de la Balance Générale du mois de janvier 2026 sur la plateforme.',
        responsable='alice.gnagne', acteurs=['patrick.koffi'],
    ),
    dict(
        titre='Dépôt Grand Livre — Janvier 2026',
        dossier='Balance Générale & Grand Livre',
        statut='cloturee', avancement=100,
        date_ouverture=make_date(-50), date_butoir=make_date(-28),
        date_realisation=make_date(-29), est_dans_delai=True,
        description='Dépôt du Grand Livre du mois de janvier 2026 sur la plateforme.',
        responsable='alice.gnagne', acteurs=['patrick.koffi'],
    ),
    dict(
        titre='Dépôt Balance Générale — Février 2026',
        dossier='Balance Générale & Grand Livre',
        statut='en_attente', avancement=50,
        date_ouverture=make_date(-15), date_butoir=make_date(2),
        date_realisation=None, est_dans_delai=None,
        description='Dépôt de la Balance Générale de février 2026 — en attente de validation SDCC.',
        responsable='alice.gnagne', acteurs=['brou.konan'],
    ),
    dict(
        titre='Lettrage Compte 401 — Fournisseurs',
        dossier='Lettrage Comptable',
        statut='en_cours', avancement=55,
        date_ouverture=make_date(-12), date_butoir=make_date(-3),  # EN RETARD
        date_realisation=None, est_dans_delai=None,
        description='Opération de lettrage du compte 401 Fournisseurs pour le mois de février.',
        responsable='patrick.koffi', acteurs=['alice.gnagne'],
    ),
    dict(
        titre='Lettrage Compte 411 — Clients',
        dossier='Lettrage Comptable',
        statut='ouverte', avancement=0,
        date_ouverture=make_date(-5), date_butoir=make_date(8),
        date_realisation=None, est_dans_delai=None,
        description='Opération de lettrage du compte 411 Clients pour le mois de février.',
        responsable='patrick.koffi', acteurs=['alice.gnagne'],
    ),
    dict(
        titre='Suivi Projet Comptable SOGEPE T1 2026',
        dossier='Projets Comptables SOGEPE',
        statut='en_cours', avancement=65,
        date_ouverture=make_date(-30), date_butoir=make_date(15),
        date_realisation=None, est_dans_delai=None,
        description='Suivi et reporting des projets comptables en partenariat avec SOGEPE pour le T1 2026.',
        responsable='jean.kouadio', acteurs=['rosine.akre'],
    ),
    dict(
        titre='Réconciliation Trésor — Janvier 2026',
        dossier='Projets Comptables SOGEPE',
        statut='cloturee', avancement=100,
        date_ouverture=make_date(-45), date_butoir=make_date(-20),
        date_realisation=make_date(-22), est_dans_delai=True,
        description='Réconciliation des comptes avec la Direction du Trésor pour janvier 2026.',
        responsable='jean.kouadio', acteurs=['rosine.akre', 'brou.konan'],
    ),
    dict(
        titre='Réconciliation Trésor — Février 2026',
        dossier='Projets Comptables SOGEPE',
        statut='ouverte', avancement=10,
        date_ouverture=make_date(-8), date_butoir=make_date(6),
        date_realisation=None, est_dans_delai=None,
        description='Réconciliation des comptes avec la Direction du Trésor pour février 2026.',
        responsable='jean.kouadio', acteurs=['rosine.akre'],
    ),
]

for a in ACTIVITES:
    dossier = created_dossiers.get(a['dossier'])
    if not dossier:
        print(f"  ✗ Dossier introuvable : {a['dossier']}")
        continue

    if Activite.objects.filter(titre=a['titre'], dossier=dossier).exists():
        print(f"  ~ Existante : {a['titre'][:55]}")
        continue

    resp = created_users[a['responsable']]
    activite = Activite.objects.create(
        titre           = a['titre'],
        description     = a['description'],
        dossier         = dossier,
        section         = dossier.section,
        statut          = a['statut'],
        etat_avancement = a['avancement'],
        date_ouverture  = a['date_ouverture'],
        date_butoir     = a['date_butoir'],
        date_realisation= a['date_realisation'],
        est_dans_delai  = a['est_dans_delai'],
        cloture_le      = timezone.now() if a['statut'] == 'cloturee' else None,
        cloture_par     = resp if a['statut'] == 'cloturee' else None,
        created_by      = resp,
        mois_reference  = a['date_ouverture'].strftime('%Y-%m'),
    )

    # Responsable
    ActiviteActeur.objects.create(activite=activite, utilisateur=resp, role_activite='responsable')

    # Acteurs
    for username in a.get('acteurs', []):
        acteur = created_users.get(username)
        if acteur:
            ActiviteActeur.objects.get_or_create(
                activite=activite, utilisateur=acteur,
                defaults={'role_activite': 'acteur'}
            )

    retard = '' 
    if a['statut'] != 'cloturee' and a['date_butoir'] < today:
        retard = ' ⚠ EN RETARD'
    delai = ''
    if a['est_dans_delai'] is True:
        delai = ' ✓ dans délais'
    elif a['est_dans_delai'] is False:
        delai = ' ✗ hors délais'

    print(f"  + {a['statut'].upper():12} {a['titre'][:45]}{retard}{delai}")

# ── RÉSUMÉ ───────────────────────────────────────────────────────────────────
print("\n=== Résumé ===")
print(f"  Utilisateurs : {Utilisateur.objects.count()}")
print(f"  Dossiers     : {Dossier.objects.count()}")
print(f"  Activités    : {Activite.objects.count()}")

total     = Activite.objects.count()
cloturees = Activite.objects.filter(statut='cloturee').count()
en_retard = Activite.objects.filter(statut__in=['ouverte','en_cours'], date_butoir__lt=today).count()
print(f"\n  Clôturées    : {cloturees} / {total} ({round(cloturees/total*100) if total else 0}%)")
print(f"  En retard    : {en_retard}")
print(f"  Dans délais  : {Activite.objects.filter(est_dans_delai=True).count()} / {cloturees}")
print("\n=== Données de test prêtes ✓ ===")
print("Comptes disponibles (mot de passe : cie2026) :")
print("  admin          → Administrateur")
print("  kouassi.ahou   → Sous-Directeur SDCC")
print("  adjoua.niamke  → Sous-Directeur SDPCC")
print("  bamba.coulibaly → Chef Section Facturation")
print("  brou.konan     → Chef Section Comptabilité")
print("  aya.kone       → Cadre Facturation")
print("  directeur.dfc  → Directeur Financier")
