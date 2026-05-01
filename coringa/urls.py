from django.urls import path
from coringa.views import Home

urlpatterns = [
    path('', Home, name='home')
]
