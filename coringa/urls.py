from django.urls import path
from django.contrib.auth import views as auth_views
from coringa.views import Home, Cadastro, Editar, Desativar, Detalhes, Historico, HistoricoDetalhes, Ativar, BillingAccounting, LogsAAA

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='coringa/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', Home, name='home'),
    path('cadastro/', Cadastro, name='Cadastro'),
    path('editar/<int:pk>/', Editar, name="editar"),
    path('desativar/<int:pk>/', Desativar, name="desativar"),
    path('detalhes/<int:pk>/', Detalhes, name="detalhes"),
    path('historico/', Historico, name="historico"),
    path('historico/detalhes/<int:pk>/', HistoricoDetalhes, name="historico_detalhes"),
    path('ativar/<int:pk>/', Ativar, name="ativar"),
    path('logs/', LogsAAA, name="logs_aaa"),
    path('api/billing/accounting/', BillingAccounting, name="billing_accounting"),
]
