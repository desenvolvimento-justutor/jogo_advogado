from django.urls import path

from . import views

app_name = "site_publico"

urlpatterns = [
    path("", views.home, name="home"),
    path("premium/", views.planos, name="planos"),
    path("area-gratuita/", views.area_gratuita, name="area_gratuita"),
    path("minha-conta/", views.minha_conta, name="minha_conta"),
]
