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

from .models import Annonce

@admin.register(Annonce)
class AnnonceAdmin(admin.ModelAdmin):
    list_display  = ['titre', 'date_debut', 'date_fin', 'actif', 'created_by']
    list_editable = ['actif']
    list_filter   = ['actif']
    search_fields = ['titre', 'description']
    readonly_fields = ['created_at']
    fieldsets = [
        ('Contenu', {'fields': ['titre', 'description', 'image']}),
        ('Période d\'affichage', {'fields': ['date_debut', 'date_fin', 'actif']}),
        ('Méta', {'fields': ['created_by', 'created_at']}),
    ]
