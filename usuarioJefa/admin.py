from django.contrib import admin
from .models import Hospital, Paciente, HistorialMedico, RecetaMedica, HistorialDoctores, HistorialEnfermeros

@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'direccion')
    search_fields = ['nombre']

@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ('nombres', 'apellidos', 'num_seguridad_social', 'area', 
                   'doctor_actual', 'enfermero_actual', 'estado', 'esta_activo')
    list_filter = ('estado', 'esta_activo', 'area', 'sexo')
    search_fields = ['nombres', 'apellidos', 'num_seguridad_social']
    date_hierarchy = 'fecha_ingreso'

@admin.register(HistorialMedico)
class HistorialMedicoAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'doctor', 'fecha')
    list_filter = ('doctor',)
    search_fields = ['paciente__nombres', 'paciente__apellidos']
    date_hierarchy = 'fecha'

@admin.register(RecetaMedica)
class RecetaMedicaAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'doctor', 'fecha', 'activa')
    list_filter = ('doctor', 'activa')
    search_fields = ['paciente__nombres', 'paciente__apellidos']
    date_hierarchy = 'fecha'

@admin.register(HistorialDoctores)
class HistorialDoctoresAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'doctor', 'fecha_asignacion', 'fecha_fin')
    list_filter = ('doctor',)
    search_fields = ['paciente__nombres', 'paciente__apellidos']
    date_hierarchy = 'fecha_asignacion'

@admin.register(HistorialEnfermeros)
class HistorialEnfermerosAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'enfermero', 'fecha_asignacion', 'fecha_fin')
    list_filter = ('enfermero',)
    search_fields = ['paciente__nombres', 'paciente__apellidos']
    date_hierarchy = 'fecha_asignacion'