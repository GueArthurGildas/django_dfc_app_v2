from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.shortcuts import render
from django.utils import timezone
from apps.organisation.models import SousDirection, Section


class DashboardView(LoginRequiredMixin, View):
    template_name = 'dashboard/index.html'

    def get(self, request):
        user = request.user
        today = timezone.now().date()

        # Sous-directions visibles selon le rôle
        role = user.role.code if user.role else ''
        if role in ('admin', 'dfc', 'da'):
            sous_directions = SousDirection.objects.filter(actif=True).order_by('ordre')
        else:
            user_sd = user.get_sous_direction()
            sous_directions = SousDirection.objects.filter(pk=user_sd.pk) if user_sd else SousDirection.objects.none()

        # Stats globales (s'enrichiront en P2 avec les activités)
        stats = {
            'ouvertes':    0,
            'en_cours':    0,
            'en_attente':  0,
            'en_retard':   0,
            'cloturees':   0,
        }
        activites_urgentes = []

        try:
            from apps.operations.models import Activite
            qs = Activite.objects.all()
            if role not in ('admin', 'dfc', 'da'):
                qs = qs.filter(section__sous_direction__in=sous_directions)

            stats['ouvertes']   = qs.filter(statut='ouverte').count()
            stats['en_cours']   = qs.filter(statut='en_cours').count()
            stats['en_attente'] = qs.filter(statut='en_attente').count()
            stats['en_retard']  = qs.filter(statut__in=['ouverte','en_cours'], date_butoir__lt=today).count()
            stats['cloturees']  = qs.filter(statut='cloturee', cloture_le__month=today.month, cloture_le__year=today.year).count()

            activites_urgentes = qs.filter(
                statut__in=['ouverte','en_cours'],
                date_butoir__lte=today + timezone.timedelta(days=7)
            ).select_related('section').order_by('date_butoir')[:10]
        except Exception:
            pass

        context = {
            'sous_directions':    sous_directions,
            'stats':              stats,
            'activites_urgentes': activites_urgentes,
            'today':              today,
        }
        return render(request, self.template_name, context)
