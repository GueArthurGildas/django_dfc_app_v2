from django.urls import path
from . import views

app_name = 'bg'

urlpatterns = [
    path('',                                    views.BgDashboardView.as_view(),     name='dashboard'),
    path('import/',                             views.BgImportView.as_view(),        name='import'),
    path('imports/',                            views.BgListeImportsView.as_view(),  name='imports'),
    path('imports/<int:pk>/',                   views.BgDetailView.as_view(),        name='detail'),
    path('imports/<int:pk>/valider/',           views.BgValiderView.as_view(),       name='valider'),
    path('imports/<int:pk>/comptes/',           views.BgComptesView.as_view(),       name='comptes'),
    path('imports/<int:pk>/export/excel/',      views.BgExportExcelView.as_view(),   name='export_excel'),
    path('imports/<int:pk>/alertes/<int:alerte_pk>/traiter/', views.BgTraiterAlerteView.as_view(), name='traiter_alerte'),
    path('imports/<int:pk>/api/kpis/',          views.BgApiKpisView.as_view(),       name='api_kpis'),
    path('imports/<int:pk>/supprimer/',         views.BgSupprimerView.as_view(),     name='supprimer'),
]
