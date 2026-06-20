from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from .models import Cliente, ClienteIP

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome', 'data_expiracao', 'observacao', 'habilitar_pool', 'pool_name_input', 'pool_block']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Provedor internet'}),
            'data_expiracao': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M',
                attrs={'class': 'form-control', 'type': 'datetime-local'}
            ),
            'observacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'habilitar_pool': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'pool_name_input': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: pool1'}),
            'pool_block': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 192.168.100.0/24'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        habilitar_pool = cleaned_data.get('habilitar_pool')
        pool_name_input = cleaned_data.get('pool_name_input')
        pool_block = cleaned_data.get('pool_block')

        if habilitar_pool:
            if not pool_name_input:
                self.add_error('pool_name_input', 'Este campo é obrigatório quando a entrega de IP por pool está habilitada.')
            if not pool_block:
                self.add_error('pool_block', 'Este campo é obrigatório quando a entrega de IP por pool está habilitada.')
        return cleaned_data

class BaseIPFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        
        total_ips = 0
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                total_ips += 1
        
        if total_ips > 5:
            raise forms.ValidationError("Um provedor pode registrar no máximo 5 IPs públicos de CCR.")

IPFormSet = inlineformset_factory(
    Cliente,
    ClienteIP,
    formset=BaseIPFormSet,
    fields=['endereco_ip'],
    extra=5,
    can_delete=True, 
    widgets={
        'endereco_ip': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '192.168.12.0/24'})
    }
)
