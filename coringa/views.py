import os
import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.contrib.auth import views as auth_views
from django.core.cache import cache

from .forms import ClienteForm, IPFormSet
from coringa.models import Cliente, ClienteIP, Radpostauth, Radacct

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

def BillingAccounting(request):
    expected_token = os.getenv('BILLING_API_TOKEN')
    
    auth_header = request.headers.get('Authorization')
    token = None
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split('Bearer ')[1]
    else:
        token = request.GET.get('token')
        
    if not token or token != expected_token:
        return JsonResponse({
            'success': False,
            'error': 'Não autorizado. Token inválido ou ausente.'
        }, status=401)
        
    cliente_id = request.GET.get('cliente_id')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    ip = request.GET.get('ip')
    status = request.GET.get('status')
    
    queryset = Radacct.objects.all()
    
    if cliente_id:
        try:
            cliente = Cliente.objects.get(pk=cliente_id)
            client_ips = list(cliente.Lista_ips.values_list('endereco_ip', flat=True))
            clean_ips = [ip.split('/')[0] for ip in client_ips]
            queryset = queryset.filter(nasipaddress__in=clean_ips)
        except Cliente.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'Cliente com ID {cliente_id} não encontrado.'
            }, status=404)
            
    if ip:
        queryset = queryset.filter(nasipaddress=ip)
        
    if data_inicio:
        dt_start = parse_datetime(data_inicio)
        if dt_start:
            queryset = queryset.filter(acctstarttime__gte=dt_start)
    if data_fim:
        dt_end = parse_datetime(data_fim)
        if dt_end:
            queryset = queryset.filter(acctstarttime__lte=dt_end)
            
    if status == 'active':
        queryset = queryset.filter(acctstoptime__isnull=True)
    elif status == 'closed':
        queryset = queryset.filter(acctstoptime__isnull=False)
        
    queryset = queryset.order_by('-acctstarttime')[:1000]
    
    data = []
    all_clients = Cliente.objects.all().prefetch_related('Lista_ips')
    ip_to_client_name = {}
    for c in all_clients:
        for ip_obj in c.Lista_ips.all():
            ip_to_client_name[ip_obj.endereco_ip.split('/')[0]] = c.nome
            
    for record in queryset:
        client_name = ip_to_client_name.get(record.nasipaddress, 'Desconhecido')
        data.append({
            'acctsessionid': record.acctsessionid,
            'acctuniqueid': record.acctuniqueid,
            'cliente_nome': client_name,
            'username': record.username,
            'nasipaddress': record.nasipaddress,
            'framedipaddress': record.framedipaddress,
            'acctstarttime': record.acctstarttime.isoformat() if record.acctstarttime else None,
            'acctstoptime': record.acctstoptime.isoformat() if record.acctstoptime else None,
            'acctsessiontime': record.acctsessiontime,
            'acctinputoctets': record.acctinputoctets,
            'acctoutputoctets': record.acctoutputoctets,
            'acctterminatecause': record.acctterminatecause,
        })
        
    return JsonResponse({
        'success': True,
        'count': len(data),
        'data': data
    })

@login_required
def LogsAAA(request):
    cliente_id = request.GET.get('cliente')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    status_reply = request.GET.get('status')
    username = request.GET.get('username')
    
    queryset = Radpostauth.objects.all()
    
    if cliente_id:
        try:
            cliente = Cliente.objects.get(pk=cliente_id)
            client_ips = list(cliente.Lista_ips.values_list('endereco_ip', flat=True))
            clean_ips = [ip.split('/')[0] for ip in client_ips]
            queryset = queryset.filter(nas_ip_address__in=clean_ips)
        except Cliente.DoesNotExist:
            pass
            
    if data_inicio:
        dt_start = parse_datetime(data_inicio)
        if dt_start:
            if timezone.is_naive(dt_start):
                dt_start = timezone.make_aware(dt_start, timezone.get_current_timezone())
            queryset = queryset.filter(authdate__gte=dt_start)
    if data_fim:
        dt_end = parse_datetime(data_fim)
        if dt_end:
            if timezone.is_naive(dt_end):
                dt_end = timezone.make_aware(dt_end, timezone.get_current_timezone())
            queryset = queryset.filter(authdate__lte=dt_end)
            
    if status_reply:
        queryset = queryset.filter(reply=status_reply)
        
    if username:
        queryset = queryset.filter(username__icontains=username)
        
    queryset = queryset.order_by('-authdate')
    
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="logs_aaa_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        response.write('\ufeff'.encode('utf8'))
        
        writer = csv.writer(response, delimiter=';')
        writer.writerow(['Data/Hora', 'Provedor', 'Usuário', 'Senha Usada', 'IP do NAS (CCR)', 'Status/Resposta'])
        
        all_clients = Cliente.objects.all().prefetch_related('Lista_ips')
        ip_to_client_name = {}
        for c in all_clients:
            for ip_obj in c.Lista_ips.all():
                ip_to_client_name[ip_obj.endereco_ip.split('/')[0]] = c.nome
                
        for log in queryset[:5000]:
            client_name = ip_to_client_name.get(log.nas_ip_address, 'Desconhecido')
            writer.writerow([
                log.authdate.astimezone(timezone.get_current_timezone()).strftime('%d/%m/%Y %H:%M:%S') if log.authdate else '',
                client_name,
                log.username,
                log.pass_field,
                log.nas_ip_address,
                log.reply
            ])
        return response
        
    paginator = Paginator(queryset, 20)
    page = request.GET.get('page')
    try:
        logs = paginator.page(page)
    except PageNotAnInteger:
        logs = paginator.page(1)
    except EmptyPage:
        logs = paginator.page(paginator.num_pages)
        
    clientes = Cliente.objects.all().order_by('nome')
    
    all_clients = Cliente.objects.all().prefetch_related('Lista_ips')
    ip_to_client_name = {}
    for c in all_clients:
        for ip_obj in c.Lista_ips.all():
            ip_to_client_name[ip_obj.endereco_ip.split('/')[0]] = c.nome
            
    for log in logs:
        log.cliente_nome = ip_to_client_name.get(log.nas_ip_address, 'Desconhecido')
        
    context = {
        'user': str(request.user),
        'logs': logs,
        'clientes': clientes,
        'filtered_cliente': int(cliente_id) if cliente_id and cliente_id.isdigit() else None,
        'filtered_data_inicio': data_inicio,
        'filtered_data_fim': data_fim,
        'filtered_status': status_reply,
        'filtered_username': username,
    }
    
    return render(request, 'coringa/logs.html', context)


class CoringaLoginView(auth_views.LoginView):
    template_name = 'coringa/login.html'
    
    def dispatch(self, request, *args, **kwargs):
        if request.method == 'POST':
            ip = request.META.get('REMOTE_ADDR')
            cache_key = f"login_attempts_{ip}"
            attempts = cache.get(cache_key, 0)
            
            if attempts >= 5:
                return render(request, self.template_name, {
                    'form': self.get_form(),
                    'error_message': 'Muitas tentativas de login. Por favor, aguarde 1 minuto.'
                }, status=429)
                
        return super().dispatch(request, *args, **kwargs)
        
    def form_invalid(self, form):
        ip = self.request.META.get('REMOTE_ADDR')
        cache_key = f"login_attempts_{ip}"
        attempts = cache.get(cache_key, 0)
        cache.set(cache_key, attempts + 1, timeout=60)
        return super().form_invalid(form)
        
    def form_valid(self, form):
        ip = self.request.META.get('REMOTE_ADDR')
        cache_key = f"login_attempts_{ip}"
        cache.delete(cache_key)
        return super().form_valid(form)