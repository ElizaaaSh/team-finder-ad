from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from projects import views as project_views
from projects.views import root_redirect

urlpatterns = [
    path("", root_redirect, name="home"),
    path("admin/", admin.site.urls),
    path("projects/", include("projects.urls")),
    path("users/", include("users.urls")),
    # Alias from the task text: /project/list/ should behave like the projects list.
    path("project/list/", project_views.project_list),
    path("project/list", project_views.project_list),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
