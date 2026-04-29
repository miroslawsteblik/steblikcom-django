from django.urls import path

from . import views

app_name = "pages"

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("experience/", views.experience, name="experience"),
    path("references/", views.references, name="references"),
    path("privacy/", views.privacy, name="privacy"),
    path("terms/", views.terms, name="terms"),
    path("legal/", views.legal, name="legal"),
    path("robots.txt", views.robots_txt, name="robots_txt"),
]
