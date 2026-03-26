from django.urls import path
from . import views

app_name = 'organisation'

urlpatterns = [
    # Portail Sous-Directions
    path('sous-directions/',                        views.SousDirectionPortailView.as_view(), name='sd_portail'),
    path('sous-directions/<int:pk>/',               views.SousDirectionDetailView.as_view(),  name='sd_detail'),
    path('sous-directions/creer/',                  views.SousDirectionCreateView.as_view(),  name='sd_create'),
    path('sous-directions/<int:pk>/modifier/',      views.SousDirectionUpdateView.as_view(),  name='sd_update'),
    # Sections
    path('sections/',                               views.SectionListView.as_view(),          name='section_list'),
    path('sections/<int:pk>/',                      views.SectionDetailView.as_view(),        name='section_detail'),
    path('sections/creer/',                         views.SectionCreateView.as_view(),        name='section_create'),
    path('sections/<int:pk>/modifier/',             views.SectionUpdateView.as_view(),        name='section_update'),
    # PIP
    path('pip/',                                    views.PIPListView.as_view(),              name='pip_list'),
    path('pip/creer/',                              views.PIPCreateView.as_view(),            name='pip_create'),
    path('pip/<int:pk>/modifier/',                  views.PIPUpdateView.as_view(),            name='pip_update'),
]
