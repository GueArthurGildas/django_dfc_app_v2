from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

class BalanceListView(LoginRequiredMixin, TemplateView):
    template_name = 'operations/coming_soon.html'
    extra_context = {'module': 'Balance Générale'}

class GrandLivreListView(LoginRequiredMixin, TemplateView):
    template_name = 'operations/coming_soon.html'
    extra_context = {'module': 'Grand Livre'}
