# urls.py
from django.urls import path
from . import views


app_name = 'login'
urlpatterns = [
    path('', views.login_view, name='login'),
    path('primer-ingreso/', views.primer_ingreso, name='primer_ingreso'),
    path('pacientes-enfermera/', views.pacientes_enfermera, name='pacientes_enfermera'),
    path('recuperar-usuario/', views.recuperar_usuario, name='recuperar_usuario'),
    path('recuperar-contrasenia/', views.recuperar_contrasenia, name='recuperar_contrasenia'),
    path('confirmar-correo/', views.confirmar_correo, name='confirmar_correo'),
]