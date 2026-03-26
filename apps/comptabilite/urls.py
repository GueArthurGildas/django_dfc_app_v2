from django.urls import path
from . import views

app_name = 'comptabilite'

urlpatterns = [
    path('balance/',     views.BalanceListView.as_view(),    name='balance_list'),
    path('grand-livre/', views.GrandLivreListView.as_view(), name='grand_livre_list'),
]
