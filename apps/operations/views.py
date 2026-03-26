from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

class DossierListView(LoginRequiredMixin, TemplateView):
    template_name = 'operations/coming_soon.html'
    extra_context = {'module': 'Dossiers'}

class ActiviteListView(LoginRequiredMixin, TemplateView):
    template_name = 'operations/coming_soon.html'
    extra_context = {'module': 'Activités'}

class ActiviteKanbanView(LoginRequiredMixin, TemplateView):
    template_name = 'operations/coming_soon.html'
    extra_context = {'module': 'Kanban'}
