import string
import secrets
from django.db import models
from ipaddress import IPv4Network
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def gerar_secret(tamanho=16):
    caracteres = string.ascii_letters + string.digits
    return ''.join(secrets.choice(caracteres) for _ in range(tamanho)) 

def validar_ip(valor):
    try:
        net = IPv4Network(valor, strict=False)
        if net.prefixlen < 24:
            raise ValidationError(
                _('Não é permitido cadastrar blocos de IP maiores que /24')
            )
    except (ValueError, TypeError):
        raise ValidationError(
            _('%(valor)s não é um IP/Rede válido'),
            params={'valor': valor},
        )

User = get_user_model()

class Cliente(models.Model):

    nome = models.CharField(
        max_length=100, 
        verbose_name="Razão social do provedor"
    )
    
    data_expiracao = models.DateTimeField(
        verbose_name="Data e hora da expiração"
    )
    
    secret = models.CharField(
        max_length=16, 
        default=gerar_secret, 
        unique=True, 
        editable=False, 
        verbose_name="Secret"
    )
    
    observacao = models.TextField(
        max_length=100, 
        blank=True, 
        null=True
    )

    responsavel_cadastro = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name="Cadastrado por",
        editable=False
    )

    data_cadastro = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de cadastro"
    )

    data_update = models.DateTimeField(
        auto_now=True,
        verbose_name="Data atualização"
    )
    
    class StatusOpcoes(models.TextChoices):
        ATIVO = 'ativo', _('Ativo')
        EXPIRADO = 'expirado', _('Expirado')
        DESATIVADO = 'desativado', _('Desativado')
        INATIVO = 'inativo', _('Inativo')

    status = models.CharField(
        max_length=10,
        choices=StatusOpcoes.choices,
        default=StatusOpcoes.ATIVO
    )

    class Meta:
        verbose_name = "Provedor de internet"
        verbose_name_plural = "Provedores de internet"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._old_nome = self.nome

    def __str__(self):
        return f"{self.nome}"

    def save(self, *args, **kwargs):
        from django.utils import timezone
        
        if self.status == 'ativo' and self.data_expiracao and self.data_expiracao <= timezone.now():
            self.status = self.StatusOpcoes.EXPIRADO
        elif self.status == 'expirado' and self.data_expiracao and self.data_expiracao > timezone.now():
            self.status = self.StatusOpcoes.ATIVO
        super().save(*args, **kwargs)
    
    
class ClienteIP(models.Model):

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        verbose_name='Provedor',
        related_name='Lista_ips'
    )

    endereco_ip = models.CharField(
        verbose_name='Endereço IP/Rede',
        validators=[validar_ip],
        help_text="Exemplo: 192.168.122.2",
        max_length=18
    )

    class Meta:
        verbose_name = 'IP do cliente'
        verbose_name_plural = 'IPs dos clientes'


    def clean(self):
        super().clean()
        if hasattr(self, 'cliente') and self.cliente:
            qs = ClienteIP.objects.filter(cliente=self.cliente)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.count() >= 5:
                raise ValidationError(_("Um provedor pode registrar no máximo 5 IPs públicos de CCR."))

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_endereco_ip = self.endereco_ip

    def __str__(self):
        return f"{self.endereco_ip}"


class Nas(models.Model):
    nasname = models.CharField(max_length=128)
    shortname = models.CharField(max_length=32, blank=True, null=True)
    type = models.CharField(max_length=30, default='other')
    ports = models.IntegerField(blank=True, null=True)
    secret = models.CharField(max_length=60, default='secret')
    server = models.CharField(max_length=64, blank=True, null=True)
    community = models.CharField(max_length=50, blank=True, null=True)
    description = models.CharField(max_length=200, default='RADIUS Client')

    class Meta:
        db_table = 'nas'
        managed = False

    def __str__(self):
        return f"{self.nasname} ({self.shortname})"


class Radcheck(models.Model):
    username = models.CharField(max_length=64, default='')
    attribute = models.CharField(max_length=64, default='')
    op = models.CharField(max_length=2, default='==')
    value = models.CharField(max_length=253, default='')

    class Meta:
        db_table = 'radcheck'
        managed = False

    def __str__(self):
        return f"{self.username}: {self.attribute} {self.op} {self.value}"


class Radpostauth(models.Model):
    username = models.CharField(max_length=64)
    pass_field = models.CharField(db_column='pass', max_length=64)
    reply = models.CharField(max_length=32)
    nas_ip_address = models.CharField(max_length=45, blank=True, null=True)
    authdate = models.DateTimeField()
    class_field = models.CharField(db_column='class', max_length=64, blank=True, null=True)

    class Meta:
        db_table = 'radpostauth'
        managed = False

    def __str__(self):
        return f"{self.authdate} - {self.username} - {self.reply}"


class Nasreload(models.Model):
    nasipaddress = models.CharField(max_length=15, primary_key=True)
    reloadtime = models.DateTimeField()

    class Meta:
        db_table = 'nasreload'
        managed = False

    def __str__(self):
        return f"{self.nasipaddress} - {self.reloadtime}"


class Radacct(models.Model):
    radacctid = models.BigAutoField(primary_key=True)
    acctsessionid = models.CharField(max_length=64, default='')
    acctuniqueid = models.CharField(max_length=32, default='', unique=True)
    username = models.CharField(max_length=64, default='')
    realm = models.CharField(max_length=64, blank=True, null=True, default='')
    nasipaddress = models.CharField(max_length=15, default='')
    nasportid = models.CharField(max_length=32, blank=True, null=True)
    nasporttype = models.CharField(max_length=32, blank=True, null=True)
    acctstarttime = models.DateTimeField(blank=True, null=True)
    acctupdatetime = models.DateTimeField(blank=True, null=True)
    acctstoptime = models.DateTimeField(blank=True, null=True)
    acctinterval = models.IntegerField(blank=True, null=True)
    acctsessiontime = models.PositiveIntegerField(blank=True, null=True)
    acctauthentic = models.CharField(max_length=32, blank=True, null=True)
    connectinfo_start = models.CharField(max_length=128, blank=True, null=True)
    connectinfo_stop = models.CharField(max_length=128, blank=True, null=True)
    acctinputoctets = models.BigIntegerField(blank=True, null=True)
    acctoutputoctets = models.BigIntegerField(blank=True, null=True)
    calledstationid = models.CharField(max_length=50, default='')
    callingstationid = models.CharField(max_length=50, default='')
    acctterminatecause = models.CharField(max_length=32, default='')
    servicetype = models.CharField(max_length=32, blank=True, null=True)
    framedprotocol = models.CharField(max_length=32, blank=True, null=True)
    framedipaddress = models.CharField(max_length=15, default='')
    framedipv6address = models.CharField(max_length=45, default='')
    framedipv6prefix = models.CharField(max_length=45, default='')
    framedinterfaceid = models.CharField(max_length=44, default='')
    delegatedipv6prefix = models.CharField(max_length=45, default='')
    class_field = models.CharField(db_column='class', max_length=64, blank=True, null=True)

    class Meta:
        db_table = 'radacct'
        managed = False

    def __str__(self):
        return f"{self.username} - {self.nasipaddress} - {self.acctsessiontime}s"


from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

import threading
import subprocess

def _restart_container_background():
    try:
        subprocess.run(
            ["docker", "container", "restart", "radcoringa-radius"],
            check=True,
            capture_output=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Falha ao restartar o container: {e.stderr.decode('utf-8')}")
    except FileNotFoundError:
        print("Comando 'docker' não encontrado no PATH.")

def trigger_nas_reload(ip_address):
    try:
        clean_ip = ip_address.split('/')[0]
        Nasreload.objects.update_or_create(
            nasipaddress=clean_ip[:15],
            defaults={'reloadtime': timezone.now()}
        )
        
        bg_thread = threading.Thread(target=_restart_container_background)
        bg_thread.daemon = True
        bg_thread.start()

    except Exception as e:
        print(f"Erro inesperado em trigger_nas_reload: {e}")

@receiver(post_save, sender=Cliente)
def sync_cliente_nas(sender, instance, **kwargs):
    old_name = getattr(instance, '_old_nome', None)
    if old_name and old_name != instance.nome:
        Nas.objects.filter(shortname=old_name[:32]).delete()
    instance._old_nome = instance.nome

    current_ips = list(instance.Lista_ips.values_list('endereco_ip', flat=True))

    if instance.status == 'ativo':
        for ip_str in current_ips:
            Nas.objects.update_or_create(
                nasname=ip_str,
                defaults={
                    'shortname': instance.nome[:32],
                    'secret': instance.secret,
                    'description': f"Cliente: {instance.nome}"[:200]
                }
            )
            trigger_nas_reload(ip_str)
        
        leftovers = Nas.objects.filter(shortname=instance.nome[:32]).exclude(nasname__in=current_ips)
        leftover_ips = list(leftovers.values_list('nasname', flat=True))
        leftovers.delete()
        for lip in leftover_ips:
            trigger_nas_reload(lip)
    else:
        Nas.objects.filter(nasname__in=current_ips).delete()
        Nas.objects.filter(shortname=instance.nome[:32]).delete()
        for ip_str in current_ips:
            trigger_nas_reload(ip_str)

@receiver(post_delete, sender=Cliente)
def clean_leftover_nas_on_cliente_delete(sender, instance, **kwargs):
    Nas.objects.filter(shortname=instance.nome[:32]).delete()

@receiver(post_save, sender=ClienteIP)
def sync_clienteip_save(sender, instance, **kwargs):
    original_ip = getattr(instance, '_original_endereco_ip', None)
    if original_ip and original_ip != instance.endereco_ip:
        Nas.objects.filter(nasname=original_ip).delete()
        trigger_nas_reload(original_ip)
    instance._original_endereco_ip = instance.endereco_ip

    if instance.cliente.status == 'ativo':
        Nas.objects.update_or_create(
            nasname=instance.endereco_ip,
            defaults={
                'shortname': instance.cliente.nome[:32],
                'secret': instance.cliente.secret,
                'description': f"Cliente: {instance.cliente.nome}"[:200]
            }
        )
        trigger_nas_reload(instance.endereco_ip)
    else:
        Nas.objects.filter(nasname=instance.endereco_ip).delete()
        trigger_nas_reload(instance.endereco_ip)

@receiver(post_delete, sender=ClienteIP)
def sync_clienteip_delete(sender, instance, **kwargs):
    Nas.objects.filter(nasname=instance.endereco_ip).delete()
    trigger_nas_reload(instance.endereco_ip)