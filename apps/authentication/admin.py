from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur, Role, Annonce


class UtilisateurSectionInline(admin.TabularInline):
    """Permet d'affecter un utilisateur à une section directement depuis sa fiche."""
    from apps.organisation.models import UtilisateurSection
    model = __import__('apps.organisation.models', fromlist=['UtilisateurSection']).UtilisateurSection
    extra = 1
    fields = ['section', 'est_principale']
    verbose_name = "Affectation à une section"
    verbose_name_plural = "Affectations aux sections"


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display  = ['username', 'nom_complet', 'matricule', 'role', 'get_sd', 'est_actif_cie', 'is_active']
    list_filter   = ['role', 'est_actif_cie', 'is_active']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'matricule']
    ordering      = ['last_name', 'first_name']
    list_editable = ['est_actif_cie']
    inlines       = [UtilisateurSectionInline]

    fieldsets = (
        ('Identité', {'fields': ('username', 'password')}),
        ('Informations personnelles', {'fields': (
            'first_name', 'last_name', 'email',
            'matricule', 'photo',
        )}),
        ('Rôle & Statut CIE', {'fields': ('role', 'est_actif_cie')}),
        ('Permissions Django', {'fields': ('is_active', 'is_staff', 'is_superuser'), 'classes': ('collapse',)}),
        ('Dates', {'fields': ('last_login', 'date_joined'), 'classes': ('collapse',)}),
    )

    add_fieldsets = (
        ('Créer un utilisateur', {
            'classes': ('wide',),
            'fields': (
                'username', 'first_name', 'last_name', 'email',
                'matricule', 'role', 'est_actif_cie',
                'password1', 'password2',
            ),
        }),
    )

    def get_sd(self, obj):
        sd = obj.get_sous_direction()
        return sd.code if sd else '—'
    get_sd.short_description = 'Sous-Direction'


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['code', 'libelle', 'niveau']
    ordering     = ['niveau']


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
