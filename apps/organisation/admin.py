from django.contrib import admin
from .models import (
    SousDirection, Section, UtilisateurSection, PIP,
    CompteComptable, SousDirectionCompte
)


class SousDirectionCompteInline(admin.TabularInline):
    model = SousDirectionCompte
    extra = 1
    autocomplete_fields = ['compte']


@admin.register(SousDirection)
class SousDirectionAdmin(admin.ModelAdmin):
    list_display  = ['code', 'libelle', 'actif', 'ordre']
    list_editable = ['actif', 'ordre']
    inlines       = [SousDirectionCompteInline]


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['code', 'libelle', 'sous_direction', 'actif']
    list_filter  = ['sous_direction', 'actif']


@admin.register(UtilisateurSection)
class UtilisateurSectionAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'section', 'est_principale', 'date_affectation']
    list_filter  = ['section__sous_direction', 'est_principale']


@admin.register(PIP)
class PIPAdmin(admin.ModelAdmin):
    list_display = ['code', 'libelle', 'email', 'sous_direction', 'actif']
    list_filter  = ['sous_direction', 'actif']


@admin.register(CompteComptable)
class CompteComptableAdmin(admin.ModelAdmin):
    list_display   = ['numero', 'libelle', 'type_compte', 'actif']
    list_editable  = ['actif']
    list_filter    = ['type_compte', 'actif']
    search_fields  = ['numero', 'libelle']
    ordering       = ['numero']


@admin.register(SousDirectionCompte)
class SousDirectionCompteAdmin(admin.ModelAdmin):
    list_display = ['sous_direction', 'compte', 'note']
    list_filter  = ['sous_direction']
