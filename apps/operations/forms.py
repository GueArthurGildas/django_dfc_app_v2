from django import forms
from django.contrib.auth import get_user_model
from .models import Dossier, Activite, CommentaireActivite

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
    La section est héritée du dossier sélectionné.
    Elle est affichée en lecture seule et remplie automatiquement via JS.
    """
    acteurs_ids = forms.ModelMultipleChoiceField(
        queryset=Utilisateur.objects.filter(est_actif_cie=True),
        required=False, label="Acteurs impliqués",
        widget=forms.SelectMultiple(attrs={**WS, 'size': '5'})
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
            # La section est forcément celle du dossier
            cleaned['section'] = dossier.section
        return cleaned


class CommentaireForm(forms.ModelForm):
    class Meta:
        model  = CommentaireActivite
        fields = ['type_comment', 'contenu', 'avancement']
        widgets = {
            'type_comment': forms.Select(attrs=WS),
            'contenu':      forms.Textarea(attrs={**W, 'rows': 3,
                            'placeholder': "Décrivez l'avancement, les blocages, les actions..."}),
            'avancement':   forms.NumberInput(attrs={**W, 'min': 0, 'max': 100}),
        }


class ReporterDateForm(forms.Form):
    nouvelle_date = forms.DateField(
        widget=forms.DateInput(attrs={**W, 'type': 'date'}),
        label="Nouvelle date intermédiaire"
    )
    motif = forms.CharField(
        widget=forms.Textarea(attrs={**W, 'rows': 2}),
        label="Motif du report (obligatoire)"
    )


class CloreForm(forms.Form):
    commentaire      = forms.CharField(
        widget=forms.Textarea(attrs={**W, 'rows': 3}),
        label="Commentaire de clôture"
    )
    date_realisation = forms.DateField(
        widget=forms.DateInput(attrs={**W, 'type': 'date'}),
        label="Date de réalisation effective"
    )
