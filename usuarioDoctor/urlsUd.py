from django.urls import path
from . import views

app_name = 'doctor'
urlpatterns = [
    path('pacientes-doctor/', views.pacientes_doctor, name='pacientes_doctor'),
    path('cuidados-pacienteD/<int:paciente_id>/', views.cuidados_paciente, name='cuidados_pacienteD'),
    path('receta-paciente/<int:paciente_id>/', views.receta_paciente, name='receta_paciente'),
    path('get-medicamento-info/<int:medicamento_id>/', views.get_medicamento_info, name='get_medicamento_info'),
    path('ver-receta/<int:paciente_id>/', views.ver_receta_paciente, name='ver_receta_paciente'),
]