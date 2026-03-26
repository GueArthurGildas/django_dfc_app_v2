"""Celery tasks — clonage mensuel et rappels d'échéances."""
from celery import shared_task

@shared_task
def cloner_activites_mensuelles():
    from .models import Activite
    from .services import ActiviteService
    from django.utils import timezone
    today = timezone.now().date()
    # Activités mensuelles clôturées du mois précédent
    if today.month == 1:
        mois_prec = f"{today.year - 1}-12"
    else:
        mois_prec = f"{today.year}-{today.month - 1:02d}"

    clonees = 0
    for a in Activite.objects.filter(type_activite='mensuelle', statut='cloturee', mois_reference=mois_prec):
        result = ActiviteService.cloner(a)
        if result:
            clonees += 1
    return f"{clonees} activité(s) clonée(s)"

@shared_task
def envoyer_rappels_echeances():
    from .models import Activite
    from .notifications import AlerteMailService
    from django.utils import timezone
    today = timezone.now().date()
    from datetime import timedelta
    rappels = 0
    for jours in [7, 3, 1]:
        cible = today + timedelta(days=jours)
        for a in Activite.objects.filter(statut__in=['ouverte', 'en_cours'], date_butoir=cible):
            AlerteMailService.envoyer_rappel(a)
            rappels += 1
    return f"{rappels} rappel(s) envoyé(s)"
