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