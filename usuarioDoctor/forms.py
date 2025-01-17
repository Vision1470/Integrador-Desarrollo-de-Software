from django import forms
from .models import RecetaPadecimiento, Padecimiento

class RecetaPadecimientoForm(forms.ModelForm):
    class Meta:
        model = RecetaPadecimiento
        fields = ['padecimiento', 'nivel_gravedad']
        widgets = {
            'padecimiento': forms.Select(attrs={'class': 'form-control'}),
            'nivel_gravedad': forms.Select(attrs={'class': 'form-control'})
        }