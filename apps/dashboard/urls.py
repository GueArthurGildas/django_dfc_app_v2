from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='index'),
    path('ia/chat/', views.IAChatView.as_view(), name='ia_chat'),
]
