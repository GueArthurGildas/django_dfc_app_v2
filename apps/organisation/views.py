from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import SousDirection, Section, PIP, CompteComptable, SousDirectionCompte
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
        # Comptes déjà associés à la SD
        comptes_associes_ids = sd.comptes.values_list('compte_id', flat=True)
        ctx['comptes_disponibles']  = CompteComptable.objects.filter(actif=True).exclude(pk__in=comptes_associes_ids).order_by('type_compte','numero')
        # Dossiers de la SD pour remplacer les modules métier
        from apps.operations.models import Dossier
        ctx['dossiers_sd'] = Dossier.objects.filter(
            section__sous_direction=sd, est_actif=True
        ).select_related('section').order_by('section__code', 'titre')
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
        ctx['chart_legende'] = [
            ('Clôturées',           stats['nb_activites_cloturees'],  '#28a745'),
            ('En cours / Ouvertes', en_cours_ok,                       sd.couleur),
            ('En attente',          stats['nb_activites_en_attente'],  '#F5A623'),
            ('En retard',           stats['nb_activites_en_retard'],   '#dc3545'),
        ]
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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method in ('POST', 'PUT'):
            kwargs['files'] = self.request.FILES
        return kwargs


class SousDirectionUpdateView(LoginRequiredMixin, UpdateView):
    model = SousDirection
    form_class = SousDirectionForm
    template_name = 'organisation/sous_direction/form.html'
    success_url = reverse_lazy('organisation:sd_portail')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method in ('POST', 'PUT'):
            kwargs['files'] = self.request.FILES
        return kwargs


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

class GererComptesSDView(LoginRequiredMixin, View):
    """Ajoute un compte comptable à une sous-direction."""
    def post(self, request, pk):
        sd = get_object_or_404(SousDirection, pk=pk)
        compte_pk = request.POST.get('compte_id')
        note      = request.POST.get('note', '')
        if compte_pk:
            compte = get_object_or_404(CompteComptable, pk=compte_pk, actif=True)
            SousDirectionCompte.objects.get_or_create(
                sous_direction=sd, compte=compte,
                defaults={'note': note}
            )
            messages.success(request, f"Compte {compte.numero} — {compte.libelle} ajouté.")
        return redirect('organisation:sd_detail', pk=pk)


class RetirerCompteSDView(LoginRequiredMixin, View):
    """Retire un compte comptable d'une sous-direction."""
    def post(self, request, pk, compte_pk):
        lien = get_object_or_404(SousDirectionCompte, sous_direction_id=pk, compte_id=compte_pk)
        numero = lien.compte.numero
        lien.delete()
        messages.success(request, f"Compte {numero} retiré.")
        return redirect('organisation:sd_detail', pk=pk)

class AudioSDView(LoginRequiredMixin, View):
    """Upload dédié de l'audio de présentation d'une SD — ne touche qu'au champ audio_resume."""
    def post(self, request, pk):
        sd = get_object_or_404(SousDirection, pk=pk)
        if 'audio_resume' not in request.FILES:
            messages.error(request, "Aucun fichier audio sélectionné.")
            return redirect('organisation:sd_detail', pk=pk)
        fichier = request.FILES['audio_resume']
        # Vérifier le type MIME
        if not fichier.content_type.startswith('audio/'):
            messages.error(request, "Le fichier doit être un fichier audio (MP3, WAV, OGG...).")
            return redirect('organisation:sd_detail', pk=pk)
        # Supprimer l'ancien fichier si présent
        if sd.audio_resume:
            try:
                import os
                if os.path.isfile(sd.audio_resume.path):
                    os.remove(sd.audio_resume.path)
            except Exception:
                pass
        sd.audio_resume = fichier
        sd.save(update_fields=['audio_resume'])
        messages.success(request, "Audio de présentation mis à jour avec succès.")
        return redirect('organisation:sd_detail', pk=pk)
