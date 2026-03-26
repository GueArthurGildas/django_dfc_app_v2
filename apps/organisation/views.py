from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from .models import SousDirection, Section, PIP
from .forms import SousDirectionForm, SectionForm, PIPForm


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
        if user_sd:
            return qs.filter(pk=user_sd.pk)
        return qs.none()


class SousDirectionDetailView(LoginRequiredMixin, DetailView):
    model = SousDirection
    template_name = 'organisation/sous_direction/detail.html'
    context_object_name = 'sd'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['pips_actifs'] = self.object.pips.filter(actif=True)
        return ctx


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
