from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required

from .forms import ClienteForm, IPFormSet
from coringa.models import Cliente, ClienteIP, Radpostauth

@login_required
def Home(request):
    from django.utils import timezone
    expired_clientes = Cliente.objects.filter(status='ativo', data_expiracao__lte=timezone.now())
    for cliente in expired_clientes:
        cliente.status = 'expirado'
        cliente.save()
    
    clientes_list = Cliente.objects.filter(status='ativo').order_by('data_expiracao')
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
        'total': Cliente.objects.filter(status='ativo').count()
    }

    return render(request, 'coringa/home.html', context)

@login_required
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

@login_required
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

@login_required
def Desativar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    cliente.status = 'inativo'
    cliente.save()
    return redirect('home')

@login_required
def Detalhes(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    ips = ClienteIP.objects.filter(cliente=cliente)
    
    # Busca logs baseados nas strings exatas de IP salvas
    ip_list = ips.values_list('endereco_ip', flat=True)
    logs = Radpostauth.objects.filter(nas_ip_address__in=ip_list).order_by('-authdate')[:5]
    
    context = { 
        'user': str(request.user),
        'cliente': cliente,
        'ips': ips,
        'logs': logs
    }
    return render(request, 'coringa/detalhes.html', context)

@login_required
def Historico(request):
    from django.utils import timezone
    expired_clientes = Cliente.objects.filter(status='ativo', data_expiracao__lte=timezone.now())
    for cliente in expired_clientes:
        cliente.status = 'expirado'
        cliente.save()
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
    return render(request, 'coringa/historico.html', context)

@login_required
def HistoricoDetalhes(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    ips = ClienteIP.objects.filter(cliente=cliente)
    context = { 
        'user': str(request.user),
        'cliente': cliente,
        'ips': ips
    }
    return render(request, 'coringa/historico_detalhes.html', context)

@login_required
def Ativar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    cliente.status = 'ativo'
    cliente.save()
    return redirect('historico')

def error_404(request, exception):
    return render(request, 'coringa/404.html', status=404)

def error_403(request, exception):
    return render(request, 'coringa/403.html', status=403)

def error_500(request):
    return render(request, 'coringa/500.html', status=500)