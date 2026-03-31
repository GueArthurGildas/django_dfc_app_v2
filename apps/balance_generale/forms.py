from django import forms
from .models import BgImport, BgAlerte

W  = {'class': 'form-control form-control-sm'}
WS = {'class': 'form-select form-select-sm'}


class BgUploadForm(forms.Form):
    fichier  = forms.FileField(
        label="Fichier Balance Générale (.xlsx)",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx,.xls'}),
        help_text="Fichier Excel exporté depuis JADE/SAP — structure tripartite CIE/Secteur/Exploitant"
    )
    exercice = forms.IntegerField(
        label="Exercice comptable",
        min_value=2000, max_value=2099,
        widget=forms.NumberInput(attrs={**W, 'placeholder': 'ex: 2026'}),
    )
    periode  = forms.IntegerField(
        label="Période G/L",
        min_value=1, max_value=16,
        widget=forms.NumberInput(attrs={**W, 'placeholder': '1-12 (ou 13-16 pour périodes spéciales)'}),
        help_text="Numéro de période : 1=Janvier ... 12=Décembre"
    )

    def clean(self):
        cleaned = super().clean()
        exercice = cleaned.get('exercice')
        periode  = cleaned.get('periode')
        if exercice and periode:
            if BgImport.objects.filter(exercice=exercice, periode=periode).exists():
                raise forms.ValidationError(
                    f"Une Balance Générale pour {exercice} P{periode:02d} existe déjà. "
                    "Supprimez-la avant de réimporter."
                )
        return cleaned


class AlerteJustificationForm(forms.ModelForm):
    class Meta:
        model   = BgAlerte
        fields  = ['justification', 'statut']
        widgets = {
            'justification': forms.Textarea(attrs={**W, 'rows': 3,
                'placeholder': 'Expliquez pourquoi cette alerte est normale ou résolue...'}),
            'statut': forms.Select(attrs=WS),
        }


class ValidationForm(forms.Form):
    commentaire = forms.CharField(
        label="Commentaire de validation",
        required=False,
        widget=forms.Textarea(attrs={**W, 'rows': 3,
            'placeholder': "Observations de la Direction Financière..."}),
    )
    geler_periode = forms.BooleanField(
        label="Geler la période après validation (irréversible)",
        required=False,
        initial=False,
    )
