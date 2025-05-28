from django.urls import path
from . import views

app_name = 'jefa'
urlpatterns = [
     # URLs existentes del menú principal
    path('menu-jefa/', views.menu_jefa, name='menu_jefa'),
    path('pacientes-jefa/', views.pacientes_jefa, name='pacientes_jefa'),
    path('agregar_pacientes', views.agregar_pacientes, name='agregar_pacientes'),
    path('historiales-/', views.historiales_, name='historiales_'),
    path('historial-pacientes/', views.historial_pacientes, name='historial_pacientes'),
    path('historial-empleados/', views.historial_empleados, name='historial_empleados'),
    
    # URLs del calendario híbrido
    path('calendario-/', views.calendario_area, name='calendario_area'),
    path('calendario/crear/', views.crear_asignacion, name='crear_asignacion'),
    path('calendario/modificar/', views.modificar_asignacion, name='modificar_asignacion'), 
    path('calendario/eliminar/<int:asignacion_id>/', views.eliminar_asignacion, name='eliminar_asignacion'),
    
    # URLs para asignaciones de emergencia
    path('emergencia/crear/', views.crear_emergencia, name='crear_emergencia'),
    path('emergencia/finalizar/<int:emergencia_id>/', views.finalizar_emergencia, name='finalizar_emergencia'),
    
    # APIs AJAX para el calendario
    path('api/mes-datos/', views.get_datos_mes_ajax, name='get_datos_mes_ajax'),
    path('api/enfermeros-disponibles/', views.obtener_enfermeros_disponibles, name='enfermeros_disponibles'),
    
    # URLs existentes de usuarios
    path('usuarios-/', views.usuarios_, name='usuarios_'),
    path('crear-usuarios/', views.crear_usuarios, name='crear_usuarios'),
    path('gestionar-usuarios/', views.gestionar_usuarios, name='gestionar_usuarios'),
    path('editar-usuario/<int:usuario_id>/', views.editar_usuario, name='editar_usuario'),
    path('toggle-usuario/<int:usuario_id>/', views.toggle_usuario, name='toggle_usuario'),
    
    # URLs existentes de almacén
    path('almacen_/', views.almacen_, name='almacen_'),
    path('editar-medicamento/<int:medicamento_id>/', views.editar_medicamento, name='editar_medicamento'),
    path('editar-instrumento/<int:instrumento_id>/', views.editar_instrumento, name='editar_instrumento'),
    path('eliminar-medicamento/<int:medicamento_id>/', views.eliminar_medicamento, name='eliminar_medicamento'),
    path('eliminar-instrumento/<int:instrumento_id>/', views.eliminar_instrumento, name='eliminar_instrumento'),
    path('get-medicamento/<int:medicamento_id>/', views.get_medicamento, name='get_medicamento'),
    path('get-instrumento/<int:instrumento_id>/', views.get_instrumento, name='get_instrumento'),
    
    # URLs existentes de pacientes
    path('dar_alta_paciente/<int:paciente_id>/', views.dar_alta_paciente, name='dar_alta_paciente'),
    path('historial/<int:paciente_id>/', views.detalle_historial, name='detalle_historial'),
    path('reactivar_paciente/<int:paciente_id>/', views.reactivar_paciente, name='reactivar_paciente'),
    path('reactivar-paciente/<int:paciente_id>/', views.reactivar_paciente_, name='reactivar_paciente_'),

    # URLs existentes de áreas y fortalezas
    path('areas-fortalezas/', views.areas_fortalezas, name='areas_fortalezas'),
    path('crear-area/', views.crear_area, name='crear_area'),
    path('crear-fortaleza/', views.crear_fortaleza, name='crear_fortaleza'),
    path('editar-area/<int:area_id>/', views.editar_area, name='editar_area'),
    path('editar-fortaleza/<int:fortaleza_id>/', views.editar_fortaleza, name='editar_fortaleza'),

    # URLs existentes de sobrecarga y distribución
    path('area/prioridad/', views.asignar_nivel_prioridad, name='asignar_nivel_prioridad'),
    path('sobrecarga/lista/', views.lista_areas_sobrecarga, name='lista_areas_sobrecarga'),

    # URLs existentes de distribución de pacientes
    path('distribucion/<int:area_id>/', views.distribuir_pacientes, name='distribuir_pacientes'),
    path('distribucion/ver/<int:area_id>/', views.ver_distribucion, name='ver_distribucion'),
    path('distribucion/guardar/<int:area_id>/', views.guardar_distribucion, name='guardar_distribucion'),
    path('distribucion/ajustar/<int:area_id>/', views.ajustar_distribucion, name='ajustar_distribucion'),
    path('distribucion/cancelar/<int:area_id>/', views.cancelar_distribucion, name='cancelar_distribucion'),
    path('distribucion/manual/<int:area_id>/', views.distribucion_manual, name='distribucion_manual'),
    path('distribucion/ajustar_manual/<int:area_id>/', views.ajustar_distribucion_manual, name='ajustar_distribucion_manual'),

]