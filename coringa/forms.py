from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
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
