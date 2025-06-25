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
    path('calendario/limpiar-todo/', views.limpiar_todas_asignaciones, name='limpiar_todas_asignaciones'),  # NUEVA URL
    
    # URLs para asignaciones de emergencia
    path('emergencia/crear/', views.crear_emergencia, name='crear_emergencia'),
    path('emergencia/finalizar/<int:emergencia_id>/', views.finalizar_emergencia, name='finalizar_emergencia'),
    
    # APIs AJAX para el calendario
    path('api/mes-datos/', views.get_datos_mes_ajax, name='get_datos_mes_ajax'),
    path('api/enfermeros-disponibles/', views.obtener_enfermeros_disponibles, name='enfermeros_disponibles'),

    #URLs para sugerencias
    path('sugerencias-anuales/', views.generar_sugerencias_anuales, name='generar_sugerencias_anuales'),
    path('sugerencias-anuales/<int:año>/', views.generar_sugerencias_anuales, name='generar_sugerencias_anuales_año'),
    
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

    # URLs del simulador de eventos
    path('simulador/', views.simulador_inicio, name='simulador_inicio'),
    path('simulador/enfermeros/<int:simulacion_id>/', views.simulador_enfermeros, name='simulador_enfermeros'),
    path('simulador/pacientes/<int:simulacion_id>/', views.simulador_pacientes, name='simulador_pacientes'),
    path('simulador/padecimientos/<int:simulacion_id>/', views.simulador_padecimientos, name='simulador_padecimientos'),
    path('simulador/resultados/<int:simulacion_id>/', views.simulador_resultados, name='simulador_resultados'),
    path('simulador/lista/', views.lista_simulaciones, name='lista_simulaciones'),



    
# AGREGAR las nuevas URLs avanzadas:
# URLs para fortalezas avanzadas (múltiples áreas y padecimientos)
path('crear-fortaleza-avanzada/', views.crear_fortaleza_avanzada, name='crear_fortaleza_avanzada'),
path('editar-fortaleza-avanzada/<int:fortaleza_id>/', views.editar_fortaleza_avanzada, name='editar_fortaleza_avanzada'),
path('eliminar-fortaleza/<int:fortaleza_id>/', views.eliminar_fortaleza, name='eliminar_fortaleza'),

# URLs para padecimientos (nuevas)
path('crear-padecimiento/', views.crear_padecimiento, name='crear_padecimiento'),
path('editar-padecimiento/<int:padecimiento_id>/', views.editar_padecimiento, name='editar_padecimiento'),
path('eliminar-padecimiento/<int:padecimiento_id>/', views.eliminar_padecimiento, name='eliminar_padecimiento'),

# APIs para filtrado dinámico y compatibilidad
path('api/padecimientos-por-areas/', views.get_padecimientos_por_areas, name='padecimientos_por_areas'),
path('api/fortalezas-por-areas/', views.get_fortalezas_por_areas, name='fortalezas_por_areas'),
path('api/compatibilidad-area/', views.get_compatibilidad_area, name='compatibilidad_area'),
path('api/obtener-area/<int:area_id>/', views.obtener_area, name='obtener_area'),

# APIs para cargar datos en modales de edición
path('api/obtener-fortaleza/<int:fortaleza_id>/', views.obtener_fortaleza, name='obtener_fortaleza'),
path('api/obtener-padecimiento/<int:padecimiento_id>/', views.obtener_padecimiento, name='obtener_padecimiento'),

#Usuarios temporales
path('crear-usuario-temporal/', views.crear_personal_temporal_nuevo, name='crear_personal_temporal'),

path('gestionar-personal-temporal/', views.gestionar_personal_temporal, name='gestionar_personal_temporal'),
path('finalizar-temporal/<int:personal_id>/', views.desactivar_personal_temporal, name='finalizar_temporal'),
path('personal-temporal/', views.gestionar_personal_temporal, name='gestionar_personal_temporal'),
path('personal-temporal/crear/', views.crear_personal_temporal_nuevo, name='crear_personal_temporal'),
path('personal-temporal/reactivar/', views.reactivar_personal_historico, name='reactivar_personal_historico'),
path('personal-temporal/desactivar/', views.desactivar_personal_temporal, name='desactivar_personal_temporal'),
path('historial-personal-temporal/<int:personal_id>/', views.historial_personal_temporal_ajax, name='historial_personal_temporal_ajax'),
]