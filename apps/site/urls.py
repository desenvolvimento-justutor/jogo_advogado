from django.urls import path

from . import views

app_name = "site_publico"

urlpatterns = [
    path("", views.home, name="home"),
    path("premium/", views.planos, name="planos"),
]
