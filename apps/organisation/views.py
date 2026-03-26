from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import SousDirection, Section, PIP
from .forms import SousDirectionForm, SectionForm, PIPForm, PhotoResponsableForm


class SousDirectionPortailView(LoginRequiredMixin, ListView):
    model = SousDirection
    template_name = 'organisation/portail/sd_portail.html'
    context_object_name = 'sous_directions'

    def get_queryset(self):
        user = self.request.user
        qs = SousDirection.objects.filter(actif=True).prefetch_related('sections')
        if user.role and user.role.code in ('admin', 'dfc', 'da'):
            return qs
        user_sd = user.get_sous_direction()
        return qs.filter(pk=user_sd.pk) if user_sd else qs.none()


class SousDirectionDetailView(LoginRequiredMixin, DetailView):
    model = SousDirection
    template_name = 'organisation/sous_direction/detail.html'
    context_object_name = 'sd'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        sd = self.object
        ctx['pips_actifs']        = sd.pips.filter(actif=True)
        ctx['membres']            = sd.get_membres()
        ctx['stats']              = sd.get_stats()
        ctx['photo_form']         = PhotoResponsableForm(instance=sd.responsable) if sd.responsable else None
        ctx['peut_modifier']      = self.request.user.role and self.request.user.role.code in ('admin', 'sd')
        # Données pour le pie chart Chart.js
        stats = ctx['stats']
        # Pie : décomposer ouvertes en retard / dans délai
        en_cours_ok = max(0, stats['nb_activites_ouvertes'] - stats['nb_activites_en_retard'])
        ctx['chart_data'] = {
            'labels': ['Clôturées', 'En cours (dans délai)', 'En attente', 'En retard'],
            'values': [
                stats['nb_activites_cloturees'],
                en_cours_ok,
                stats['nb_activites_en_attente'],
                stats['nb_activites_en_retard'],
            ],
            'colors': ['#28a745', sd.couleur, '#F5A623', '#dc3545'],
        }
        return ctx


class PhotoResponsableView(LoginRequiredMixin, View):
    """Upload de la photo du responsable de la SD via POST"""
    def post(self, request, pk):
        sd = get_object_or_404(SousDirection, pk=pk)
        if not sd.responsable:
            messages.error(request, "Aucun responsable défini pour cette sous-direction.")
            return redirect('organisation:sd_detail', pk=pk)
        form = PhotoResponsableForm(request.POST, request.FILES, instance=sd.responsable)
        if form.is_valid():
            form.save()
            messages.success(request, "Photo du responsable mise à jour avec succès.")
        else:
            messages.error(request, "Erreur lors de l'upload. Vérifiez le format de l'image.")
        return redirect('organisation:sd_detail', pk=pk)


class SousDirectionCreateView(LoginRequiredMixin, CreateView):
    model = SousDirection
    form_class = SousDirectionForm
    template_name = 'organisation/sous_direction/form.html'
    success_url = reverse_lazy('organisation:sd_portail')


class SousDirectionUpdateView(LoginRequiredMixin, UpdateView):
    model = SousDirection
    form_class = SousDirectionForm
    template_name = 'organisation/sous_direction/form.html'
    success_url = reverse_lazy('organisation:sd_portail')


class SectionListView(LoginRequiredMixin, ListView):
    model = Section
    template_name = 'organisation/section/list.html'
    context_object_name = 'sections'
    queryset = Section.objects.filter(actif=True).select_related('sous_direction', 'responsable')


class SectionDetailView(LoginRequiredMixin, DetailView):
    model = Section
    template_name = 'organisation/section/detail.html'
    context_object_name = 'section'


class SectionCreateView(LoginRequiredMixin, CreateView):
    model = Section
    form_class = SectionForm
    template_name = 'organisation/section/form.html'
    success_url = reverse_lazy('organisation:section_list')


class SectionUpdateView(LoginRequiredMixin, UpdateView):
    model = Section
    form_class = SectionForm
    template_name = 'organisation/section/form.html'
    success_url = reverse_lazy('organisation:section_list')


class PIPListView(LoginRequiredMixin, ListView):
    model = PIP
    template_name = 'organisation/pip/list.html'
    context_object_name = 'pips'
    queryset = PIP.objects.filter(actif=True).select_related('sous_direction')


class PIPCreateView(LoginRequiredMixin, CreateView):
    model = PIP
    form_class = PIPForm
    template_name = 'organisation/pip/form.html'
    success_url = reverse_lazy('organisation:pip_list')


class PIPUpdateView(LoginRequiredMixin, UpdateView):
    model = PIP
    form_class = PIPForm
    template_name = 'organisation/pip/form.html'
    success_url = reverse_lazy('organisation:pip_list')
