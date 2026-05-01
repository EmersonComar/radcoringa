from coringa.models import Cliente
from django.shortcuts import render

def Home(request): 
    context = {
        'user': str(request.user),
        'clientes': Cliente.objects.filter(status='ativo')
    }
    return render(request, 'coringa/home.html', context)