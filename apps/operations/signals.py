"""Signal post_save pour historique automatique des modifications d'Activite."""
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Activite, HistoriqueActivite

CHAMPS_SURVEILLES = ['titre', 'statut', 'date_butoir', 'date_intermediaire', 'etat_avancement', 'section']
_pre_save_instances = {}

@receiver(pre_save, sender=Activite)
def capture_avant_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            _pre_save_instances[instance.pk] = Activite.objects.get(pk=instance.pk)
        except Activite.DoesNotExist:
            pass

@receiver(post_save, sender=Activite)
def enregistrer_historique(sender, instance, created, **kwargs):
    if created:
        return
    ancien = _pre_save_instances.pop(instance.pk, None)
    if not ancien:
        return
    for champ in CHAMPS_SURVEILLES:
        av = str(getattr(ancien, champ, ''))
        nv = str(getattr(instance, champ, ''))
        if av != nv:
            HistoriqueActivite.objects.create(
                activite=instance,
                utilisateur=None,
                champ_modifie=champ,
                ancienne_valeur=av,
                nouvelle_valeur=nv
            )
