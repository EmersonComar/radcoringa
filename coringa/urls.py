from django.urls import path
from coringa.views import Home, Cadastro, Editar, Desativar

urlpatterns = [
    path('', Home, name='home'),
    path('cadastro/', Cadastro, name='Cadastro'),
    path('editar/<int:pk>/', Editar, name="editar"),
    path('desativar/<int:pk>/', Desativar, name="desativar"),
]
