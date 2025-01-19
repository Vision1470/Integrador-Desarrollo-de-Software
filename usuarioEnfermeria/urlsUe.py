# urls.py
from django.urls import path
from . import views

app_name = 'enfermeria'
urlpatterns = [
    path('pacientes-enfermera/', views.pacientes_enfermeria, name='pacientes_enfermeria'),
    path('formulario-paciente/', views.formulario_paciente, name='formulario_paciente'),
    path('cuidados-paciente/<int:paciente_id>/', views.cuidados_paciente, name='cuidados_paciente'),
]