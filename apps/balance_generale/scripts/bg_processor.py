"""
Script de traitement de la Balance Générale CIE.
Parse le fichier Excel, calcule les agrégats, détecte les anomalies.
"""
import pandas as pd
import numpy as np
from django.utils import timezone


COLONNES_ATTENDUES = {
    'description':      0,
    'cie_report':       1,
    'cie_periode':      2,
    'cie_exercice':     3,
    'cie_total':        4,
    'sect_report':      5,
    'sect_periode':     6,
    'sect_exercice':    7,
    'sect_total':       8,
    'expl_report':      9,
    'expl_periode':     10,
    'expl_exercice':    11,
    'expl_total':       12,
}

REGLES_ALERTES = {
    # Critiques
    'DESEQUILIBRE_GLOBAL':   'critique',
    'INCOHERENCE_CALCUL':    'critique',
    'CONSOLIDATION_INVALIDE':'critique',
    'TRESORERIE_NEGATIVE':   'critique',
    # Hautes
    'INTERCO_ASYMETRIQUE':   'haute',
    'CAPITAL_DEBITEUR':      'haute',
    'DECOUVERTE_BANCAIRE':   'haute',
    'RUPTURE_RAN':           'haute',
    'COMPTE_130100_NON_SOLDE':'haute',
    # Moyennes
    'VARIATION_BRUTALE':     'moyenne',
    'COMPTE_ATTENTE':        'moyenne',
    'IMMOB_EN_COURS_BLOQUEE':'moyenne',
    'DSO_ELEVE':             'moyenne',
}


def _val(v):
    """Convertit une valeur en entier FCFA (0 si vide/NaN)."""
    if pd.isna(v) or v == '' or v is None:
        return 0
    try:
        return int(float(str(v).replace(' ', '').replace('\xa0', '')))
    except (ValueError, TypeError):
        return 0


def _detecter_debut_donnees(df_brut):
    """Détecte dynamiquement la ligne de début des données."""
    for i, row in df_brut.iterrows():
        premiere = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ''
        if premiere and premiere[0].isdigit() and len(premiere) >= 6:
            return i
    return 3  # fallback


def _sens_normal(num_compte):
    """Détermine le sens normal d'un compte selon SYSCOHADA."""
    classe = int(str(num_compte).strip()[0]) if str(num_compte).strip() else 0
    if classe in (1, 2, 4, 5):
        return 'C' if classe in (1,) else 'D'
    elif classe in (6,):
        return 'D'
    elif classe in (7,):
        return 'C'
    return 'D'


def traiter_balance(bg_import, fichier_path):
    """
    Point d'entrée principal.
    Lit le fichier Excel, crée les BgLigne, BgAgregat, BgAlerte.
    Retourne (nb_lignes, nb_anomalies, erreur).
    """
    from apps.balance_generale.models import BgLigne, BgAgregat, BgAlerte, BgComparaison

    try:
        # ── Lecture Excel ───────────────────────────────────────────────────
        df_brut = pd.read_excel(fichier_path, header=None, dtype=str)

        # Extraire exercice et période depuis l'entête
        try:
            ligne0 = str(df_brut.iloc[0, 0])
            if 'Exercice' in ligne0 or len(ligne0) <= 4:
                bg_import.exercice = int(ligne0.strip()) if ligne0.strip().isdigit() else bg_import.exercice
        except Exception:
            pass

        # Trouver la ligne de début des données
        debut = _detecter_debut_donnees(df_brut)
        df = df_brut.iloc[debut:].copy()
        df.columns = range(len(df.columns))
        df = df.dropna(subset=[0], how='all')

        # ── Traitement ligne par ligne ──────────────────────────────────────
        lignes_creees = []
        nb_lignes = 0

        for _, row in df.iterrows():
            description = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ''
            if not description or description.lower() in ('nan', 'total', 'sous-total'):
                continue

            # Extraire num_compte et intitulé
            parts      = description.split(None, 1)
            num_compte = parts[0].strip() if parts else description
            intitule   = parts[1].strip() if len(parts) > 1 else ''

            # Accepter les comptes analytiques format "603310.512"
            # Extraire la partie principale avant le point
            num_base = num_compte.split('.')[0]
            if not num_base or not num_base[0].isdigit():
                continue
            # Garder le numéro complet (avec sous-compte si présent)
            classe = int(num_base[0])
            is_interco = num_compte.startswith('185')
            is_ran     = num_compte.startswith('121')

            # iloc index (0-based) — colonnes Excel :
            # CIE        : D(3)=Report, E(4)=Période, F(5)=Exercice, G(6)=Total
            # Secteur    : I(8)=Report, J(9)=Période, K(10)=Exercice, L(11)=Total
            # Exploitant : O(14)=Report, P(15)=Période, Q(16)=Exercice, R(17)=Total
            entites = [
                ('CIE',         3,  4,  5,  6),
                ('Secteur',     8,  9, 10, 11),
                ('Exploitant', 14, 15, 16, 17),
            ]

            for entite_nom, col_rep, col_per, col_exc, col_tot in entites:
                try:
                    report    = _val(row.iloc[col_rep])
                    periode   = _val(row.iloc[col_per])
                    exercice  = _val(row.iloc[col_exc])
                    total     = _val(row.iloc[col_tot])
                except IndexError:
                    continue

                if report == 0 and periode == 0 and exercice == 0 and total == 0:
                    continue

                lignes_creees.append(BgLigne(
                    bg_import        = bg_import,
                    num_compte       = num_compte,
                    intitule         = intitule,
                    classe           = classe,
                    entite           = entite_nom,
                    report           = report,
                    activite_periode = periode,
                    activite_exercice= exercice,
                    total            = total,
                    is_interco       = is_interco,
                    is_ran           = is_ran,
                    sens_normal      = _sens_normal(num_compte),
                ))
            nb_lignes += 1

        BgLigne.objects.bulk_create(lignes_creees, batch_size=500)

        # ── Calcul des agrégats ─────────────────────────────────────────────
        _calculer_agregats(bg_import)

        # ── Détection des anomalies ─────────────────────────────────────────
        nb_anomalies = _detecter_anomalies(bg_import)

        return nb_lignes, nb_anomalies, None

    except Exception as e:
        import traceback
        return 0, 0, traceback.format_exc()


def _calculer_agregats(bg_import):
    """Calcule les agrégats financiers par classe et entité."""
    from apps.balance_generale.models import BgLigne, BgAgregat
    from django.db.models import Sum

    agregats = []
    for entite in ('CIE', 'Secteur', 'Exploitant'):
        for classe in range(1, 9):
            qs = BgLigne.objects.filter(bg_import=bg_import, entite=entite, classe=classe)
            if not qs.exists():
                continue
            agg = qs.aggregate(
                r=Sum('report'), p=Sum('activite_periode'),
                e=Sum('activite_exercice'), t=Sum('total')
            )
            agregats.append(BgAgregat(
                bg_import       = bg_import,
                type_agregat    = 'classe',
                entite          = entite,
                libelle         = f"Classe {classe}",
                classe          = classe,
                valeur_report   = agg['r'] or 0,
                valeur_periode  = agg['p'] or 0,
                valeur_exercice = agg['e'] or 0,
                valeur_total    = agg['t'] or 0,
            ))

    # KPIs spéciaux
    for entite in ('CIE', 'Exploitant'):
        # Chiffre d'affaires (cl.7)
        ca = BgLigne.objects.filter(bg_import=bg_import, entite=entite, classe=7).aggregate(t=Sum('total'))['t'] or 0
        # Charges (cl.6)
        charges = BgLigne.objects.filter(bg_import=bg_import, entite=entite, classe=6).aggregate(t=Sum('total'))['t'] or 0
        # Résultat net
        resultat = abs(ca) - abs(charges)
        # Trésorerie (cl.5)
        tresorerie = BgLigne.objects.filter(bg_import=bg_import, entite=entite, classe=5).aggregate(t=Sum('total'))['t'] or 0
        # Créances clients (411)
        clients = BgLigne.objects.filter(bg_import=bg_import, entite=entite, num_compte__startswith='411').aggregate(t=Sum('total'))['t'] or 0

        for libelle, valeur in [
            ("Chiffre d'affaires", abs(ca)),
            ("Charges totales", abs(charges)),
            ("Résultat net estimé", resultat),
            ("Trésorerie nette", tresorerie),
            ("Créances clients (411)", clients),
        ]:
            agregats.append(BgAgregat(
                bg_import=bg_import, type_agregat='kpi',
                entite=entite, libelle=libelle,
                valeur_total=valeur,
            ))

    BgAgregat.objects.bulk_create(agregats, batch_size=200)


def _detecter_anomalies(bg_import):
    """Détecte les anomalies comptables et crée les BgAlerte."""
    from apps.balance_generale.models import BgLigne, BgAlerte
    from django.db.models import Sum

    alertes = []

    def alerte(niveau, code, message, compte='', entite='', valeur=None):
        alertes.append(BgAlerte(
            bg_import=bg_import, niveau=niveau,
            code_regle=code, message=message,
            num_compte=compte, entite=entite,
            valeur_constatee=valeur,
        ))

    # ── CRITIQUES ─────────────────────────────────────────────────────────

    # 1. Déséquilibre global Exploitant
    expl = BgLigne.objects.filter(bg_import=bg_import, entite='Exploitant')
    debits  = expl.filter(total__gt=0).aggregate(s=Sum('total'))['s'] or 0
    credits = expl.filter(total__lt=0).aggregate(s=Sum('total'))['s'] or 0
    ecart   = debits + credits
    if abs(ecart) > 1:
        alerte('critique', 'DESEQUILIBRE_GLOBAL',
               f"Balance déséquilibrée : écart de {ecart:,} FCFA. Arrêté impossible.",
               valeur=ecart)

    # 2. Incoherence calcul ligne (Report + Act.Exercice != Total)
    for ligne in BgLigne.objects.filter(bg_import=bg_import, entite='Exploitant')[:500]:
        attendu = ligne.report + ligne.activite_exercice
        if abs(attendu - ligne.total) > 1:
            alerte('critique', 'INCOHERENCE_CALCUL',
                   f"Calcul incorrect : {ligne.report} + {ligne.activite_exercice} ≠ {ligne.total}",
                   compte=ligne.num_compte, entite=ligne.entite,
                   valeur=ligne.total - attendu)
            if len(alertes) > 20:
                break

    # 3. Consolidation invalide (Exploitant ≠ CIE + Secteur)
    for classe in range(1, 8):
        cie_tot  = BgLigne.objects.filter(bg_import=bg_import, entite='CIE',        classe=classe).aggregate(s=Sum('total'))['s'] or 0
        sect_tot = BgLigne.objects.filter(bg_import=bg_import, entite='Secteur',    classe=classe).aggregate(s=Sum('total'))['s'] or 0
        expl_tot = BgLigne.objects.filter(bg_import=bg_import, entite='Exploitant', classe=classe).aggregate(s=Sum('total'))['s'] or 0
        ecart    = expl_tot - (cie_tot + sect_tot)
        if abs(ecart) > 100:
            alerte('critique', 'CONSOLIDATION_INVALIDE',
                   f"Classe {classe} : Exploitant ({expl_tot:,}) ≠ CIE ({cie_tot:,}) + Secteur ({sect_tot:,}). Écart = {ecart:,} FCFA.",
                   valeur=ecart)

    # 4. Trésorerie négative
    tresorerie = BgLigne.objects.filter(bg_import=bg_import, entite='Exploitant', classe=5).aggregate(s=Sum('total'))['s'] or 0
    if tresorerie < 0:
        alerte('critique', 'TRESORERIE_NEGATIVE',
               f"Trésorerie nette négative : {tresorerie:,} FCFA.",
               valeur=tresorerie)

    # ── HAUTES ────────────────────────────────────────────────────────────

    # 5. Interco asymétrique (185xxx CIE + Secteur ≠ 0)
    interco_cie  = BgLigne.objects.filter(bg_import=bg_import, entite='CIE',     is_interco=True).aggregate(s=Sum('total'))['s'] or 0
    interco_sect = BgLigne.objects.filter(bg_import=bg_import, entite='Secteur', is_interco=True).aggregate(s=Sum('total'))['s'] or 0
    ecart_interco = interco_cie + interco_sect
    if abs(ecart_interco) > 1:
        alerte('haute', 'INTERCO_ASYMETRIQUE',
               f"Comptes 185xxx non équilibrés : CIE={interco_cie:,}, Secteur={interco_sect:,}, Écart={ecart_interco:,} FCFA.",
               valeur=ecart_interco)

    # 6. Capital social débiteur
    capital = BgLigne.objects.filter(bg_import=bg_import, entite='CIE', num_compte__startswith='101').aggregate(s=Sum('total'))['s'] or 0
    if capital > 0:
        alerte('haute', 'CAPITAL_DEBITEUR',
               f"Capital social débiteur : {capital:,} FCFA — anomalie comptable.",
               compte='101xxx', valeur=capital)

    # 7. Découverte bancaire
    for compte_prefix in ('521', '531'):
        val = BgLigne.objects.filter(bg_import=bg_import, entite='Exploitant', num_compte__startswith=compte_prefix).aggregate(s=Sum('total'))['s'] or 0
        if val > 0:
            alerte('haute', 'DECOUVERTE_BANCAIRE',
                   f"Découverte bancaire non déclarée sur {compte_prefix}xxx : {val:,} FCFA.",
                   compte=f"{compte_prefix}xxx", valeur=val)

    # 8. Compte 580 non soldé
    solde_580 = BgLigne.objects.filter(bg_import=bg_import, entite='Exploitant', num_compte__startswith='580').aggregate(s=Sum('total'))['s'] or 0
    if abs(solde_580) > 1:
        alerte('haute', 'VIREMENT_FONDS_OUVERT',
               f"Compte 580 non soldé : {solde_580:,} FCFA. Doit être soldé à la clôture.",
               compte='580', valeur=solde_580)

    # ── MOYENNES ──────────────────────────────────────────────────────────

    # 9. Comptes d'attente 471/478
    for prefix in ('471', '478'):
        val = BgLigne.objects.filter(bg_import=bg_import, entite='Exploitant', num_compte__startswith=prefix).aggregate(s=Sum('total'))['s'] or 0
        if abs(val) > 1:
            alerte('moyenne', 'COMPTE_ATTENTE',
                   f"Compte d'attente {prefix}xxx avec solde persistant : {val:,} FCFA.",
                   compte=f"{prefix}xxx", valeur=val)

    # 10. Immobilisations en cours (231xxx)
    immo = BgLigne.objects.filter(bg_import=bg_import, entite='Exploitant', num_compte__startswith='231').aggregate(s=Sum('total'))['s'] or 0
    if immo > 0:
        alerte('moyenne', 'IMMOB_EN_COURS',
               f"Immobilisations en cours : {immo:,} FCFA — à surveiller si > 365 jours.",
               compte='231xxx', valeur=immo)

    BgAlerte.objects.bulk_create(alertes, batch_size=100)
    return len(alertes)
