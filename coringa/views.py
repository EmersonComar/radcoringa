from coringa.models import Cliente
from .forms import ClienteForm, IPFormSet
from django.shortcuts import render, redirect, get_object_or_404

def Home(request):
    context = {
        'user': str(request.user),
        'clientes': Cliente.objects.filter(status='ativo').order_by('data_expiracao'),
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

def Editar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        formset = IPFormSet(request.POST, instance=cliente)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('home')
    else:
        form = ClienteForm(instance=cliente)
        formset = IPFormSet(instance=cliente)

    return render(request, 'coringa/cadastro.html', {
        'cliente': cliente,
        'cadastro': form,
        'ips': formset,
    })