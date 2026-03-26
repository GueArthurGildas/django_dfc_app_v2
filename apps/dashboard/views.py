import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.shortcuts import render
from django.utils import timezone
from apps.organisation.models import SousDirection


def get_stats_dashboard(user, sd_id=None):
    from apps.operations.views import get_qs_activites, calcul_stats_qs
    qs = get_qs_activites(user)
    if sd_id and sd_id != 'all':
        try:
            qs = qs.filter(section__sous_direction_id=int(sd_id))
        except (ValueError, TypeError):
            pass
    return calcul_stats_qs(qs), qs


def get_mes_activites(user):
    """Activités où l'utilisateur est responsable ou acteur, non clôturées."""
    from apps.operations.models import Activite
    today = timezone.now().date()
    qs = Activite.objects.filter(
        acteurs__utilisateur=user,
        deleted_at__isnull=True
    ).exclude(statut='cloturee').select_related(
        'section__sous_direction', 'dossier'
    ).distinct().order_by('date_butoir')

    # Enrichir chaque activité avec son contexte personnel
    mes_retard    = qs.filter(date_butoir__lt=today)
    mes_urgentes  = qs.filter(date_butoir__gte=today, date_butoir__lte=today + timezone.timedelta(days=7))
    mes_normales  = qs.filter(date_butoir__gt=today + timezone.timedelta(days=7))
    mes_responsable = qs.filter(acteurs__utilisateur=user, acteurs__role_activite='responsable').distinct()

    return {
        'toutes':       qs,
        'en_retard':    mes_retard,
        'urgentes':     mes_urgentes,
        'normales':     mes_normales,
        'responsable':  mes_responsable,
        'total':        qs.count(),
        'nb_retard':    mes_retard.count(),
        'nb_urgentes':  mes_urgentes.count(),
        'nb_responsable': mes_responsable.count(),
    }


class DashboardView(LoginRequiredMixin, View):
    template_name = 'dashboard/index.html'

    def get(self, request):
        today  = timezone.now().date()
        user   = request.user
        sd_id  = request.GET.get('sd', 'all')

        # Sous-directions visibles
        role = user.role.code if user.role else ''
        if role in ('admin', 'dfc', 'da'):
            sous_directions = SousDirection.objects.filter(actif=True).order_by('ordre')
        else:
            user_sd = user.get_sous_direction()
            sous_directions = SousDirection.objects.filter(pk=user_sd.pk) if user_sd else SousDirection.objects.none()

        stats, qs = get_stats_dashboard(user, sd_id)

        # Activités urgentes globales (J-7)
        activites_urgentes = qs.filter(
            statut__in=['ouverte', 'en_cours'],
            date_butoir__lte=today + timezone.timedelta(days=7)
        ).select_related('section__sous_direction').order_by('date_butoir')[:6]

        # MES activités (focus personnel)
        mes_activites = get_mes_activites(user)

        # Stats par SD
        stats_par_sd = []
        for sd in sous_directions:
            from apps.operations.views import calcul_stats_qs, get_qs_activites
            qs_sd = get_qs_activites(user).filter(section__sous_direction=sd)
            s = calcul_stats_qs(qs_sd)
            stats_par_sd.append({
                'id':      sd.pk,
                'code':    sd.code,
                'couleur': sd.couleur,
                'label':   sd.libelle[:20],
                **s
            })

        context = {
            'sous_directions':    sous_directions,
            'sd_selectionnee':    sd_id,
            'stats':              stats,
            'stats_par_sd':       json.dumps(stats_par_sd),
            'sd_cards':           stats_par_sd,
            'activites_urgentes': activites_urgentes,
            'mes_activites':      mes_activites,
            'today':              today,
        }
        return render(request, self.template_name, context)
