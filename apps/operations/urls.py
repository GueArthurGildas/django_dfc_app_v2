from django.urls import path
from . import views

app_name = 'operations'

urlpatterns = [
    # Dossiers
    path('dossiers/',                        views.DossierListView.as_view(),    name='dossier_list'),
    path('dossiers/creer/',                  views.DossierCreateView.as_view(),  name='dossier_create'),
    path('dossiers/<int:pk>/',               views.DossierDetailView.as_view(),  name='dossier_detail'),
    path('dossiers/<int:pk>/modifier/',      views.DossierUpdateView.as_view(),  name='dossier_update'),
    # Activités
    path('activites/',                       views.ActiviteListView.as_view(),   name='activite_list'),
    path('activites/creer/',                 views.ActiviteCreateView.as_view(), name='activite_create'),
    path('activites/kanban/',                views.ActiviteKanbanView.as_view(), name='activite_kanban'),
    path('activites/<int:pk>/',              views.ActiviteDetailView.as_view(), name='activite_detail'),
    path('activites/<int:pk>/modifier/',     views.ActiviteUpdateView.as_view(), name='activite_update'),
    path('activites/<int:pk>/clore/',        views.CloreActiviteView.as_view(),  name='activite_clore'),
    path('activites/<int:pk>/reporter/',     views.ReporterDateView.as_view(),   name='activite_reporter'),
    path('activites/<int:pk>/commenter/',    views.CommenterView.as_view(),      name='activite_commenter'),
    path('activites/<int:pk>/cloner/',       views.ClonerActiviteView.as_view(), name='activite_cloner'),
    path('activites/<int:pk>/statut/',       views.ChangerStatutView.as_view(),  name='activite_statut'),
    # Documents
    path('activites/<int:pk>/documents/ajouter/',         views.AjouterDocumentActiviteView.as_view(), name='document_ajouter'),
    path('activites/<int:pk>/documents/<int:doc_pk>/statut/', views.ChangerStatutDocView.as_view(), name='document_statut'),
    path('activites/<int:pk>/documents/<int:doc_pk>/supprimer/', views.SupprimerDocView.as_view(), name='document_supprimer'),
    # API JSON pour dashboard
    path('api/stats/',                       views.StatsAPIView.as_view(),       name='api_stats'),
]
