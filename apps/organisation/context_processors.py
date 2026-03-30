from .models import SousDirection

def sidebar_context(request):
    """Injecte les sous-directions actives dans tous les templates (sidebar dynamique)"""
    if request.user.is_authenticated:
        return {
            'sous_directions_sidebar': SousDirection.objects.filter(actif=True).order_by('ordre')
        }
    return {'sous_directions_sidebar': []}


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
