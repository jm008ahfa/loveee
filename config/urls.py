from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("letters.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = "letters.views.custom_404"
handler500 = "letters.views.custom_500"

admin.site.site_header = "To My Love — Admin"
admin.site.site_title = "To My Love"
admin.site.index_title = "Letters, themes and music"
