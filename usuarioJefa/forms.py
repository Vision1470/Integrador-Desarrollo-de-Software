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