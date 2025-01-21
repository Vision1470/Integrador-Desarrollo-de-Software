from django.urls import path
from . import views

app_name = 'jefa'
urlpatterns = [
    path('menu-jefa/', views.menu_jefa, name='menu_jefa'),
    path('pacientes-jefa/', views.pacientes_jefa, name='pacientes_jefa'),
    path('agregar_pacientes', views.agregar_pacientes, name='agregar_pacientes'),
    path('historiales-/', views.historiales_, name='historiales_'),
    path('historial-pacientes/', views.historial_pacientes, name='historial_pacientes'),
    path('historial-empleados/', views.historial_empleados, name='historial_empleados'),
    path('calendario-/', views.calendario_, name='calendario_'),
    path('usuarios-/', views.usuarios_, name='usuarios_'),
    path('crear-usuarios/', views.crear_usuarios, name='crear_usuarios'),
    path('gestionar-usuarios/', views.gestionar_usuarios, name='gestionar_usuarios'),
    path('editar-usuario/<int:usuario_id>/', views.editar_usuario, name='editar_usuario'),
    path('toggle-usuario/<int:usuario_id>/', views.toggle_usuario, name='toggle_usuario'),
    path('almacen_/', views.almacen_, name='almacen_'),
    path('editar-medicamento/<int:medicamento_id>/', views.editar_medicamento, name='editar_medicamento'),
    path('editar-instrumento/<int:instrumento_id>/', views.editar_instrumento, name='editar_instrumento'),
    path('eliminar-medicamento/<int:medicamento_id>/', views.eliminar_medicamento, name='eliminar_medicamento'),
    path('eliminar-instrumento/<int:instrumento_id>/', views.eliminar_instrumento, name='eliminar_instrumento'),
    path('get-medicamento/<int:medicamento_id>/', views.get_medicamento, name='get_medicamento'),
    path('get-instrumento/<int:instrumento_id>/', views.get_instrumento, name='get_instrumento'),
    path('dar_alta_paciente/<int:paciente_id>/', views.dar_alta_paciente, name='dar_alta_paciente'),
    path('historial/<int:paciente_id>/', views.detalle_historial, name='detalle_historial'),
]