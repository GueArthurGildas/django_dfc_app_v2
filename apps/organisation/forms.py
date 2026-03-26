from django import forms
from .models import SousDirection, Section, PIP, COULEURS_SD

W  = {'class': 'form-control form-control-sm'}
WS = {'class': 'form-select form-select-sm'}


class SousDirectionForm(forms.ModelForm):
    class Meta:
        model  = SousDirection
        fields = ['code', 'libelle', 'description', 'couleur', 'responsable', 'ordre', 'actif']
        widgets = {
            'code':        forms.TextInput(attrs=W),
            'libelle':     forms.TextInput(attrs=W),
            'description': forms.Textarea(attrs={**W, 'rows': 3}),
            'couleur':     forms.Select(attrs=WS, choices=COULEURS_SD),
            'responsable': forms.Select(attrs=WS),
            'ordre':       forms.NumberInput(attrs=W),
        }


class SectionForm(forms.ModelForm):
    class Meta:
        model  = Section
        fields = ['sous_direction', 'code', 'libelle', 'description', 'responsable', 'actif']
        widgets = {
            'sous_direction': forms.Select(attrs=WS),
            'code':           forms.TextInput(attrs=W),
            'libelle':        forms.TextInput(attrs=W),
            'description':    forms.Textarea(attrs={**W, 'rows': 3}),
            'responsable':    forms.Select(attrs=WS),
        }


class PIPForm(forms.ModelForm):
    class Meta:
        model  = PIP
        fields = ['code', 'libelle', 'description', 'email', 'telephone', 'sous_direction', 'actif']
        widgets = {
            'code':           forms.TextInput(attrs=W),
            'libelle':        forms.TextInput(attrs=W),
            'description':    forms.Textarea(attrs={**W, 'rows': 3}),
            'email':          forms.EmailInput(attrs=W),
            'telephone':      forms.TextInput(attrs=W),
            'sous_direction': forms.Select(attrs=WS),
        }
