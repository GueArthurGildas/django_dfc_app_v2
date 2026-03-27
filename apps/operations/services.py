"""
ActiviteService — logique métier centralisée pour les activités.
Toute modification de statut/avancement DOIT passer par ce service.
"""
from django.utils import timezone
from .models import Activite, ActiviteActeur, CommentaireActivite, HistoriqueActivite, AlerteMail
from .notifications import AlerteMailService


class ActiviteService:

    @staticmethod
    def creer(data: dict, user) -> Activite:
        acteurs_ids      = data.pop('acteurs_ids', [])
        responsables_ids = data.pop('responsables_ids', [])
        pips_ids         = data.pop('pips_ids', [])
        data_pre = {'acteurs_ids': acteurs_ids, 'responsables_ids': responsables_ids}
        data['created_by'] = user
        data['statut']     = 'ouverte'
        # Si section absente, la récupérer depuis le dossier
        if 'section' not in data and 'dossier' in data:
            data['section'] = data['dossier'].section
        data['mois_reference'] = data.get('date_ouverture', timezone.now().date()).strftime('%Y-%m')

        activite = Activite.objects.create(**data)

        # Responsables explicitement désignés
        responsables_ids = data_pre.get('responsables_ids', [])
        for uid in responsables_ids:
            ActiviteActeur.objects.get_or_create(
                activite=activite, utilisateur_id=uid,
                defaults={'role_activite': 'responsable', 'peut_recevoir_mail': True}
            )
        # Si aucun responsable désigné → le créateur devient responsable par défaut
        if not responsables_ids:
            ActiviteActeur.objects.get_or_create(
                activite=activite, utilisateur=user,
                defaults={'role_activite': 'responsable'}
            )
        # Acteurs
        for uid in acteurs_ids:
            ActiviteActeur.objects.get_or_create(
                activite=activite, utilisateur_id=uid,
                defaults={'role_activite': 'acteur', 'peut_recevoir_mail': True}
            )
        # PIP
        if pips_ids:
            from .models import ActivitePIP
            from apps.organisation.models import PIP
            for pid in pips_ids:
                ActivitePIP.objects.get_or_create(activite=activite, pip_id=pid)

        HistoriqueActivite.objects.create(
            activite=activite, utilisateur=user,
            champ_modifie='création', ancienne_valeur='', nouvelle_valeur='Activité créée'
        )
        AlerteMailService.envoyer_ouverture(activite)
        return activite

    @staticmethod
    def mettre_a_jour(activite: Activite, statut: str, avancement: int, contenu: str, user, type_comment='mise_a_jour') -> Activite:
        ancien_statut     = activite.statut
        ancien_avancement = activite.etat_avancement

        activite.statut          = statut
        activite.etat_avancement = avancement
        activite.save(update_fields=['statut', 'etat_avancement', 'updated_at'])

        CommentaireActivite.objects.create(
            activite=activite, auteur=user,
            type_comment=type_comment, contenu=contenu, avancement=avancement
        )
        if ancien_statut != statut:
            HistoriqueActivite.objects.create(
                activite=activite, utilisateur=user,
                champ_modifie='statut',
                ancienne_valeur=ancien_statut, nouvelle_valeur=statut
            )
        if ancien_avancement != avancement:
            HistoriqueActivite.objects.create(
                activite=activite, utilisateur=user,
                champ_modifie='avancement',
                ancienne_valeur=str(ancien_avancement), nouvelle_valeur=str(avancement)
            )
        return activite

    @staticmethod
    def clore(activite: Activite, commentaire: str, user, motif: str = 'objectif_atteint', date_realisation=None) -> Activite:
        from datetime import date as date_type
        today = date_realisation or timezone.now().date()
        activite.statut              = 'cloturee'
        activite.etat_avancement     = 100
        activite.date_realisation    = today
        activite.est_dans_delai      = activite.calculer_est_dans_delai()
        activite.cloture_par         = user
        activite.cloture_le          = timezone.now()
        activite.cloture_motif       = motif
        activite.cloture_commentaire = commentaire
        activite.save(update_fields=[
            'statut', 'etat_avancement', 'date_realisation', 'est_dans_delai',
            'cloture_par', 'cloture_le', 'cloture_motif', 'cloture_commentaire', 'updated_at'
        ])
        motif_label = dict(activite.MOTIFS_CLOTURE).get(motif, motif)
        CommentaireActivite.objects.create(
            activite=activite, auteur=user, type_comment='cloture',
            contenu=f"[{motif_label}] {commentaire}", avancement=100
        )
        HistoriqueActivite.objects.create(
            activite=activite, utilisateur=user,
            champ_modifie='statut', ancienne_valeur='en_cours', nouvelle_valeur='cloturee'
        )
        AlerteMailService.envoyer_cloture(activite)
        return activite

    @staticmethod
    def reporter_date(activite: Activite, nouvelle_date, motif: str, user) -> Activite:
        ancienne_date = activite.date_intermediaire
        if not activite.date_intermediaire_init:
            activite.date_intermediaire_init = ancienne_date
        activite.date_intermediaire = nouvelle_date
        activite.nb_reports += 1
        activite.save(update_fields=['date_intermediaire', 'date_intermediaire_init', 'nb_reports', 'updated_at'])

        HistoriqueActivite.objects.create(
            activite=activite, utilisateur=user,
            champ_modifie='date_intermediaire',
            ancienne_valeur=str(ancienne_date), nouvelle_valeur=str(nouvelle_date) + f' (motif: {motif})'
        )
        AlerteMailService.envoyer_alerte_report(activite, motif)
        return activite

    @staticmethod
    def cloner(activite: Activite) -> Activite:
        """Clone une activité mensuelle pour le mois suivant"""
        from datetime import date
        import calendar
        today = date.today()
        # Nouveau mois
        if today.month == 12:
            new_month, new_year = 1, today.year + 1
        else:
            new_month, new_year = today.month + 1, today.year

        mois_ref = f"{new_year}-{new_month:02d}"
        # Vérifier qu'il n'existe pas déjà
        if Activite.objects.filter(activite_parente=activite, mois_reference=mois_ref).exists():
            return None

        last_day = calendar.monthrange(new_year, new_month)[1]
        new_butoir = activite.date_butoir.replace(year=new_year, month=new_month,
                                                   day=min(activite.date_butoir.day, last_day))
        clone = Activite.objects.create(
            titre           = activite.titre,
            description     = activite.description,
            type_activite   = activite.type_activite,
            statut          = 'ouverte',
            dossier         = activite.dossier,
            section         = activite.section,
            date_ouverture  = date(new_year, new_month, 1),
            date_butoir     = new_butoir,
            est_kpi         = activite.est_kpi,
            est_arrete      = activite.est_arrete,
            activite_parente= activite,
            mois_reference  = mois_ref,
            created_by      = activite.created_by,
        )
        # Copier les acteurs
        for acteur in activite.acteurs.all():
            ActiviteActeur.objects.create(
                activite=clone, utilisateur=acteur.utilisateur,
                role_activite=acteur.role_activite,
                peut_recevoir_mail=acteur.peut_recevoir_mail
            )
        # Copier les PIP
        from .models import ActivitePIP
        for ap in ActivitePIP.objects.filter(activite=activite):
            ActivitePIP.objects.create(activite=clone, pip=ap.pip)

        AlerteMailService.envoyer_clonage(clone)
        return clone

    @staticmethod
    def calculer_progression(activite: Activite) -> int:
        dernier = activite.commentaires.order_by('-created_at').first()
        return dernier.avancement if dernier else activite.etat_avancement
