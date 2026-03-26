from .models import SousDirection

def sidebar_context(request):
    """Injecte les sous-directions actives dans tous les templates (sidebar dynamique)"""
    if request.user.is_authenticated:
        return {
            'sous_directions_sidebar': SousDirection.objects.filter(actif=True).order_by('ordre')
        }
    return {'sous_directions_sidebar': []}
