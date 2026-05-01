from django import forms
from django.forms import inlineformset_factory
from .models import Cliente, ClienteIP

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome', 'data_expiracao', 'observacao']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Provedor internet'}),
            'data_expiracao': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M',
                attrs={'class': 'form-control', 'type': 'datetime-local'}
            ),
            'observacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

IPFormSet = inlineformset_factory(
    Cliente,
    ClienteIP,
    fields=['endereco_ip'],
    extra=5,
    can_delete=False, 
    widgets={
        'endereco_ip': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '192.168.12.0/24'})
    }
)
