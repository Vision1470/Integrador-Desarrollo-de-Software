from django import forms
from django.db.models import Q
from .models import *
from login.models import Usuarios, AreaEspecialidad
import calendar
from django.db import models

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = [
            'nombres', 'apellidos', 'fecha_nacimiento', 
            'sexo', 'num_seguridad_social', 'area',
            'doctor_actual', 'enfermero_actual', 'hospital_origen'
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(
                attrs={'type': 'date'}
            ),
            'nombres': forms.TextInput(
                attrs={'placeholder': 'Ingrese los nombres'}
            ),
            'apellidos': forms.TextInput(
                attrs={'placeholder': 'Ingrese los apellidos'}
            ),
            'num_seguridad_social': forms.TextInput(
                attrs={'placeholder': 'Ingrese el número de seguridad social'}
            ),
            'hospital_origen': forms.TextInput(attrs={'class': 'form-control'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['area'].queryset = AreaEspecialidad.objects.all()
        self.fields['doctor_actual'].queryset = Usuarios.objects.filter(tipoUsuario='DR')
        self.fields['enfermero_actual'].queryset = Usuarios.objects.filter(tipoUsuario='EN')
        self.fields['hospital_origen'].required = False

    def clean_num_seguridad_social(self):
        num_seguridad_social = self.cleaned_data.get('num_seguridad_social')
        paciente = Paciente.objects.filter(num_seguridad_social=num_seguridad_social).first()
        
        if paciente:
            if paciente.esta_activo:
                raise forms.ValidationError('Ya existe un paciente activo con este número de seguridad social.')
            else:
                # Guardamos el paciente inactivo para usarlo en la vista
                self.paciente_inactivo = paciente
                raise forms.ValidationError('INACTIVO')  # Usamos esto como señal
        return num_seguridad_social

class ActivarSobrecargaForm(forms.ModelForm):
    class Meta:
        model = AreaSobrecarga
        fields = ['area']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Excluir áreas que ya están en sobrecarga activa
        areas_sobrecargadas = AreaSobrecarga.objects.filter(activo=True).values_list('area', flat=True)
        self.fields['area'].queryset = AreaEspecialidad.objects.exclude(id__in=areas_sobrecargadas)
        self.fields['area'].label = "Área a marcar en sobrecarga"

class AsignarGravedadPacienteForm(forms.ModelForm):
    class Meta:
        model = GravedadPaciente
        fields = ['paciente', 'nivel_gravedad']
        
    def __init__(self, *args, **kwargs):
        area = kwargs.pop('area', None)
        super().__init__(*args, **kwargs)
        if area:
            # Filtrar pacientes por área específica
            self.fields['paciente'].queryset = Paciente.objects.filter(area=area)

class NivelPrioridadAreaForm(forms.ModelForm):
    class Meta:
        model = NivelPrioridadArea
        fields = ['area', 'nivel_prioridad']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Excluir áreas que ya tienen nivel de prioridad asignado
        areas_con_prioridad = NivelPrioridadArea.objects.values_list('area', flat=True)
        self.fields['area'].queryset = AreaEspecialidad.objects.exclude(id__in=areas_con_prioridad)
