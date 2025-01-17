from django.contrib import admin
from .models import *

class RecetaPadecimientoInline(admin.TabularInline):
    model = RecetaPadecimiento
    extra = 0

class RecetaCuidadoInline(admin.TabularInline):
    model = RecetaCuidado
    extra = 0

class DetalleRecetaInline(admin.TabularInline):
    model = DetalleReceta
    extra = 0

@admin.register(Receta)
class RecetaAdmin(admin.ModelAdmin):
    list_display = ('id', 'paciente', 'doctor', 'fecha_creacion', 'activa')
    list_filter = ('activa', 'aprobado_por_jefa')
    search_fields = ('paciente__nombres', 'paciente__apellidos', 'doctor__username')
    inlines = [RecetaPadecimientoInline, RecetaCuidadoInline, DetalleRecetaInline]
    date_hierarchy = 'fecha_creacion'

@admin.register(Padecimiento)
class PadecimientoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    search_fields = ('nombre',)

@admin.register(Cuidado)
class CuidadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    search_fields = ('nombre',)

@admin.register(Diagnostico)
class DiagnosticoAdmin(admin.ModelAdmin):
    list_display = ('id', 'paciente', 'doctor', 'fecha_creacion', 'activo')
    list_filter = ('activo', 'aprobado_por_jefa')
    search_fields = ('paciente__nombres', 'paciente__apellidos', 'doctor__username')
    date_hierarchy = 'fecha_creacion'

@admin.register(HistorialDiagnostico)
class HistorialDiagnosticoAdmin(admin.ModelAdmin):
    list_display = ('diagnostico', 'doctor_modificador', 'fecha_modificacion')
    list_filter = ('fecha_modificacion',)
    search_fields = ('diagnostico__paciente__nombres', 'doctor_modificador__username')

@admin.register(HistorialReceta)
class HistorialRecetaAdmin(admin.ModelAdmin):
    list_display = ('receta', 'doctor_modificador', 'fecha_modificacion', 'medicamento_no_efectivo')
    list_filter = ('fecha_modificacion', 'medicamento_no_efectivo')
    search_fields = ('receta__paciente__nombres', 'doctor_modificador__username')

@admin.register(RecetaPadecimiento)
class RecetaPadecimientoAdmin(admin.ModelAdmin):
    list_display = ('receta', 'padecimiento', 'nivel_gravedad')
    list_filter = ('nivel_gravedad',)
    search_fields = ('receta__paciente__nombres', 'padecimiento__nombre')

@admin.register(RecetaCuidado)
class RecetaCuidadoAdmin(admin.ModelAdmin):
    list_display = ('receta', 'cuidado', 'completado', 'fecha_completado', 'completado_por')
    list_filter = ('completado', 'fecha_completado')
    search_fields = ('receta__paciente__nombres', 'cuidado__nombre')

@admin.register(DetalleReceta)
class DetalleRecetaAdmin(admin.ModelAdmin):
    list_display = ('receta', 'medicamento', 'cantidad_por_toma', 'frecuencia_horas', 'dias_tratamiento', 'hay_existencia')
    list_filter = ('hay_existencia', 'unidad_medida')
    search_fields = ('receta__paciente__nombres', 'medicamento__nombre')