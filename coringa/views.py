from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .forms import ClienteForm, IPFormSet
from coringa.models import Cliente, ClienteIP

def Home(request):
    clientes_list = Cliente.objects.order_by('data_expiracao')
    paginator = Paginator(clientes_list, 10)
    
    page = request.GET.get('page')
    try:
        clientes = paginator.page(page)
    except PageNotAnInteger:
        clientes = paginator.page(1)
    except EmptyPage:
        clientes = paginator.page(paginator.num_pages)

    context = { 
        'user': str(request.user),
        'clientes': clientes,
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

def Desativar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    cliente.status = 'inativo'
    cliente.save()
    return redirect('home')

def Detalhes(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    ips = ClienteIP.objects.filter(cliente=cliente)
    context = { 
        'user': str(request.user),
        'cliente': cliente,
        'ips': ips
    }
    return render(request, 'coringa/detalhes.html', context)