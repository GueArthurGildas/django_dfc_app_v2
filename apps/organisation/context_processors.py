from .models import SousDirection

def sidebar_context(request):
    """Injecte les sous-directions actives dans tous les templates (sidebar dynamique)"""
    if request.user.is_authenticated:
        return {
            'sous_directions_sidebar': SousDirection.objects.filter(actif=True).order_by('ordre')
        }
    return {'sous_directions_sidebar': []}


def alertes_context(request):
    """Compte les activités en retard et urgentes pour la cloche de notification."""
    if not request.user.is_authenticated:
        return {'nb_alertes': 0, 'alertes': []}
    try:
        from django.utils import timezone
        from apps.operations.models import Activite
        today = timezone.now().date()
        dans_7j = today + timezone.timedelta(days=7)

        # Activités en retard OU à échéance dans 7j, non clôturées
        # Filtrées selon le périmètre de l'utilisateur
        qs = Activite.objects.filter(
            deleted_at__isnull=True,
            statut__in=['ouverte', 'en_cours'],
        ).select_related('section__sous_direction')

        # Restreindre selon le rôle
        if request.user.role and request.user.role.code not in ('admin', 'dfc', 'da'):
            sd = request.user.get_sous_direction()
            if sd:
                qs = qs.filter(section__sous_direction=sd)
            else:
                qs = qs.none()

        en_retard = list(qs.filter(date_butoir__lt=today).order_by('date_butoir')[:5])
        urgentes  = list(qs.filter(date_butoir__gte=today, date_butoir__lte=dans_7j).order_by('date_butoir')[:5])

        alertes = []
        for a in en_retard:
            jours = (today - a.date_butoir).days
            alertes.append({'activite': a, 'type': 'retard', 'jours': jours})
        for a in urgentes:
            jours = (a.date_butoir - today).days
            alertes.append({'activite': a, 'type': 'urgente', 'jours': jours})

        return {'nb_alertes': len(alertes), 'alertes': alertes}
    except Exception:
        return {'nb_alertes': 0, 'alertes': []}


def ia_context(request):
    """Injecte les suggestions IA dans tous les templates."""
    return {
        'ia_suggestions': [
            'Balance Générale', 'Grand Livre', 'Lettrage comptable',
            'Arrêté mensuel', 'Gestion du stress', 'SYSCOHADA',
            'Rapprochement bancaire', 'Trésorerie',
        ]
    }


def annonces_context(request):
    """Injecte les annonces actives — affichées une seule fois par session."""
    if not request.user.is_authenticated:
        return {'annonces_actives': []}
    from apps.authentication.models import Annonce
    annonces = list(Annonce.get_actives())
    # Filtrer celles déjà vues dans cette session
    vues = request.session.get('annonces_vues', [])
    annonces_nouvelles = [a for a in annonces if a.pk not in vues]
    return {
        'annonces_actives':    annonces_nouvelles,
        'nb_annonces_actives': len(annonces_nouvelles),
    }
