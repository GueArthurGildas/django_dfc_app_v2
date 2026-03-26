from django.urls import path
from . import views

app_name = 'operations'

urlpatterns = [
    path('dossiers/',          views.DossierListView.as_view(),    name='dossier_list'),
    path('activites/',         views.ActiviteListView.as_view(),   name='activite_list'),
    path('activites/kanban/',  views.ActiviteKanbanView.as_view(), name='activite_kanban'),
]
