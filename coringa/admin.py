from django.contrib import admin
from .models import Cliente, ClienteIP

class IPsInline(admin.TabularInline):
    model = ClienteIP
    extra = 1 

class ClienteAdmin(admin.ModelAdmin):
    list_display = (
        'nome', 
        'status', 
        'responsavel_cadastro', 
        'data_cadastro', 
        'secret'
    )

    search_fields = ('nome',)
    
    inlines = [IPsInline]

    def get_readonly_fields(self, request, obj=None):
        if obj is None: 
            return ('status', )
        return ('responsavel_cadastro',)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.responsavel_cadastro = request.user
        super().save_model(request, obj, form, change)

admin.site.register(Cliente, ClienteAdmin)
admin.site.register(ClienteIP)