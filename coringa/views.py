from coringa.models import Cliente
from .forms import ClienteForm, IPFormSet
from django.shortcuts import render, redirect

def Home(request): 

    context = {
        'user': str(request.user).upper(),
        'clientes': Cliente.objects.filter(status='ativo'),
        'total': Cliente.objects.count()
    }

    return render(request, 'coringa/home.html', context)

def Cadastro(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        formset = IPFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            cliente = form.save(commit=False)
            cliente.responsavel_cadastro = request.user
            cliente.save()
            formset.instance = cliente
            formset.save()
            return redirect('home')
    else:
        form = ClienteForm()
        formset = IPFormSet()
    
    return render(request, 'coringa/cadastro.html', {
        'cadastro': form,
        'ips': formset
    })