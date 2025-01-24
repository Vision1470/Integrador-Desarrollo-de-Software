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
    
    path('calendario-/', views.calendario_area, name='calendario_area'),
    path('calendario/crear/', views.crear_asignacion, name='crear_asignacion'),
    path('calendario/modificar/', views.modificar_asignacion, name='modificar_asignacion'), 
    path('calendario/eliminar/<int:asignacion_id>/', views.eliminar_asignacion, name='eliminar_asignacion'),

    
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
    path('reactivar_paciente/<int:paciente_id>/', views.reactivar_paciente, name='reactivar_paciente'),

    path('areas-fortalezas/', views.areas_fortalezas, name='areas_fortalezas'),
    path('crear-area/', views.crear_area, name='crear_area'),
    path('crear-fortaleza/', views.crear_fortaleza, name='crear_fortaleza'),
    path('editar-area/<int:area_id>/', views.editar_area, name='editar_area'),
    path('editar-fortaleza/<int:fortaleza_id>/', views.editar_fortaleza, name='editar_fortaleza'),

    path('reactivar-paciente/<int:paciente_id>/', views.reactivar_paciente_, name='reactivar_paciente_'),

    path('sobrecarga/lista/', views.lista_areas_sobrecarga, name='lista_areas_sobrecarga'),
    path('sobrecarga/activar/', views.activar_sobrecarga, name='activar_sobrecarga'),
    path('sobrecarga/desactivar/<int:sobrecarga_id>/', views.desactivar_sobrecarga, name='desactivar_sobrecarga'),
    path('area/prioridad/', views.asignar_nivel_prioridad, name='asignar_nivel_prioridad'),
    path('sobrecarga/lista/', views.lista_areas_sobrecarga, name='lista_areas_sobrecarga'),
]