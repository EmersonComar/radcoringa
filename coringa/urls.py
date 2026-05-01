from django.urls import path
from coringa.views import Home, Cadastro

urlpatterns = [
    path('', Home, name='home'),
    path('cadastro/', Cadastro, name='Cadastro')
]
