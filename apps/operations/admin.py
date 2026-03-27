from django.contrib import admin
from .models import (
    Dossier, Activite, ActiviteActeur, CommentaireActivite,
    HistoriqueActivite, TypeDocument, DocumentActivite
)


class ActiviteActeurInline(admin.TabularInline):
    model = ActiviteActeur
    extra = 1


class DocumentActiviteInline(admin.TabularInline):
    model = DocumentActivite
    extra = 0
    fields = ['type_document', 'etat', 'date_prevue', 'observations']


@admin.register(TypeDocument)
class TypeDocumentAdmin(admin.ModelAdmin):
    list_display  = ['code', 'libelle', 'categorie', 'actif', 'ordre']
    list_editable = ['actif', 'ordre']
    list_filter   = ['categorie', 'actif']
    ordering      = ['categorie', 'ordre']


@admin.register(Dossier)
class DossierAdmin(admin.ModelAdmin):
    list_display = ['titre', 'section', 'est_actif', 'nb_activites', 'created_at']
    list_filter  = ['section__sous_direction', 'est_actif']


@admin.register(Activite)
class ActiviteAdmin(admin.ModelAdmin):
    list_display  = ['titre', 'section', 'statut', 'etat_avancement', 'date_butoir', 'est_dans_delai']
    list_filter   = ['statut', 'section__sous_direction', 'type_activite', 'est_dans_delai']
    inlines       = [ActiviteActeurInline, DocumentActiviteInline]
    search_fields = ['titre']


@admin.register(DocumentActivite)
class DocumentActiviteAdmin(admin.ModelAdmin):
    list_display  = ['type_document', 'activite', 'etat', 'mis_a_jour_par', 'mis_a_jour_le']
    list_filter   = ['etat', 'type_document__categorie']
    search_fields = ['activite__titre', 'type_document__libelle']


@admin.register(CommentaireActivite)
class CommentaireAdmin(admin.ModelAdmin):
    list_display = ['activite', 'auteur', 'type_comment', 'avancement', 'created_at']
