from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('apps.authentication.urls')),
    path('organisation/', include('apps.organisation.urls')),
    path('operations/', include('apps.operations.urls')),
    path('comptabilite/', include('apps.comptabilite.urls')),
    path('sdcc/', include('apps.organisation.modules.sdcc.urls')),
    path('sdpcc/', include('apps.organisation.modules.sdpcc.urls')),
    path('balance-generale/', include('apps.balance_generale.urls', namespace='bg')),
    path('', include('apps.dashboard.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
