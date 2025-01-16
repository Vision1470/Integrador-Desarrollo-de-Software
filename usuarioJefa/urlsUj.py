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
    #path('eliminar-usuario/<int:usuario_id>/', views.eliminar_usuario, name='eliminar_usuario'),
    path('almacen_/', views.almacen_, name='almacen_'),
]