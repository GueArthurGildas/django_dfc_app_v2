from django.contrib import admin
from .models import Dossier, Activite, ActiviteActeur, CommentaireActivite, HistoriqueActivite

class ActiviteActeurInline(admin.TabularInline):
    model = ActiviteActeur
    extra = 1

@admin.register(Dossier)
class DossierAdmin(admin.ModelAdmin):
    list_display = ['titre', 'section', 'est_actif', 'nb_activites', 'created_at']
    list_filter  = ['section__sous_direction', 'est_actif']

@admin.register(Activite)
class ActiviteAdmin(admin.ModelAdmin):
    list_display  = ['titre', 'section', 'statut', 'etat_avancement', 'date_butoir', 'est_dans_delai']
    list_filter   = ['statut', 'section__sous_direction', 'type_activite', 'est_dans_delai']
    inlines       = [ActiviteActeurInline]
    search_fields = ['titre']

@admin.register(CommentaireActivite)
class CommentaireAdmin(admin.ModelAdmin):
    list_display = ['activite', 'auteur', 'type_comment', 'avancement', 'created_at']
