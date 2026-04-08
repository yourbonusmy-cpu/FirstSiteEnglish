from django.urls import path

from apps.social import views

app_name = "social"

urlpatterns = [
    path("toggle-like/<int:pk>/", views.toggle_like, name="toggle_like"),
]
