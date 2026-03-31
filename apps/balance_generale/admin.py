from django.contrib import admin
from .models import BgImport, BgLigne, BgAlerte, BgAgregat, BgAuditTrail, BgRegleAlerte


@admin.register(BgRegleAlerte)
class BgRegleAlerteAdmin(admin.ModelAdmin):
    list_display  = ['code', 'libelle', 'niveau', 'seuil', 'active', 'ordre']
    list_editable = ['active', 'seuil', 'ordre']
    list_filter   = ['niveau', 'active']
    ordering      = ['ordre']


class BgAlerteInline(admin.TabularInline):
    model  = BgAlerte
    extra  = 0
    fields = ['niveau', 'code_regle', 'message', 'statut']
    readonly_fields = ['niveau', 'code_regle', 'message']


@admin.register(BgImport)
class BgImportAdmin(admin.ModelAdmin):
    list_display    = ['__str__', 'statut', 'nb_lignes', 'nb_anomalies', 'importe_par', 'date_import']
    list_filter     = ['statut', 'exercice']
    readonly_fields = ['date_import', 'importe_par', 'valide_par', 'date_validation']
    inlines         = [BgAlerteInline]


@admin.register(BgAlerte)
class BgAlerteAdmin(admin.ModelAdmin):
    list_display  = ['bg_import', 'niveau', 'code_regle', 'num_compte', 'statut']
    list_filter   = ['niveau', 'statut']
    search_fields = ['code_regle', 'message', 'num_compte']


@admin.register(BgAuditTrail)
class BgAuditTrailAdmin(admin.ModelAdmin):
    list_display = ['bg_import', 'action', 'utilisateur', 'created_at']
    list_filter  = ['action']
    readonly_fields = ['created_at']
