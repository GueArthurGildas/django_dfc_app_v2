import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.shortcuts import render
from django.utils import timezone
from apps.organisation.models import SousDirection
from apps.operations.views import get_qs_activites, calcul_stats_qs, get_user_sd, ROLES_GLOBAUX, appliquer_filtre_periode, get_annees_disponibles, TRIMESTRES


def get_mes_activites(user):
    """Activités non clôturées où l'utilisateur est responsable ou acteur."""
    from apps.operations.models import Activite
    today = timezone.now().date()
    qs = Activite.objects.filter(
        acteurs__utilisateur=user,
        deleted_at__isnull=True
    ).exclude(statut='cloturee').select_related(
        'section__sous_direction', 'dossier'
    ).distinct().order_by('date_butoir')

    return {
        'toutes':         qs,
        'en_retard':      qs.filter(date_butoir__lt=today),
        'urgentes':       qs.filter(date_butoir__gte=today, date_butoir__lte=today + timezone.timedelta(days=7)),
        'normales':       qs.filter(date_butoir__gt=today + timezone.timedelta(days=7)),
        'responsable':    qs.filter(acteurs__utilisateur=user, acteurs__role_activite='responsable').distinct(),
        'total':          qs.count(),
        'nb_retard':      qs.filter(date_butoir__lt=today).count(),
        'nb_urgentes':    qs.filter(date_butoir__gte=today, date_butoir__lte=today + timezone.timedelta(days=7)).count(),
        'nb_responsable': qs.filter(acteurs__utilisateur=user, acteurs__role_activite='responsable').distinct().count(),
    }


class DashboardView(LoginRequiredMixin, View):
    template_name = 'dashboard/index.html'

    def get(self, request):
        today    = timezone.now().date()
        user     = request.user
        role     = user.role.code if user.role else ''
        sd_id     = request.GET.get('sd', 'all')
        annee     = request.GET.get('annee', '')
        trimestre = request.GET.get('trimestre', '')
        user_sd  = get_user_sd(user)  # None si accès global

        # ── Sous-directions visibles ─────────────────────────────────────────
        if user_sd is None:
            # Admin / DFC / DA : toutes les SD
            sous_directions = SousDirection.objects.filter(actif=True).order_by('ordre')
        else:
            # SD et en dessous : uniquement leur SD
            sous_directions = SousDirection.objects.filter(pk=user_sd.pk)
            sd_id = str(user_sd.pk)  # forcer le filtre sur leur SD

        # ── Filtre SD supplémentaire (pour admin/DFC/DA) ─────────────────────
        qs_global = get_qs_activites(user)
        qs_global = appliquer_filtre_periode(qs_global, annee, trimestre)
        if sd_id and sd_id != 'all':
            try:
                qs_global = qs_global.filter(section__sous_direction_id=int(sd_id))
            except (ValueError, TypeError):
                pass

        stats = calcul_stats_qs(qs_global)

        # ── Activités urgentes J-7 ────────────────────────────────────────────
        activites_urgentes = qs_global.filter(
            statut__in=['ouverte', 'en_cours'],
            date_butoir__lte=today + timezone.timedelta(days=7)
        ).select_related('section__sous_direction').order_by('date_butoir')[:6]

        # ── Mes activités (focus personnel) ──────────────────────────────────
        mes_activites = get_mes_activites(user)

        # ── Stats par SD (uniquement les SD visibles) ─────────────────────────
        stats_par_sd = []
        for sd in sous_directions:
            qs_sd = appliquer_filtre_periode(get_qs_activites(user).filter(section__sous_direction=sd), annee, trimestre)
            s     = calcul_stats_qs(qs_sd)
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
            'afficher_filtre_sd': user_sd is None,  # filtre visible seulement pour les globaux
            'stats':              stats,
            'stats_par_sd':       json.dumps(stats_par_sd),
            'sd_cards':           stats_par_sd,
            'activites_urgentes': activites_urgentes,
            'mes_activites':      mes_activites,
            'filtre_annee':       annee,
            'filtre_trimestre':   trimestre,
            'annees_dispo':       get_annees_disponibles(),
            'trimestres':         TRIMESTRES,
            'today':              today,
        }
        return render(request, self.template_name, context)
