from django.urls import path

from . import views

urlpatterns = [
    path("", views.my_profile, name="profile"),
    path("unsubscribe/<uuid:token>/", views.unsubscribe, name="unsubscribe"),
]
