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
        IPv4Network(valor, strict=False)
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

    status = models.CharField(
        max_length=10,
        choices=StatusOpcoes.choices,
        default=StatusOpcoes.ATIVO
    )

    class Meta:
        verbose_name = "Provedor de internet"
        verbose_name_plural = "Provedores de internet"

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


class Nasreload(models.Model):
    nasipaddress = models.CharField(max_length=15, primary_key=True)
    reloadtime = models.DateTimeField()

    class Meta:
        db_table = 'nasreload'
        managed = False

    def __str__(self):
        return f"{self.nasipaddress} - {self.reloadtime}"


# Signals for Radius Sync
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

def trigger_nas_reload(ip_address):
    try:
        # Check if the IP contains a mask (CIDR), if so we extract the pure IP or keep it.
        # nasreload.nasipaddress is varchar(15), so it only fits IPv4 without mask.
        clean_ip = ip_address.split('/')[0]
        Nasreload.objects.update_or_create(
            nasipaddress=clean_ip[:15],
            defaults={'reloadtime': timezone.now()}
        )
    except Exception:
        # Fail-safe in case of any issues with the unmanaged tables during migrations
        pass

@receiver(post_save, sender=Cliente)
def sync_cliente_nas(sender, instance, **kwargs):
    if instance.status == 'ativo':
        for ip in instance.Lista_ips.all():
            Nas.objects.update_or_create(
                nasname=ip.endereco_ip,
                defaults={
                    'shortname': instance.nome[:32],
                    'secret': instance.secret,
                    'description': f"Cliente: {instance.nome}"[:200]
                }
            )
            trigger_nas_reload(ip.endereco_ip)
    else:
        # If client becomes inactive/expired, delete all associated IPs
        ips = list(instance.Lista_ips.values_list('endereco_ip', flat=True))
        Nas.objects.filter(nasname__in=ips).delete()
        for ip_str in ips:
            trigger_nas_reload(ip_str)

@receiver(post_delete, sender=Cliente)
def clean_leftover_nas_on_cliente_delete(sender, instance, **kwargs):
    # Bulk cleanup for the deleted client's shortname
    Nas.objects.filter(shortname=instance.nome[:32]).delete()

@receiver(post_save, sender=ClienteIP)
def sync_clienteip_save(sender, instance, **kwargs):
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