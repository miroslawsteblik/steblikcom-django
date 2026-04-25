from django.urls import path

from . import views

app_name = "pages"

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("experience/", views.experience, name="experience"),
    path("references/", views.references, name="references"),
    path("robots.txt", views.robots_txt, name="robots_txt"),
]
