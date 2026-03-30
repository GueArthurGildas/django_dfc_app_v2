import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Avg, Count, Q

from .models import Dossier, Activite, ActiviteActeur, CommentaireActivite, DocumentActivite, TypeDocument
from .forms import DossierForm, ActiviteForm, CommentaireForm, ReporterDateForm, CloreForm, DocumentActiviteForm
from .services import ActiviteService
from apps.organisation.models import SousDirection, Section



# ── Filtres temporels (arrêtés comptables) ───────────────────────────────────
TRIMESTRES = [
    ('T1', 'T1 — Jan/Fév/Mar', [1, 2, 3]),
    ('T2', 'T2 — Avr/Mai/Jun', [4, 5, 6]),
    ('T3', 'T3 — Jul/Aoû/Sep', [7, 8, 9]),
    ('T4', 'T4 — Oct/Nov/Déc', [10, 11, 12]),
]

def get_annees_disponibles():
    """Années disponibles dans la base opérations."""
    from django.db.models.functions import ExtractYear
    from apps.operations.models import Activite
    return list(
        Activite.objects.annotate(annee=ExtractYear('date_ouverture'))
        .values_list('annee', flat=True).distinct().order_by('-annee')
    )

def appliquer_filtre_periode(qs, annee, trimestre):
    """Filtre un queryset Activite par année et/ou trimestre d'ouverture."""
    if annee:
        try:
            qs = qs.filter(date_ouverture__year=int(annee))
        except (ValueError, TypeError):
            pass
    if trimestre:
        mois = next((t[2] for t in TRIMESTRES if t[0] == trimestre), None)
        if mois:
            qs = qs.filter(date_ouverture__month__in=mois)
    return qs

def contexte_periode(request):
    """Retourne les variables de contexte liées aux filtres de période."""
    from django.utils import timezone
    annee_courante = timezone.now().year
    return {
        'filtre_annee':     request.GET.get('annee', str(annee_courante)),
        'filtre_trimestre': request.GET.get('trimestre', ''),
        'annees_dispo':     get_annees_disponibles(),
        'trimestres':       TRIMESTRES,
    }

# ── Rôles avec accès global ───────────────────────────────────────────────────
ROLES_GLOBAUX  = ('admin', 'dfc', 'da')
ROLES_CREATION = ('admin', 'dfc', 'da', 'sd')


def get_user_sd(user):
    """Retourne la SD de l'utilisateur ou None si accès global."""
    if user.role and user.role.code in ROLES_GLOBAUX:
        return None  # accès à toutes les SD
    return user.get_sous_direction()


def filtre_qs_par_sd(qs, user, champ_sd='section__sous_direction'):
    """Filtre un queryset selon la SD de l'utilisateur."""
    sd = get_user_sd(user)
    if sd:
        return qs.filter(**{champ_sd: sd})
    return qs


def get_qs_activites(user):
    qs = Activite.objects.filter(deleted_at__isnull=True).select_related(
        'section__sous_direction', 'dossier', 'created_by'
    )
    sd = get_user_sd(user)
    if sd:
        return qs.filter(section__sous_direction=sd)
    return qs


def calcul_stats_qs(qs):
    today     = timezone.now().date()
    total     = qs.count()
    cloturees = qs.filter(statut='cloturee').count()
    en_retard = qs.filter(statut__in=['ouverte','en_cours'], date_butoir__lt=today).count()
    en_delai  = qs.filter(statut='cloturee', est_dans_delai=True).count()
    avancement = qs.aggregate(moy=Avg('etat_avancement'))['moy'] or 0
    return {
        'total':            total,
        'ouvertes':         qs.filter(statut='ouverte').count(),
        'en_cours':         qs.filter(statut='en_cours').count(),
        'en_attente':       qs.filter(statut='en_attente').count(),
        'cloturees':        cloturees,
        'en_retard':        en_retard,
        'taux_completion':  round(cloturees / total * 100) if total else 0,
        'taux_delai':       round(en_delai / cloturees * 100) if cloturees else 0,
        'taux_retard':      round(en_retard / total * 100) if total else 0,
        'avancement_moyen': round(avancement),
    }


# ── Dossiers ──────────────────────────────────────────────────────────────────

class DossierListView(LoginRequiredMixin, ListView):
    model = Dossier
    template_name = 'operations/dossier/list.html'
    context_object_name = 'dossiers'

    def get_queryset(self):
        qs    = Dossier.objects.filter(est_actif=True).select_related('section__sous_direction', 'responsable')
        qs    = filtre_qs_par_sd(qs, self.request.user)
        sd_id = self.request.GET.get('sd')
        if sd_id:
            qs = qs.filter(section__sous_direction_id=sd_id)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['sous_directions'] = SousDirection.objects.filter(actif=True)
        ctx['filtre_sd']       = self.request.GET.get('sd', '')
        return ctx


class DossierDetailView(LoginRequiredMixin, DetailView):
    model = Dossier
    template_name = 'operations/dossier/detail.html'
    context_object_name = 'dossier'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['activites'] = self.object.activites.filter(deleted_at__isnull=True).select_related('section')
        return ctx


class DossierCreateView(LoginRequiredMixin, View):
    template_name = 'operations/dossier/form.html'

    def _get_form(self, user, data=None):
        from apps.organisation.models import Section
        form = DossierForm(data)
        role = user.role.code if user.role else ''
        # Restreindre les sections à celles de la SD de l'utilisateur
        if role not in ('admin', 'dfc', 'da'):
            user_sd = user.get_sous_direction()
            if user_sd:
                form.fields['section'].queryset = Section.objects.filter(
                    sous_direction=user_sd, actif=True
                )
            else:
                form.fields['section'].queryset = Section.objects.none()
        # Restreindre le responsable aux membres de la SD
        if role not in ('admin', 'dfc', 'da'):
            from apps.authentication.models import Utilisateur
            user_sd = user.get_sous_direction()
            if user_sd:
                form.fields['responsable'].queryset = Utilisateur.objects.filter(
                    sections_lien__section__sous_direction=user_sd,
                    est_actif_cie=True
                ).distinct()
        return form

    def get(self, request):
        return render(request, self.template_name, {
            'form': self._get_form(request.user),
            'action': 'Créer'
        })

    def post(self, request):
        form = self._get_form(request.user, request.POST)
        if form.is_valid():
            dossier = form.save(commit=False)
            # Sécurité : vérifier que la section appartient bien à la SD de l'user
            role = request.user.role.code if request.user.role else ''
            if role not in ('admin', 'dfc', 'da'):
                user_sd = request.user.get_sous_direction()
                if dossier.section.sous_direction != user_sd:
                    messages.error(request, "Vous ne pouvez pas créer un dossier pour une autre sous-direction.")
                    return render(request, self.template_name, {'form': form, 'action': 'Créer'})
            dossier.save()
            messages.success(request, f"Dossier « {dossier.titre} » créé.")
            return redirect('operations:dossier_list')
        return render(request, self.template_name, {'form': form, 'action': 'Créer'})


class DossierUpdateView(LoginRequiredMixin, UpdateView):
    model = Dossier
    form_class = DossierForm
    template_name = 'operations/dossier/form.html'
    success_url = reverse_lazy('operations:dossier_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user
        role = user.role.code if user.role else ''
        if role not in ('admin', 'dfc', 'da'):
            from apps.organisation.models import Section
            from apps.authentication.models import Utilisateur
            user_sd = user.get_sous_direction()
            if user_sd:
                form.fields['section'].queryset = Section.objects.filter(
                    sous_direction=user_sd, actif=True
                )
                form.fields['responsable'].queryset = Utilisateur.objects.filter(
                    sections_lien__section__sous_direction=user_sd,
                    est_actif_cie=True
                ).distinct()
        return form


# ── Activités ─────────────────────────────────────────────────────────────────

class ActiviteListView(LoginRequiredMixin, ListView):
    model = Activite
    template_name = 'operations/activite/list.html'
    context_object_name = 'activites'
    paginate_by = 25

    def get_queryset(self):
        qs       = get_qs_activites(self.request.user)
        statut   = self.request.GET.get('statut')
        sd_id    = self.request.GET.get('sd')
        assignee = self.request.GET.get('assignee')
        annee    = self.request.GET.get('annee')
        mois     = self.request.GET.get('mois')
        q         = self.request.GET.get('q', '').strip()
        trimestre = self.request.GET.get('trimestre', '')
        if q:
            qs = qs.filter(
                Q(titre__icontains=q) |
                Q(description__icontains=q) |
                Q(dossier__titre__icontains=q) |
                Q(section__libelle__icontains=q) |
                Q(section__sous_direction__code__icontains=q)
            ).distinct()
        if statut:
            qs = qs.filter(statut=statut)
        if sd_id:
            qs = qs.filter(section__sous_direction_id=sd_id)
        if assignee == 'me':
            qs = qs.filter(acteurs__utilisateur=self.request.user).distinct()
        # Filtres période
        qs = appliquer_filtre_periode(qs, annee, trimestre)
        return qs.order_by('date_butoir')

    def get_context_data(self, **kwargs):
        ctx      = super().get_context_data(**kwargs)
        assignee = self.request.GET.get('assignee', '')
        qs_base  = get_qs_activites(self.request.user)
        if assignee == 'me':
            qs_base = qs_base.filter(acteurs__utilisateur=self.request.user).distinct()
        ctx['stats']           = calcul_stats_qs(qs_base)
        # Les non-globaux ne voient que leur propre SD dans le filtre
        user_sd = get_user_sd(self.request.user)
        if user_sd:
            ctx['sous_directions'] = SousDirection.objects.filter(pk=user_sd.pk)
        else:
            ctx['sous_directions'] = SousDirection.objects.filter(actif=True)
        ctx['filtre_statut']   = self.request.GET.get('statut', '')
        ctx['filtre_sd']       = self.request.GET.get('sd', '')
        ctx['filtre_assignee'] = assignee
        ctx['filtre_annee']    = self.request.GET.get('annee', '')
        ctx['filtre_q']        = self.request.GET.get('q', '')
        ctx['filtre_trimestre'] = self.request.GET.get('trimestre', '')
        ctx['trimestres']       = TRIMESTRES
        ctx['filtre_mois']     = self.request.GET.get('mois', '')
        ctx['today']           = timezone.now().date()
        # Années disponibles pour le filtre
        from django.db.models.functions import ExtractYear
        ctx['mois_list'] = [
            (1,'Janvier'),(2,'Février'),(3,'Mars'),(4,'Avril'),
            (5,'Mai'),(6,'Juin'),(7,'Juillet'),(8,'Août'),
            (9,'Septembre'),(10,'Octobre'),(11,'Novembre'),(12,'Décembre')
        ]
        ctx['annees_dispo'] = (
            get_qs_activites(self.request.user)
            .annotate(annee=ExtractYear('date_ouverture'))
            .values_list('annee', flat=True)
            .distinct().order_by('-annee')
        )
        return ctx


class ActiviteDetailView(LoginRequiredMixin, DetailView):
    model = Activite
    template_name = 'operations/activite/detail.html'
    context_object_name = 'activite'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        a   = self.object
        ctx['acteurs']        = a.acteurs.select_related('utilisateur__role').all()
        ctx['commentaires']   = a.commentaires.select_related('auteur').order_by('created_at')
        ctx['historique']     = a.historique.select_related('utilisateur').order_by('-created_at')[:10]
        ctx['comment_form']   = CommentaireForm()
        ctx['clore_form']     = CloreForm(initial={'date_realisation': timezone.now().date(), 'motif': 'objectif_atteint'})
        ctx['reporter_form']  = ReporterDateForm()
        ctx['documents']      = a.documents.select_related('type_document','mis_a_jour_par').order_by('type_document__categorie','type_document__ordre')
        ctx['types_documents'] = TypeDocument.objects.filter(actif=True).exclude(pk__in=a.documents.values('type_document_id')).order_by('categorie','ordre')
        ctx['today']          = timezone.now().date()
        # Membres de la SD pour le sélecteur d'ajout d'acteur
        from apps.authentication.models import Utilisateur
        ctx['membres_sd'] = Utilisateur.objects.filter(
            sections_lien__section__sous_direction=a.section.sous_direction,
            est_actif_cie=True
        ).select_related('role').exclude(
            pk__in=a.acteurs.values('utilisateur_id')
        ).order_by('role__niveau', 'last_name', 'first_name').distinct()
        bg, fg = a.get_statut_display_badge()
        ctx['statut_bg'], ctx['statut_fg'] = bg, fg
        return ctx


# Rôles autorisés à créer des activités
ROLES_CREATION_ACTIVITE = ('admin', 'dfc', 'da', 'sd')


class ActiviteCreateView(LoginRequiredMixin, View):
    template_name = 'operations/activite/form.html'

    def _check_permission(self, user):
        return user.role and user.role.code in ROLES_CREATION_ACTIVITE

    def _dossiers_sections(self):
        return {
            str(d.pk): {
                'section_id':      d.section_id,
                'section_code':    d.section.code,
                'section_libelle': d.section.libelle,
                'sd_code':         d.section.sous_direction.code,
                'sd_id':           d.section.sous_direction_id,
                'sd_couleur':      d.section.sous_direction.couleur,
            }
            for d in Dossier.objects.select_related('section__sous_direction').all()
        }

    def _membres_par_sd(self):
        """Retourne les membres groupés par SD pour le sélecteur JS."""
        from apps.authentication.models import Utilisateur
        membres = Utilisateur.objects.filter(
            est_actif_cie=True
        ).select_related('role').prefetch_related(
            'sections_lien__section__sous_direction'
        ).order_by('role__niveau', 'last_name', 'first_name')

        result = {}
        for u in membres:
            sd = u.get_sous_direction()
            sd_id = str(sd.pk) if sd else '0'
            if sd_id not in result:
                result[sd_id] = []
            result[sd_id].append({
                'id':     u.pk,
                'nom':    u.nom_complet,
                'role':   u.role.libelle if u.role else '',
                'niveau': u.role.niveau if u.role else 9,
            })
        return result

    def get(self, request):
        if not self._check_permission(request.user):
            messages.error(request, "Vous n'avez pas les droits pour créer une activité. Seuls les Sous-Directeurs, DA et DFC peuvent le faire.")
            return redirect('operations:activite_list')
        initial = {}
        if request.GET.get('dossier'):
            initial['dossier'] = request.GET.get('dossier')
        return render(request, self.template_name, {
            'form':               ActiviteForm(initial=initial),
            'action':             'Créer',
            'dossiers_sections':  json.dumps(self._dossiers_sections()),
            'membres_par_sd':     json.dumps(self._membres_par_sd()),
        })

    def post(self, request):
        if not self._check_permission(request.user):
            messages.error(request, "Action non autorisée.")
            return redirect('operations:activite_list')
        form = ActiviteForm(request.POST)
        if form.is_valid():
            data             = form.cleaned_data.copy()
            acteurs_ids      = [u.pk for u in data.pop('acteurs_ids', [])]
            responsables_ids = [u.pk for u in data.pop('responsables_ids', [])]
            documents_ids    = [td.pk for td in data.pop('documents_ids', [])]
            data['acteurs_ids']      = acteurs_ids
            data['responsables_ids'] = responsables_ids
            activite = ActiviteService.creer(data, request.user)
            for td_pk in documents_ids:
                DocumentActivite.objects.get_or_create(
                    activite=activite, type_document_id=td_pk,
                    defaults={'etat': 'non_commence'}
                )
            messages.success(request, f"Activité « {activite.titre} » créée avec succès.")
            return redirect('operations:activite_detail', pk=activite.pk)
        return render(request, self.template_name, {
            'form':              form,
            'action':            'Créer',
            'dossiers_sections': json.dumps(self._dossiers_sections()),
            'membres_par_sd':    json.dumps(self._membres_par_sd()),
        })


class ActiviteUpdateView(LoginRequiredMixin, UpdateView):
    model = Activite
    form_class = ActiviteForm
    template_name = 'operations/activite/form.html'

    def get_success_url(self):
        return reverse('operations:activite_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['action'] = 'Modifier'
        return ctx


class CommenterView(LoginRequiredMixin, View):
    def post(self, request, pk):
        activite    = get_object_or_404(Activite, pk=pk)
        contenu     = request.POST.get('contenu', '').strip()
        type_comment= request.POST.get('type_comment', 'mise_a_jour')
        avancement  = int(request.POST.get('avancement', activite.etat_avancement))
        statut      = request.POST.get('statut', activite.statut)

        # Validation basique
        if not contenu:
            messages.error(request, "Le commentaire ne peut pas être vide.")
            return redirect('operations:activite_detail', pk=pk)

        # Transition automatique selon l'avancement si statut non fourni explicitement
        if statut not in dict(Activite.STATUTS):
            statut = activite.statut
        # Si l'avancement progresse et que l'activité est encore "ouverte" → en_cours
        if avancement > 0 and statut == 'ouverte':
            statut = 'en_cours'

        ActiviteService.mettre_a_jour(
            activite, statut, avancement, contenu, request.user, type_comment
        )
        messages.success(request, "Suivi enregistré.")
        return redirect('operations:activite_detail', pk=pk)


class CloreActiviteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        activite = get_object_or_404(Activite, pk=pk)
        form = CloreForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            ActiviteService.clore(activite, d['commentaire'], request.user, motif=d['motif'], date_realisation=d['date_realisation'])
            messages.success(request, "Activité clôturée.")
        else:
            messages.error(request, "Veuillez corriger les erreurs du formulaire.")
        return redirect('operations:activite_detail', pk=pk)


class ReporterDateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        activite = get_object_or_404(Activite, pk=pk)
        form = ReporterDateForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            ActiviteService.reporter_date(activite, d['nouvelle_date'], d['motif'], request.user)
            messages.success(request, f"Date reportée au {d['nouvelle_date']}.")
        return redirect('operations:activite_detail', pk=pk)


class ClonerActiviteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        activite = get_object_or_404(Activite, pk=pk)
        clone = ActiviteService.cloner(activite)
        if clone:
            messages.success(request, f"Activité clonée pour {clone.mois_reference}.")
            return redirect('operations:activite_detail', pk=clone.pk)
        messages.warning(request, "Une instance existe déjà pour ce mois.")
        return redirect('operations:activite_detail', pk=pk)


class ChangerStatutView(LoginRequiredMixin, View):
    def post(self, request, pk):
        activite = get_object_or_404(Activite, pk=pk)
        try:
            data   = json.loads(request.body)
            statut = data.get('statut')
            if statut not in dict(Activite.STATUTS):
                return JsonResponse({'error': 'Statut invalide'}, status=400)
            ActiviteService.mettre_a_jour(activite, statut, activite.etat_avancement, f"Statut changé via Kanban → {statut}", request.user)
            return JsonResponse({'ok': True, 'statut': statut})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class ActiviteKanbanView(LoginRequiredMixin, View):
    template_name = 'operations/activite/kanban.html'

    def get(self, request):
        qs        = get_qs_activites(request.user).filter(deleted_at__isnull=True)
        sd_id     = request.GET.get('sd')
        annee     = request.GET.get('annee', '')
        trimestre = request.GET.get('trimestre', '')
        if sd_id:
            qs = qs.filter(section__sous_direction_id=sd_id)
        qs = appliquer_filtre_periode(qs, annee, trimestre)
        kanban_cols = [
            {'statut':'ouverte',    'label':'Ouverte',    'color':'#003F7F', 'activites': list(qs.filter(statut='ouverte').order_by('date_butoir').select_related('section__sous_direction'))},
            {'statut':'en_cours',   'label':'En cours',   'color':'#F5A623', 'activites': list(qs.filter(statut='en_cours').order_by('date_butoir').select_related('section__sous_direction'))},
            {'statut':'en_attente', 'label':'En attente', 'color':'#6c757d', 'activites': list(qs.filter(statut='en_attente').order_by('date_butoir').select_related('section__sous_direction'))},
            {'statut':'cloturee',   'label':'Clôturée',   'color':'#28a745', 'activites': list(qs.filter(statut='cloturee').order_by('-cloture_le').select_related('section__sous_direction')[:15])},
        ]
        return render(request, self.template_name, {
            'kanban_cols':     kanban_cols,
            'sous_directions': SousDirection.objects.filter(actif=True),
            'filtre_sd':       sd_id or '',
            'filtre_annee':    annee,
            'filtre_trimestre':trimestre,
            'annees_dispo':    get_annees_disponibles(),
            'trimestres':      TRIMESTRES,
            'today':           timezone.now().date(),
        })


# ── Documents ─────────────────────────────────────────────────────────────────

class AjouterDocumentActiviteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        activite = get_object_or_404(Activite, pk=pk)
        td_pk    = request.POST.get('type_document_id')
        if td_pk:
            td = get_object_or_404(TypeDocument, pk=td_pk, actif=True)
            DocumentActivite.objects.get_or_create(
                activite=activite, type_document=td,
                defaults={'etat': 'non_commence'}
            )
            messages.success(request, f"Document « {td.libelle} » ajouté.")
        return redirect('operations:activite_detail', pk=pk)


class ChangerStatutDocView(LoginRequiredMixin, View):
    def post(self, request, pk, doc_pk):
        doc = get_object_or_404(DocumentActivite, pk=doc_pk, activite_id=pk)
        try:
            data = json.loads(request.body)
        except Exception:
            data = {}
        etat         = data.get('etat') or request.POST.get('etat')
        observations = data.get('observations', doc.observations)

        if etat not in dict(DocumentActivite.ETATS):
            return JsonResponse({'error': 'État invalide'}, status=400)

        doc.etat         = etat
        doc.observations = observations
        doc.mis_a_jour_par = request.user
        doc.mis_a_jour_le  = timezone.now()
        doc.save(update_fields=['etat','observations','mis_a_jour_par','mis_a_jour_le'])

        bg, fg = doc.couleur_etat
        return JsonResponse({'ok': True, 'etat': etat, 'label': doc.get_etat_display(), 'bg': bg, 'fg': fg})


class SupprimerDocView(LoginRequiredMixin, View):
    def post(self, request, pk, doc_pk):
        doc     = get_object_or_404(DocumentActivite, pk=doc_pk, activite_id=pk)
        libelle = doc.type_document.libelle
        doc.delete()
        messages.success(request, f"Document « {libelle} » retiré.")
        return redirect('operations:activite_detail', pk=pk)


# ── Gestion des acteurs ────────────────────────────────────────────────────────

class AjouterActeurView(LoginRequiredMixin, View):
    def post(self, request, pk):
        activite    = get_object_or_404(Activite, pk=pk)
        user_id     = request.POST.get('user_id')
        role        = request.POST.get('role', 'acteur')
        recevoir_mail = request.POST.get('peut_recevoir_mail', 'true') == 'true'
        if user_id:
            from apps.authentication.models import Utilisateur
            user = get_object_or_404(Utilisateur, pk=user_id)
            obj, created = ActiviteActeur.objects.get_or_create(
                activite=activite, utilisateur=user,
                defaults={'role_activite': role, 'peut_recevoir_mail': recevoir_mail}
            )
            if not created:
                obj.role_activite = role
                obj.peut_recevoir_mail = recevoir_mail
                obj.save()
            label = 'ajouté' if created else 'mis à jour'
            messages.success(request, f"{user.nom_complet} {label} comme {role}.")
        return redirect('operations:activite_detail', pk=pk)


class RetirerActeurView(LoginRequiredMixin, View):
    def post(self, request, pk, acteur_pk):
        lien = get_object_or_404(ActiviteActeur, pk=acteur_pk, activite_id=pk)
        nom  = lien.utilisateur.nom_complet
        lien.delete()
        messages.success(request, f"{nom} retiré de l'activité.")
        return redirect('operations:activite_detail', pk=pk)


class ChangerRoleActeurView(LoginRequiredMixin, View):
    def post(self, request, pk, acteur_pk):
        lien = get_object_or_404(ActiviteActeur, pk=acteur_pk, activite_id=pk)
        role = request.POST.get('role', lien.role_activite)
        if role in ('responsable', 'acteur'):
            lien.role_activite = role
            lien.save(update_fields=['role_activite'])
        return redirect('operations:activite_detail', pk=pk)


# ── API JSON ──────────────────────────────────────────────────────────────────

class StatsAPIView(LoginRequiredMixin, View):
    def get(self, request):
        sd_id = request.GET.get('sd', '')
        qs    = get_qs_activites(request.user)
        if sd_id and sd_id != 'all':
            qs = qs.filter(section__sous_direction_id=sd_id)
        stats = calcul_stats_qs(qs)
        today = timezone.now().date()
        stats_par_sd = []
        for sd in SousDirection.objects.filter(actif=True):
            qs_sd    = get_qs_activites(request.user).filter(section__sous_direction=sd)
            total_sd = qs_sd.count()
            clot_sd  = qs_sd.filter(statut='cloturee').count()
            retard_sd= qs_sd.filter(statut__in=['ouverte','en_cours'], date_butoir__lt=today).count()
            stats_par_sd.append({
                'id':      sd.pk,
                'code':    sd.code,
                'couleur': sd.couleur,
                'total':   total_sd,
                'cloturees': clot_sd,
                'en_retard': retard_sd,
                'taux':    round(clot_sd/total_sd*100) if total_sd else 0,
            })
        urgentes = list(
            qs.filter(statut__in=['ouverte','en_cours'], date_butoir__lte=today+timezone.timedelta(days=7))
            .order_by('date_butoir')
            .values('id','titre','date_butoir','etat_avancement','statut','section__code','section__sous_direction__couleur')[:8]
        )
        for u in urgentes:
            u['date_butoir'] = str(u['date_butoir'])
        stats['stats_par_sd'] = stats_par_sd
        stats['urgentes']     = urgentes
        return JsonResponse(stats)
