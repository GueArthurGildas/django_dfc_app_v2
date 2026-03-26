from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur, Role

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['code', 'libelle', 'niveau']
    ordering = ['niveau']

@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display = ['username', 'nom_complet', 'role', 'est_actif_cie', 'matricule']
    list_filter = ['role', 'est_actif_cie', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('CIE Manager', {'fields': ('matricule', 'telephone', 'role', 'photo', 'est_actif_cie')}),
    )
