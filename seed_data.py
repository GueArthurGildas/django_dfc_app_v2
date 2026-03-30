"""
═══════════════════════════════════════════════════════════════════════════════
  CIE MANAGER — Script de données initiales
  DFC / Compagnie Ivoirienne d'Électricité

  Usage :
      python seed_data.py

  Ce script crée (ou met à jour si déjà existant) :
    1. Utilisateurs (DFC, DA, Sous-Directeurs, Chefs de section, Cadres)
    2. PIP (Partenaires Institutionnels et Prestataires)
    3. Comptes comptables affectés aux SD
    4. Dossiers par section
    5. Activités (ouvertes, en cours, clôturées) avec acteurs et documents
    6. Annonce de bienvenue
═══════════════════════════════════════════════════════════════════════════════
"""

import os, sys, django
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from apps.authentication.models import Utilisateur, Role
from apps.organisation.models import (
    SousDirection, Section, UtilisateurSection,
    PIP, CompteComptable, SousDirectionCompte
)
from apps.operations.models import (
    Dossier, Activite, ActiviteActeur,
    TypeDocument, DocumentActivite
)

# ─── Helpers ──────────────────────────────────────────────────────────────────

def log(msg):   print(f"  ✓  {msg}")
def head(msg):  print(f"\n{'─'*60}\n  {msg}\n{'─'*60}")
MOT_DE_PASSE = "cie2026"
today = date.today()


# ══════════════════════════════════════════════════════════════════════════════
# 1. RÔLES (créés par fixtures — on les charge juste)
# ══════════════════════════════════════════════════════════════════════════════
head("1. Chargement des rôles")
roles = {r.code: r for r in Role.objects.all()}
assert roles, "Lancez d'abord : python manage.py loaddata fixtures/roles.json"
log(f"{len(roles)} rôles disponibles")


# ══════════════════════════════════════════════════════════════════════════════
# 2. SOUS-DIRECTIONS & SECTIONS (créées par fixtures)
# ══════════════════════════════════════════════════════════════════════════════
head("2. Chargement des SD et sections")
sds      = {sd.code: sd  for sd in SousDirection.objects.all()}
sections = {s.code:  s   for s in Section.objects.all()}
assert sds, "Lancez d'abord : python manage.py loaddata fixtures/sous_directions.json"
log(f"{len(sds)} sous-directions, {len(sections)} sections")


# ══════════════════════════════════════════════════════════════════════════════
# 3. UTILISATEURS
# ══════════════════════════════════════════════════════════════════════════════
head("3. Création des utilisateurs")

UTILISATEURS = [
    # ── Direction ──────────────────────────────────────────────────────────
    {
        'username':   'directeur.dfc',
        'first_name': 'Kouadio',
        'last_name':  'ASSOUMOU',
        'email':      'k.assoumou@cie.ci',
        'matricule':  'CIE-001',
        'role':       'dfc',
        'section':    None,   # accès global
    },
    {
        'username':   'directeur.adjoint',
        'first_name': 'Adjoua',
        'last_name':  'KOFFI',
        'email':      'a.koffi@cie.ci',
        'matricule':  'CIE-002',
        'role':       'da',
        'section':    None,
    },

    # ── SDCC ───────────────────────────────────────────────────────────────
    {
        'username':   'sd.sdcc',
        'first_name': 'Kouassi',
        'last_name':  'AHOU',
        'email':      'k.ahou@cie.ci',
        'matricule':  'CIE-010',
        'role':       'sd',
        'section':    'SC-COM',
    },
    {
        'username':   'chef.commercial',
        'first_name': 'Bamba',
        'last_name':  'COULIBALY',
        'email':      'b.coulibaly@cie.ci',
        'matricule':  'CIE-011',
        'role':       'chef',
        'section':    'SC-COM',
    },
    {
        'username':   'cadre.commercial1',
        'first_name': 'Fatou',
        'last_name':  'DIALLO',
        'email':      'f.diallo@cie.ci',
        'matricule':  'CIE-012',
        'role':       'cadre',
        'section':    'SC-COM',
    },
    {
        'username':   'chef.facturation',
        'first_name': 'Yao',
        'last_name':  'KOUAME',
        'email':      'y.kouame@cie.ci',
        'matricule':  'CIE-013',
        'role':       'chef',
        'section':    'SC-FACT',
    },
    {
        'username':   'cadre.facturation1',
        'first_name': 'Awa',
        'last_name':  'TRAORE',
        'email':      'a.traore@cie.ci',
        'matricule':  'CIE-014',
        'role':       'cadre',
        'section':    'SC-FACT',
    },
    {
        'username':   'cadre.facturation2',
        'first_name': 'Kofi',
        'last_name':  'MENSAH',
        'email':      'k.mensah@cie.ci',
        'matricule':  'CIE-015',
        'role':       'cadre',
        'section':    'SC-FACT',
    },
    {
        'username':   'chef.recouvrement',
        'first_name': 'Mariam',
        'last_name':  'TOURE',
        'email':      'm.toure@cie.ci',
        'matricule':  'CIE-016',
        'role':       'chef',
        'section':    'SC-RECOV',
    },
    {
        'username':   'cadre.recouvrement1',
        'first_name': 'Ibrahim',
        'last_name':  'OUATTARA',
        'email':      'i.ouattara@cie.ci',
        'matricule':  'CIE-017',
        'role':       'cadre',
        'section':    'SC-RECOV',
    },
    {
        'username':   'maitrise.recouvrement',
        'first_name': 'Aminata',
        'last_name':  'SANGARE',
        'email':      'a.sangare@cie.ci',
        'matricule':  'CIE-018',
        'role':       'maitrise',
        'section':    'SC-RECOV',
    },

    # ── SDPCC ──────────────────────────────────────────────────────────────
    {
        'username':   'sd.sdpcc',
        'first_name': 'Adjoua',
        'last_name':  'NIAMKE',
        'email':      'a.niamke@cie.ci',
        'matricule':  'CIE-020',
        'role':       'sd',
        'section':    'SC-COMPTA',
    },
    {
        'username':   'chef.comptabilite',
        'first_name': 'Brou',
        'last_name':  'KONAN',
        'email':      'b.konan@cie.ci',
        'matricule':  'CIE-021',
        'role':       'chef',
        'section':    'SC-COMPTA',
    },
    {
        'username':   'cadre.comptabilite1',
        'first_name': 'Clarisse',
        'last_name':  'ADOU',
        'email':      'c.adou@cie.ci',
        'matricule':  'CIE-022',
        'role':       'cadre',
        'section':    'SC-COMPTA',
    },
    {
        'username':   'cadre.comptabilite2',
        'first_name': 'Mathieu',
        'last_name':  'YOBOUE',
        'email':      'm.yoboue@cie.ci',
        'matricule':  'CIE-023',
        'role':       'cadre',
        'section':    'SC-COMPTA',
    },
    {
        'username':   'cadre.comptabilite3',
        'first_name': 'Sylvie',
        'last_name':  'KONE',
        'email':      's.kone@cie.ci',
        'matricule':  'CIE-024',
        'role':       'cadre',
        'section':    'SC-COMPTA',
    },
    {
        'username':   'chef.projets',
        'first_name': 'Alexis',
        'last_name':  'GBAGBO',
        'email':      'a.gbagbo@cie.ci',
        'matricule':  'CIE-025',
        'role':       'chef',
        'section':    'SC-PROJ',
    },
    {
        'username':   'cadre.projets1',
        'first_name': 'Rachel',
        'last_name':  'DOFFOU',
        'email':      'r.doffou@cie.ci',
        'matricule':  'CIE-026',
        'role':       'cadre',
        'section':    'SC-PROJ',
    },
    {
        'username':   'cadre.projets2',
        'first_name': 'Emmanuel',
        'last_name':  'AKRE',
        'email':      'e.akre@cie.ci',
        'matricule':  'CIE-027',
        'role':       'cadre',
        'section':    'SC-PROJ',
    },
]

utilisateurs = {}
for u in UTILISATEURS:
    obj, created = Utilisateur.objects.get_or_create(
        username=u['username'],
        defaults={
            'first_name':   u['first_name'],
            'last_name':    u['last_name'],
            'email':        u['email'],
            'matricule':    u['matricule'],
            'role':         roles[u['role']],
            'est_actif_cie':True,
            'is_active':    True,
        }
    )
    if created:
        obj.set_password(MOT_DE_PASSE)
        obj.save()
        log(f"Créé : {obj.nom_complet} ({u['role']})")
    else:
        log(f"Existe : {obj.nom_complet}")

    utilisateurs[u['username']] = obj

    # Affecter à la section
    if u['section'] and u['section'] in sections:
        UtilisateurSection.objects.get_or_create(
            utilisateur=obj,
            section=sections[u['section']],
            defaults={'est_principale': True}
        )


# ══════════════════════════════════════════════════════════════════════════════
# 4. PIP
# ══════════════════════════════════════════════════════════════════════════════
head("4. Création des PIP")

PIPS = [
    # SDCC
    {'code': 'SOPIE',   'libelle': 'Société de Gestion du Patrimoine du Secteur Électricité', 'email': 'contact@sopie.ci',    'sd': 'SDCC'},
    {'code': 'ANARE',   'libelle': 'Autorité Nationale de Régulation du Secteur Électricité', 'email': 'info@anare.ci',       'sd': 'SDCC'},
    {'code': 'MINEE',   'libelle': "Ministère des Mines, du Pétrole et de l'Énergie",         'email': 'dg@energie.gouv.ci',  'sd': 'SDCC'},
    {'code': 'DGI',     'libelle': 'Direction Générale des Impôts',                           'email': 'contact@dgi.ci',      'sd': 'SDCC'},
    # SDPCC
    {'code': 'TRESOR',  'libelle': 'Direction Générale du Trésor et de la Comptabilité',      'email': 'tresor@finances.ci',  'sd': 'SDPCC'},
    {'code': 'BCEAO',   'libelle': "Banque Centrale des États de l'Afrique de l'Ouest",       'email': 'info@bceao.int',      'sd': 'SDPCC'},
    {'code': 'BICICI',  'libelle': "Banque Internationale pour le Commerce et l'Industrie",  'email': 'contact@bicici.ci',   'sd': 'SDPCC'},
    {'code': 'SGBCI',   'libelle': 'Société Générale de Banques en Côte d\'Ivoire',           'email': 'info@sgbci.ci',       'sd': 'SDPCC'},
    {'code': 'PWC',     'libelle': 'PricewaterhouseCoopers Côte d\'Ivoire',                   'email': 'abidjan@pwc.com',     'sd': 'SDPCC'},
]

for p in PIPS:
    obj, created = PIP.objects.get_or_create(
        code=p['code'],
        defaults={
            'libelle':        p['libelle'],
            'email':          p['email'],
            'sous_direction': sds[p['sd']],
            'actif':          True,
        }
    )
    log(f"{'Créé' if created else 'Existe'} : PIP {obj.code}")


# ══════════════════════════════════════════════════════════════════════════════
# 5. COMPTES COMPTABLES → SD
# ══════════════════════════════════════════════════════════════════════════════
head("5. Affectation des comptes comptables aux SD")

COMPTES_SD = {
    'SDCC': ['411', '411100', '411200', '411300', '411400' if False else '416',
             '4428', '706', '706100', '706200', '706300', '706400', '701', '570'],
    'SDPCC': ['401', '512', '421', '161', '185', '231', '445',
              '486', '487', '706', '701', '467'],
}

comptes_map = {c.numero: c for c in CompteComptable.objects.all()}

for sd_code, numeros in COMPTES_SD.items():
    sd = sds[sd_code]
    for num in numeros:
        c = comptes_map.get(num)
        if c:
            SousDirectionCompte.objects.get_or_create(
                sous_direction=sd, compte=c,
                defaults={'note': 'Affecté par seed'}
            )
            log(f"{sd_code} ← {c.numero} {c.libelle[:40]}")


# ══════════════════════════════════════════════════════════════════════════════
# 6. DOSSIERS
# ══════════════════════════════════════════════════════════════════════════════
head("6. Création des dossiers")

DOSSIERS = [
    # ── SDCC / SC-COM ──────────────────────────────────────────────────────
    {'titre': 'Gestion de la Clientèle Ordinaire',
     'description': 'Suivi et gestion des clients BT et MT ordinaires',
     'section': 'SC-COM', 'responsable': 'chef.commercial'},

    {'titre': 'Programme Électricité Pour Tous (PEPT)',
     'description': 'Suivi des abonnés PEPT, gestion des connexions et paiements',
     'section': 'SC-COM', 'responsable': 'chef.commercial'},

    {'titre': 'Smart Vending — Gestion Prépayée',
     'description': 'Suivi des compteurs prépayés et vente de crédit énergie',
     'section': 'SC-COM', 'responsable': 'chef.commercial'},

    # ── SDCC / SC-FACT ─────────────────────────────────────────────────────
    {'titre': 'Facturation Mensuelle BT/MT',
     'description': 'Production et édition des factures mensuelles clients',
     'section': 'SC-FACT', 'responsable': 'chef.facturation'},

    {'titre': 'Arrêtés Comptables Mensuels',
     'description': 'Préparation et validation des arrêtés T1 à T4',
     'section': 'SC-FACT', 'responsable': 'chef.facturation'},

    # ── SDCC / SC-RECOV ────────────────────────────────────────────────────
    {'titre': 'Recouvrement Clients Ordinaires',
     'description': 'Suivi des impayés et actions de recouvrement BT/MT',
     'section': 'SC-RECOV', 'responsable': 'chef.recouvrement'},

    {'titre': 'Gestion des Contentieux',
     'description': 'Dossiers contentieux et provisions pour créances douteuses',
     'section': 'SC-RECOV', 'responsable': 'chef.recouvrement'},

    # ── SDPCC / SC-COMPTA ──────────────────────────────────────────────────
    {'titre': 'Comptabilité Générale',
     'description': 'Tenue de la comptabilité générale — Balance, Grand Livre, Journaux',
     'section': 'SC-COMPTA', 'responsable': 'chef.comptabilite'},

    {'titre': 'Trésorerie et Rapprochements Bancaires',
     'description': 'Gestion des flux de trésorerie et rapprochements mensuels',
     'section': 'SC-COMPTA', 'responsable': 'chef.comptabilite'},

    {'titre': 'Fiscalité et Déclarations',
     'description': 'TVA, IS, déclarations fiscales et relations DGI',
     'section': 'SC-COMPTA', 'responsable': 'chef.comptabilite'},

    # ── SDPCC / SC-PROJ ────────────────────────────────────────────────────
    {'titre': 'Projets d\'Extension Réseau',
     'description': 'Suivi financier et comptable des projets d\'extension réseau électrique',
     'section': 'SC-PROJ', 'responsable': 'chef.projets'},

    {'titre': 'Fonds de Concours et Subventions',
     'description': 'Gestion des fonds reçus de l\'État et des bailleurs (compte 185)',
     'section': 'SC-PROJ', 'responsable': 'chef.projets'},
]

dossiers = {}
for d in DOSSIERS:
    obj, created = Dossier.objects.get_or_create(
        titre=d['titre'],
        section=sections[d['section']],
        defaults={
            'description': d['description'],
            'responsable': utilisateurs[d['responsable']],
            'est_actif':   True,
        }
    )
    dossiers[d['titre']] = obj
    log(f"{'Créé' if created else 'Existe'} : {obj.titre[:50]}")


# ══════════════════════════════════════════════════════════════════════════════
# 7. ACTIVITÉS
# ══════════════════════════════════════════════════════════════════════════════
head("7. Création des activités")

# Charger les types de documents
tdocs = {t.code: t for t in TypeDocument.objects.all()}

def creer_activite(data, responsable_username, acteurs_usernames, docs_codes):
    """Crée une activité avec ses acteurs et documents."""
    dossier = dossiers[data['dossier']]
    obj, created = Activite.objects.get_or_create(
        titre=data['titre'],
        dossier=dossier,
        defaults={
            'description':     data.get('description', ''),
            'type_activite':   data.get('type_activite', 'mensuelle'),
            'statut':          data.get('statut', 'en_cours'),
            'section':         dossier.section,
            'date_ouverture':  data['date_ouverture'],
            'date_butoir':     data['date_butoir'],
            'etat_avancement': data.get('avancement', 0),
            'est_kpi':         data.get('est_kpi', False),
            'est_arrete':      data.get('est_arrete', False),
            'mois_reference':  data.get('mois_ref', today.strftime('%Y-%m')),
            'created_by':      utilisateurs.get(responsable_username),
        }
    )
    if created:
        # Responsable
        ActiviteActeur.objects.get_or_create(
            activite=obj,
            utilisateur=utilisateurs[responsable_username],
            defaults={'role_activite': 'responsable', 'peut_recevoir_mail': True}
        )
        # Acteurs
        for u in acteurs_usernames:
            if u in utilisateurs:
                ActiviteActeur.objects.get_or_create(
                    activite=obj,
                    utilisateur=utilisateurs[u],
                    defaults={'role_activite': 'acteur', 'peut_recevoir_mail': True}
                )
        # Documents
        for code in docs_codes:
            if code in tdocs:
                DocumentActivite.objects.get_or_create(
                    activite=obj,
                    type_document=tdocs[code],
                    defaults={'etat': 'non_commence'}
                )
        log(f"Créée : {obj.titre[:55]}")
    else:
        log(f"Existe : {obj.titre[:55]}")
    return obj


# ── Mois de référence ─────────────────────────────────────────────────────────
m0 = today.replace(day=1)                           # Mois courant
m1 = (m0 - timedelta(days=1)).replace(day=1)        # Mois précédent
m2 = (m1 - timedelta(days=1)).replace(day=1)        # 2 mois avant
fin_m0 = (m0 + timedelta(days=32)).replace(day=1) - timedelta(days=1)
fin_m1 = m0 - timedelta(days=1)
fin_m2 = m1 - timedelta(days=1)

ACTIVITES = [

    # ── Balance Générale (mensuelle récurrente) ───────────────────────────
    {
        'data': {
            'titre':         f"Balance Générale — {m1.strftime('%B %Y')}",
            'description':   'Production et validation de la Balance Générale mensuelle',
            'dossier':       'Arrêtés Comptables Mensuels',
            'type_activite': 'mensuelle',
            'statut':        'cloturee',
            'date_ouverture':m1,
            'date_butoir':   fin_m1,
            'avancement':    100,
            'est_arrete':    True,
            'est_kpi':       True,
            'mois_ref':      m1.strftime('%Y-%m'),
        },
        'responsable':  'chef.facturation',
        'acteurs':      ['cadre.facturation1', 'cadre.facturation2', 'chef.comptabilite'],
        'docs':         ['BAL-GEN', 'BAL-AUX', 'GRAND-LIV'],
    },
    {
        'data': {
            'titre':         f"Balance Générale — {m0.strftime('%B %Y')}",
            'description':   'Production et validation de la Balance Générale mensuelle',
            'dossier':       'Arrêtés Comptables Mensuels',
            'type_activite': 'mensuelle',
            'statut':        'en_cours',
            'date_ouverture':m0,
            'date_butoir':   fin_m0,
            'avancement':    45,
            'est_arrete':    True,
            'est_kpi':       True,
            'mois_ref':      m0.strftime('%Y-%m'),
        },
        'responsable':  'chef.facturation',
        'acteurs':      ['cadre.facturation1', 'cadre.facturation2', 'chef.comptabilite'],
        'docs':         ['BAL-GEN', 'BAL-AUX', 'GRAND-LIV', 'RAPP-RECAP'],
    },

    # ── Grand Livre ───────────────────────────────────────────────────────
    {
        'data': {
            'titre':         f"Grand Livre Auxiliaire — {m0.strftime('%B %Y')}",
            'description':   'Production du Grand Livre auxiliaire clients et fournisseurs',
            'dossier':       'Comptabilité Générale',
            'type_activite': 'mensuelle',
            'statut':        'en_cours',
            'date_ouverture':m0,
            'date_butoir':   fin_m0,
            'avancement':    30,
            'est_arrete':    True,
            'mois_ref':      m0.strftime('%Y-%m'),
        },
        'responsable':  'chef.comptabilite',
        'acteurs':      ['cadre.comptabilite1', 'cadre.comptabilite2'],
        'docs':         ['GRAND-LIV', 'GRAND-LIV-AUX', 'BAL-AUX'],
    },

    # ── Facturation mensuelle ─────────────────────────────────────────────
    {
        'data': {
            'titre':         f"Facturation BT/MT — {m1.strftime('%B %Y')}",
            'description':   'Production des factures clients Basse et Moyenne Tension',
            'dossier':       'Facturation Mensuelle BT/MT',
            'type_activite': 'mensuelle',
            'statut':        'cloturee',
            'date_ouverture':m1,
            'date_butoir':   fin_m1,
            'avancement':    100,
            'est_kpi':       True,
            'mois_ref':      m1.strftime('%Y-%m'),
        },
        'responsable':  'chef.facturation',
        'acteurs':      ['cadre.facturation1', 'cadre.facturation2'],
        'docs':         ['FACT-CLI', 'RAPP-FACT', 'SYNTH-CA'],
    },
    {
        'data': {
            'titre':         f"Facturation BT/MT — {m0.strftime('%B %Y')}",
            'description':   'Production des factures clients Basse et Moyenne Tension',
            'dossier':       'Facturation Mensuelle BT/MT',
            'type_activite': 'mensuelle',
            'statut':        'en_cours',
            'date_ouverture':m0,
            'date_butoir':   fin_m0,
            'avancement':    60,
            'est_kpi':       True,
            'mois_ref':      m0.strftime('%Y-%m'),
        },
        'responsable':  'chef.facturation',
        'acteurs':      ['cadre.facturation1', 'cadre.facturation2'],
        'docs':         ['FACT-CLI', 'RAPP-FACT', 'SYNTH-CA', 'TAB-BORD'],
    },

    # ── Facturation PEPT ─────────────────────────────────────────────────
    {
        'data': {
            'titre':         f"Facturation PEPT — {m0.strftime('%B %Y')}",
            'description':   'Facturation et suivi des abonnés Programme Électricité Pour Tous',
            'dossier':       'Programme Électricité Pour Tous (PEPT)',
            'type_activite': 'mensuelle',
            'statut':        'ouverte',
            'date_ouverture':m0,
            'date_butoir':   fin_m0,
            'avancement':    10,
            'mois_ref':      m0.strftime('%Y-%m'),
        },
        'responsable':  'chef.commercial',
        'acteurs':      ['cadre.commercial1'],
        'docs':         ['FACT-CLI', 'BORD-RECOV', 'RAPP-RECAP'],
    },

    # ── Recouvrement ─────────────────────────────────────────────────────
    {
        'data': {
            'titre':         f"Suivi Recouvrement — {m0.strftime('%B %Y')}",
            'description':   'Relances clients impayés et suivi des encaissements',
            'dossier':       'Recouvrement Clients Ordinaires',
            'type_activite': 'mensuelle',
            'statut':        'en_cours',
            'date_ouverture':m0,
            'date_butoir':   fin_m0,
            'avancement':    55,
            'est_kpi':       True,
            'mois_ref':      m0.strftime('%Y-%m'),
        },
        'responsable':  'chef.recouvrement',
        'acteurs':      ['cadre.recouvrement1', 'maitrise.recouvrement'],
        'docs':         ['SITU-IMPAYES', 'BORD-RECOV', 'RAPP-RECAP'],
    },

    # ── Trésorerie ────────────────────────────────────────────────────────
    {
        'data': {
            'titre':         f"Situation de Trésorerie — {m0.strftime('%B %Y')}",
            'description':   'État hebdomadaire de la trésorerie et rapprochements bancaires',
            'dossier':       'Trésorerie et Rapprochements Bancaires',
            'type_activite': 'mensuelle',
            'statut':        'en_cours',
            'date_ouverture':m0,
            'date_butoir':   today + timedelta(days=5),   # urgent
            'avancement':    70,
            'est_kpi':       True,
            'mois_ref':      m0.strftime('%Y-%m'),
        },
        'responsable':  'chef.comptabilite',
        'acteurs':      ['cadre.comptabilite1', 'cadre.comptabilite3'],
        'docs':         ['SITU-TRESOR', 'RAPP-RECAP'],
    },

    # ── Déclaration TVA (en retard pour tester les alertes) ───────────────
    {
        'data': {
            'titre':         f"Déclaration TVA — {m1.strftime('%B %Y')}",
            'description':   'Préparation et dépôt de la déclaration de TVA mensuelle à la DGI',
            'dossier':       'Fiscalité et Déclarations',
            'type_activite': 'mensuelle',
            'statut':        'en_cours',
            'date_ouverture':m1,
            'date_butoir':   today - timedelta(days=3),  # EN RETARD
            'avancement':    80,
            'mois_ref':      m1.strftime('%Y-%m'),
        },
        'responsable':  'chef.comptabilite',
        'acteurs':      ['cadre.comptabilite2', 'cadre.comptabilite3'],
        'docs':         ['NOTE-SYN', 'PV-ARRETE'],
    },

    # ── Projets extension réseau ─────────────────────────────────────────
    {
        'data': {
            'titre':         'Suivi Financier Extension Réseau Yopougon Sud',
            'description':   'Suivi des décaissements et avancement financier du projet Yopougon',
            'dossier':       "Projets d'Extension Réseau",
            'type_activite': 'ponctuelle',
            'statut':        'en_cours',
            'date_ouverture':today - timedelta(days=45),
            'date_butoir':   today + timedelta(days=60),
            'avancement':    35,
        },
        'responsable':  'chef.projets',
        'acteurs':      ['cadre.projets1', 'cadre.projets2', 'chef.comptabilite'],
        'docs':         ['RAPP-RECAP', 'TAB-BORD', 'SITU-TRESOR'],
    },

    # ── Fonds de concours ────────────────────────────────────────────────
    {
        'data': {
            'titre':         'Rapport Fonds de Concours T1 2026',
            'description':   'Rapport semestriel sur les fonds de concours reçus de l\'État',
            'dossier':       'Fonds de Concours et Subventions',
            'type_activite': 'trimestrielle',
            'statut':        'ouverte',
            'date_ouverture':today - timedelta(days=10),
            'date_butoir':   today + timedelta(days=20),
            'avancement':    15,
            'est_kpi':       True,
        },
        'responsable':  'chef.projets',
        'acteurs':      ['cadre.projets1'],
        'docs':         ['RAPP-RECAP', 'NOTE-SYN', 'PV-ARRETE'],
    },

    # ── Smart Vending ────────────────────────────────────────────────────
    {
        'data': {
            'titre':         f"Bilan Smart Vending — {m1.strftime('%B %Y')}",
            'description':   'Analyse des ventes de crédit prépayé et taux d\'utilisation',
            'dossier':       'Smart Vending — Gestion Prépayée',
            'type_activite': 'mensuelle',
            'statut':        'cloturee',
            'date_ouverture':m1,
            'date_butoir':   fin_m1,
            'avancement':    100,
            'mois_ref':      m1.strftime('%Y-%m'),
        },
        'responsable':  'chef.commercial',
        'acteurs':      ['cadre.commercial1'],
        'docs':         ['SYNTH-CA', 'TAB-BORD', 'RAPP-FACT'],
    },

    # ── Contentieux ──────────────────────────────────────────────────────
    {
        'data': {
            'titre':         'Revue Dossiers Contentieux Q1 2026',
            'description':   'Revue trimestrielle des créances douteuses et provisions',
            'dossier':       'Gestion des Contentieux',
            'type_activite': 'trimestrielle',
            'statut':        'en_cours',
            'date_ouverture':today - timedelta(days=20),
            'date_butoir':   today + timedelta(days=10),
            'avancement':    65,
            'est_kpi':       True,
        },
        'responsable':  'chef.recouvrement',
        'acteurs':      ['cadre.recouvrement1'],
        'docs':         ['SITU-IMPAYES', 'NOTE-SYN', 'PV-ARRETE'],
    },
]

for item in ACTIVITES:
    creer_activite(item['data'], item['responsable'], item['acteurs'], item['docs'])


# ══════════════════════════════════════════════════════════════════════════════
# 8. CLÔTURER les activités clôturées avec motif
# ══════════════════════════════════════════════════════════════════════════════
head("8. Finalisation des clôtures")

from apps.operations.services import ActiviteService
admin_user = Utilisateur.objects.filter(is_superuser=True).first()

for a in Activite.objects.filter(statut='cloturee', cloture_par__isnull=True):
    a.cloture_par         = utilisateurs.get('chef.facturation') or admin_user
    a.cloture_le          = timezone.now()
    a.cloture_motif       = 'objectif_atteint'
    a.cloture_commentaire = 'Activité réalisée dans les délais. Documents produits et validés.'
    a.save(update_fields=['cloture_par', 'cloture_le', 'cloture_motif', 'cloture_commentaire'])
    log(f"Clôturée : {a.titre[:50]}")


# ══════════════════════════════════════════════════════════════════════════════
# 9. ANNONCE DE BIENVENUE
# ══════════════════════════════════════════════════════════════════════════════
head("9. Annonce de bienvenue")

from apps.authentication.models import Annonce

annonce, created = Annonce.objects.get_or_create(
    titre="Bienvenue sur CIE Manager",
    defaults={
        'description': (
            "CIE Manager est maintenant opérationnel pour la DFC.\n\n"
            "Vous pouvez dès à présent :\n"
            "• Créer et suivre vos activités par dossier\n"
            "• Consulter les tableaux de bord de votre sous-direction\n"
            "• Dialoguer avec ARIA, votre assistante IA comptable\n"
            "• Recevoir des alertes sur vos activités urgentes\n\n"
            "Bonne utilisation à toutes les équipes !"
        ),
        'date_debut':   timezone.now(),
        'date_fin':     timezone.now() + timedelta(days=7),
        'actif':        True,
        'created_by':   admin_user,
    }
)
log(f"{'Créée' if created else 'Existe'} : Annonce de bienvenue")


# ══════════════════════════════════════════════════════════════════════════════
# RÉSUMÉ
# ══════════════════════════════════════════════════════════════════════════════
print(f"""
{'═'*60}
  SEED TERMINÉ ✓
{'═'*60}
  Utilisateurs : {Utilisateur.objects.filter(est_actif_cie=True).count()}
  PIP          : {PIP.objects.filter(actif=True).count()}
  Dossiers     : {Dossier.objects.filter(est_actif=True).count()}
  Activités    : {Activite.objects.filter(deleted_at__isnull=True).count()}
    • En cours   : {Activite.objects.filter(statut='en_cours').count()}
    • Ouvertes   : {Activite.objects.filter(statut='ouverte').count()}
    • Clôturées  : {Activite.objects.filter(statut='cloturee').count()}
    • En retard  : {Activite.objects.filter(statut__in=['ouverte','en_cours'], date_butoir__lt=today).count()}

  Comptes CIE manager :
{'─'*60}
  admin          / admin123
  directeur.dfc  / {MOT_DE_PASSE}
  directeur.adjoint / {MOT_DE_PASSE}
  sd.sdcc        / {MOT_DE_PASSE}
  sd.sdpcc       / {MOT_DE_PASSE}
  chef.facturation  / {MOT_DE_PASSE}
  chef.comptabilite / {MOT_DE_PASSE}
  cadre.facturation1 / {MOT_DE_PASSE}
  ... (tous les comptes : mot de passe {MOT_DE_PASSE})
{'═'*60}
""")
