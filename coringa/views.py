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
from coringa.models import Cliente, ClienteIP, Radpostauth, Radacct, Radippool
from django.db import models as django_models

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
    
    # Busca logs baseados nas strings de IP salvas
    ip_list = ips.values_list('endereco_ip', flat=True)
    clean_ips = [ip.split('/')[0] for ip in ip_list]
    todos_logs = obter_logs_unificados(clean_ips=clean_ips, limit=1000)
    
    pool_data = None
    pool_info = ""
    if cliente.habilitar_pool:
        pool_name = f"{cliente.nome}_{cliente.pool_name_input}"
        total_ips = Radippool.objects.filter(pool_name=pool_name).count()
        free_ips = Radippool.objects.filter(
            pool_name=pool_name
        ).filter(
            django_models.Q(username='') | django_models.Q(username__isnull=True) | django_models.Q(expiry_time__lt=timezone.now())
        ).count()
        pool_info = f" (Pool: {free_ips}/{total_ips} livres)"
        pool_data = {
            'nome': pool_name,
            'total': total_ips,
            'livres': free_ips,
            'ocupados': total_ips - free_ips,
            'bloco': cliente.pool_block,
        }

    for log in todos_logs:
        log['cliente_nome'] = f"{cliente.nome}{pool_info}"
        
    paginator = Paginator(todos_logs, 10)
    page = request.GET.get('page')
    try:
        logs = paginator.page(page)
    except PageNotAnInteger:
        logs = paginator.page(1)
    except EmptyPage:
        logs = paginator.page(paginator.num_pages)
    
    context = { 
        'user': str(request.user),
        'cliente': cliente,
        'ips': ips,
        'logs': logs,
        'pool_data': pool_data
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
    
    # Busca logs baseados nas strings de IP salvas
    ip_list = ips.values_list('endereco_ip', flat=True)
    clean_ips = [ip.split('/')[0] for ip in ip_list]
    todos_logs = obter_logs_unificados(clean_ips=clean_ips, limit=1000)
    
    pool_data = None
    pool_info = ""
    if cliente.habilitar_pool:
        pool_name = f"{cliente.nome}_{cliente.pool_name_input}"
        total_ips = Radippool.objects.filter(pool_name=pool_name).count()
        free_ips = Radippool.objects.filter(
            pool_name=pool_name
        ).filter(
            django_models.Q(username='') | django_models.Q(username__isnull=True) | django_models.Q(expiry_time__lt=timezone.now())
        ).count()
        pool_info = f" (Pool: {free_ips}/{total_ips} livres)"
        pool_data = {
            'nome': pool_name,
            'total': total_ips,
            'livres': free_ips,
            'ocupados': total_ips - free_ips,
            'bloco': cliente.pool_block,
        }

    for log in todos_logs:
        log['cliente_nome'] = f"{cliente.nome}{pool_info}"
        
    paginator = Paginator(todos_logs, 10)
    page = request.GET.get('page')
    try:
        logs = paginator.page(page)
    except PageNotAnInteger:
        logs = paginator.page(1)
    except EmptyPage:
        logs = paginator.page(paginator.num_pages)
    
    context = { 
        'user': str(request.user),
        'cliente': cliente,
        'ips': ips,
        'logs': logs,
        'pool_data': pool_data
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

def obter_logs_unificados(clean_ips=None, dt_start=None, dt_end=None, status_reply=None, username=None, log_type='ambos', limit=2000):
    logs_postauth = []
    logs_acct = []
    
    # 1. Buscar Radpostauth se aplicável
    if log_type in ('ambos', 'auth') and status_reply not in ('Acct-Active', 'Acct-Stop'):
        qs = Radpostauth.objects.all()
        if clean_ips is not None:
            qs = qs.filter(nas_ip_address__in=clean_ips)
        if dt_start:
            qs = qs.filter(authdate__gte=dt_start)
        if dt_end:
            qs = qs.filter(authdate__lte=dt_end)
        if status_reply and status_reply in ('Access-Accept', 'Access-Reject'):
            qs = qs.filter(reply=status_reply)
        if username:
            qs = qs.filter(username__icontains=username)
            
        qs = qs.order_by('-authdate')[:limit]
        
        for log in qs:
            logs_postauth.append({
                'date': log.authdate,
                'tipo': 'Autenticação',
                'nas_ip': log.nas_ip_address,
                'username': log.username,
                'detalhe': log.pass_field,
                'status': log.reply,
                'is_auth': True,
            })
            
    # 2. Buscar Radacct se aplicável
    if log_type in ('ambos', 'acct') and status_reply not in ('Access-Accept', 'Access-Reject'):
        qs = Radacct.objects.all()
        if clean_ips is not None:
            qs = qs.filter(nasipaddress__in=clean_ips)
        if dt_start:
            qs = qs.filter(acctstarttime__gte=dt_start)
        if dt_end:
            qs = qs.filter(acctstarttime__lte=dt_end)
        if status_reply:
            if status_reply == 'Acct-Active':
                qs = qs.filter(acctstoptime__isnull=True)
            elif status_reply == 'Acct-Stop':
                qs = qs.filter(acctstoptime__isnull=False)
        if username:
            qs = qs.filter(username__icontains=username)
            
        qs = qs.order_by('-acctstarttime')[:limit]
        
        for log in qs:
            detalhe = f"IP: {log.framedipaddress}" if log.framedipaddress else "IP: N/A"
            if log.acctsessiontime:
                seconds = log.acctsessiontime
                hours = seconds // 3600
                minutes = (seconds % 3600) // 60
                remaining_seconds = seconds % 60
                duration_str = ""
                if hours > 0:
                    duration_str += f"{hours}h "
                if minutes > 0 or hours > 0:
                    duration_str += f"{minutes}m "
                duration_str += f"{remaining_seconds}s"
                detalhe += f" | {duration_str}"
                
            status_str = "Acct-Active" if not log.acctstoptime else "Acct-Stop"
            if log.acctstoptime and log.acctterminatecause:
                status_str += f" ({log.acctterminatecause})"
                
            logs_acct.append({
                'date': log.acctstarttime or timezone.now(),
                'tipo': 'Contabilidade',
                'nas_ip': log.nasipaddress,
                'username': log.username,
                'detalhe': detalhe,
                'status': status_str,
                'is_auth': False,
            })
            
    todos_logs = logs_postauth + logs_acct
    todos_logs.sort(key=lambda x: x['date'], reverse=True)
    return todos_logs

def obter_stats_pools():
    pool_stats = {}
    clientes = Cliente.objects.filter(status='ativo', habilitar_pool=True)
    for c in clientes:
        pool_name = f"{c.nome}_{c.pool_name_input}"
        total_ips = Radippool.objects.filter(pool_name=pool_name).count()
        free_ips = Radippool.objects.filter(
            pool_name=pool_name
        ).filter(
            django_models.Q(username='') | django_models.Q(username__isnull=True) | django_models.Q(expiry_time__lt=timezone.now())
        ).count()
        pool_stats[c.nome] = f" (Pool: {free_ips}/{total_ips} livres)"
    return pool_stats

@login_required
def LogsAAA(request):
    cliente_id = request.GET.get('cliente')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    status_reply = request.GET.get('status')
    username = request.GET.get('username')
    log_type = request.GET.get('log_type', 'ambos')
    
    clean_ips = None
    if cliente_id:
        try:
            cliente = Cliente.objects.get(pk=cliente_id)
            client_ips = list(cliente.Lista_ips.values_list('endereco_ip', flat=True))
            clean_ips = [ip.split('/')[0] for ip in client_ips]
        except Cliente.DoesNotExist:
            pass
            
    dt_start = None
    if data_inicio:
        dt_start = parse_datetime(data_inicio)
        if dt_start and timezone.is_naive(dt_start):
            dt_start = timezone.make_aware(dt_start, timezone.get_current_timezone())
            
    dt_end = None
    if data_fim:
        dt_end = parse_datetime(data_fim)
        if dt_end and timezone.is_naive(dt_end):
            dt_end = timezone.make_aware(dt_end, timezone.get_current_timezone())
            
    # Obter logs unificados
    limit = 5000 if request.GET.get('export') == 'csv' else 2000
    todos_logs = obter_logs_unificados(
        clean_ips=clean_ips,
        dt_start=dt_start,
        dt_end=dt_end,
        status_reply=status_reply,
        username=username,
        log_type=log_type,
        limit=limit
    )
    
    # Preencher nome do cliente
    all_clients = Cliente.objects.all().prefetch_related('Lista_ips')
    ip_to_client_name = {}
    for c in all_clients:
        for ip_obj in c.Lista_ips.all():
            ip_to_client_name[ip_obj.endereco_ip.split('/')[0]] = c.nome
            
    pool_stats = obter_stats_pools()
    for log in todos_logs:
        client_name = ip_to_client_name.get(log['nas_ip'], 'Desconhecido')
        pool_info = pool_stats.get(client_name, '')
        log['cliente_nome'] = f"{client_name}{pool_info}"
        
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="logs_aaa_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        response.write('\ufeff'.encode('utf8'))
        
        writer = csv.writer(response, delimiter=';')
        writer.writerow(['Data/Hora', 'Tipo', 'Provedor', 'Usuário', 'Senha/IP Concedido', 'IP do NAS (CCR)', 'Status/Resposta'])
        
        for log in todos_logs[:5000]:
            writer.writerow([
                log['date'].astimezone(timezone.get_current_timezone()).strftime('%d/%m/%Y %H:%M:%S') if log['date'] else '',
                log['tipo'],
                log['cliente_nome'],
                log['username'],
                log['detalhe'],
                log['nas_ip'],
                log['status']
            ])
        return response
        
    paginator = Paginator(todos_logs, 20)
    page = request.GET.get('page')
    try:
        logs = paginator.page(page)
    except PageNotAnInteger:
        logs = paginator.page(1)
    except EmptyPage:
        logs = paginator.page(paginator.num_pages)
        
    clientes = Cliente.objects.all().order_by('nome')
    
    context = {
        'user': str(request.user),
        'logs': logs,
        'clientes': clientes,
        'filtered_cliente': int(cliente_id) if cliente_id and cliente_id.isdigit() else None,
        'filtered_data_inicio': data_inicio,
        'filtered_data_fim': data_fim,
        'filtered_status': status_reply,
        'filtered_username': username,
        'filtered_log_type': log_type,
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