from django.contrib import admin
from .models import SousDirection, Section, UtilisateurSection, PIP

@admin.register(SousDirection)
class SousDirectionAdmin(admin.ModelAdmin):
    list_display = ['code', 'libelle', 'actif', 'ordre']
    list_editable = ['actif', 'ordre']

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['code', 'libelle', 'sous_direction', 'actif']
    list_filter = ['sous_direction', 'actif']

@admin.register(UtilisateurSection)
class UtilisateurSectionAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'section', 'est_principale', 'date_affectation']
    list_filter = ['section__sous_direction', 'est_principale']

@admin.register(PIP)
class PIPAdmin(admin.ModelAdmin):
    list_display = ['code', 'libelle', 'email', 'sous_direction', 'actif']
    list_filter = ['sous_direction', 'actif']
