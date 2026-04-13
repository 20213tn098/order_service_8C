from django.urls import path
from .views import RegistroView, LoginView, PerfilView

urlpatterns = [
    path('register/',          RegistroView.as_view(), name='registro'),
    path('login/',             LoginView.as_view(),    name='login'),
    path('<int:id>/profile/',  PerfilView.as_view(),   name='perfil'),
]