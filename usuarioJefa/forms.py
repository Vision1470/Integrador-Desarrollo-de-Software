from django import forms
from django.db.models import Q
from .models import Paciente, Hospital
from login.models import Usuarios, AreaEspecialidad

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
        
        # Configurar los campos
        self.fields['area'].queryset = AreaEspecialidad.objects.all()
        self.fields['doctor_actual'].queryset = Usuarios.objects.filter(tipoUsuario='DR')
        self.fields['enfermero_actual'].queryset = Usuarios.objects.filter(tipoUsuario='EN')
        self.fields['hospital_origen'].required = False
        
        # Filtrar doctores y enfermeros
        self.fields['doctor_actual'].queryset = Usuarios.objects.filter(tipoUsuario='DR')
        self.fields['enfermero_actual'].queryset = Usuarios.objects.filter(tipoUsuario='EN')