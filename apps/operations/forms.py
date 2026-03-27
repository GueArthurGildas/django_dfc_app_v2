from django import forms
from django.contrib.auth import get_user_model
from .models import Dossier, Activite, CommentaireActivite, TypeDocument, DocumentActivite

W  = {'class': 'form-control form-control-sm'}
WS = {'class': 'form-select form-select-sm'}
Utilisateur = get_user_model()


class DossierForm(forms.ModelForm):
    class Meta:
        model  = Dossier
        fields = ['titre', 'description', 'section', 'responsable']
        widgets = {
            'titre':       forms.TextInput(attrs=W),
            'description': forms.Textarea(attrs={**W, 'rows': 3}),
            'section':     forms.Select(attrs=WS),
            'responsable': forms.Select(attrs=WS),
        }


class ActiviteForm(forms.ModelForm):
    """
    - section héritée du dossier
    - responsables et acteurs sélectionnés via checkboxes AJAX par SD
    """
    responsables_ids = forms.ModelMultipleChoiceField(
        queryset=Utilisateur.objects.filter(est_actif_cie=True).select_related('role'),
        required=False,
        label="Responsable(s)",
        widget=forms.CheckboxSelectMultiple(),
        help_text="Personne(s) responsable(s) de l'activité"
    )
    acteurs_ids = forms.ModelMultipleChoiceField(
        queryset=Utilisateur.objects.filter(est_actif_cie=True).select_related('role'),
        required=False,
        label="Acteurs impliqués",
        widget=forms.CheckboxSelectMultiple(),
        help_text="Personnes participant à l'activité"
    )
    documents_ids = forms.ModelMultipleChoiceField(
        queryset=TypeDocument.objects.filter(actif=True).order_by('categorie', 'ordre'),
        required=False,
        label="Documents / rendus attendus",
        widget=forms.CheckboxSelectMultiple(),
    )

    class Meta:
        model  = Activite
        fields = [
            'titre', 'description', 'type_activite', 'dossier',
            'date_ouverture', 'date_butoir', 'date_intermediaire',
            'est_kpi', 'est_arrete',
        ]
        widgets = {
            'titre':              forms.TextInput(attrs=W),
            'description':        forms.Textarea(attrs={**W, 'rows': 3}),
            'type_activite':      forms.Select(attrs=WS),
            'dossier':            forms.Select(attrs={**WS, 'id': 'id_dossier'}),
            'date_ouverture':     forms.DateInput(attrs={**W, 'type': 'date'}),
            'date_butoir':        forms.DateInput(attrs={**W, 'type': 'date'}),
            'date_intermediaire': forms.DateInput(attrs={**W, 'type': 'date'}),
        }

    def clean(self):
        cleaned = super().clean()
        dossier = cleaned.get('dossier')
        if dossier:
            cleaned['section'] = dossier.section
        return cleaned


class DocumentActiviteForm(forms.ModelForm):
    class Meta:
        model  = DocumentActivite
        fields = ['etat', 'observations', 'date_prevue', 'date_realisation']
        widgets = {
            'etat':             forms.Select(attrs=WS),
            'observations':     forms.Textarea(attrs={**W, 'rows': 2}),
            'date_prevue':      forms.DateInput(attrs={**W, 'type': 'date'}),
            'date_realisation': forms.DateInput(attrs={**W, 'type': 'date'}),
        }


class CommentaireForm(forms.ModelForm):
    class Meta:
        model  = CommentaireActivite
        fields = ['type_comment', 'contenu', 'avancement']
        widgets = {
            'type_comment': forms.Select(attrs=WS),
            'contenu':      forms.Textarea(attrs={**W, 'rows': 3}),
            'avancement':   forms.NumberInput(attrs={**W, 'min': 0, 'max': 100}),
        }


class ReporterDateForm(forms.Form):
    nouvelle_date = forms.DateField(widget=forms.DateInput(attrs={**W, 'type': 'date'}), label="Nouvelle date")
    motif         = forms.CharField(widget=forms.Textarea(attrs={**W, 'rows': 2}), label="Motif (obligatoire)")


class CloreForm(forms.Form):
    MOTIFS = [
        ('objectif_atteint', 'Objectif atteint'),
        ('partiellement',    'Partiellement atteint'),
        ('non_atteint',      'Objectif non atteint'),
        ('annule',           'Activité annulée'),
        ('autre',            'Autre motif'),
    ]
    motif            = forms.ChoiceField(choices=MOTIFS, widget=forms.RadioSelect(), initial='objectif_atteint', label="Résultat")
    commentaire      = forms.CharField(widget=forms.Textarea(attrs={**W, 'rows': 3}), label="Commentaire de clôture")
    date_realisation = forms.DateField(widget=forms.DateInput(attrs={**W, 'type': 'date'}), label="Date de réalisation effective")
