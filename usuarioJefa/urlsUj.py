from django.urls import path
from . import views

app_name = 'jefa'
urlpatterns = [
    path('menu-jefa/', views.menu_jefa, name='menu_jefa'),
    path('pacientes-jefa/', views.pacientes_jefa, name='pacientes_jefa'),
    path('historiales-/', views.historiales_, name='historiales_'),
    path('historial-pacientes/', views.historial_pacientes, name='historial_pacientes'),
    path('historial-empleados/', views.historial_empleados, name='historial_empleados'),
    path('calendario-/', views.calendario_, name='calendario_'),
]