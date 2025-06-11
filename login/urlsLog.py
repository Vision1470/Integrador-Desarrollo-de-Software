from django.urls import path
from . import views

app_name = 'login'
urlpatterns = [
    path('', views.login_view, name='login'),  # Ruta principal del login
    path('logout/', views.logout_view, name='logout'),  # Nueva vista de logout
    path('primer-ingreso/', views.primer_ingreso, name='primer_ingreso'),
    path('recuperar-usuario/', views.recuperar_usuario, name='recuperar_usuario'),
    path('recuperar-contrasenia/', views.recuperar_contrasenia, name='recuperar_contrasenia'),
    path('confirmar-correo/', views.confirmar_correo, name='confirmar_correo'),
]