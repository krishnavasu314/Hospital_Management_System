from django.contrib import admin
from django.urls import include, path

from users.views import home


urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),
    path("", include("users.urls")),
    path("", include("appointments.urls")),
]
