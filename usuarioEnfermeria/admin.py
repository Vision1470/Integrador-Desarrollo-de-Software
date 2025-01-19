from django.contrib import admin
from .models import SeguimientoCuidados, RegistroCuidado, RegistroMedicamento

class RegistroCuidadoInline(admin.TabularInline):
    model = RegistroCuidado
    extra = 0

class RegistroMedicamentoInline(admin.TabularInline):
    model = RegistroMedicamento
    extra = 0

@admin.register(SeguimientoCuidados)
class SeguimientoCuidadosAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'registrado_por', 'fecha_registro')
    list_filter = ('registrado_por', 'fecha_registro')
    search_fields = ('paciente__nombres', 'paciente__apellidos')
    inlines = [RegistroCuidadoInline, RegistroMedicamentoInline]

@admin.register(RegistroCuidado)
class RegistroCuidadoAdmin(admin.ModelAdmin):
    list_display = ('seguimiento', 'cuidado', 'completado', 'fecha_completado')
    list_filter = ('completado', 'fecha_completado')

@admin.register(RegistroMedicamento)
class RegistroMedicamentoAdmin(admin.ModelAdmin):
    list_display = ('seguimiento', 'medicamento', 'administrado', 'fecha_administracion')
    list_filter = ('administrado', 'fecha_administracion')