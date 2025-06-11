from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.contrib.auth import logout
from django.contrib import messages

def home_view(request):
    """Función para manejar la página principal y forzar logout si es necesario"""
    # Si hay un usuario autenticado, cerrar su sesión
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        print(f"DEBUG: Sesión cerrada automáticamente para {username} desde página principal")
    
    # Siempre redirigir al login
    return redirect('login:login')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),  # Usar la nueva función
    path('login/', include('login.urlsLog')),
    path('jefa/', include('usuarioJefa.urlsUj')),
    path('doctor/', include('usuarioDoctor.urlsUd')),
    path('enfermeria/', include('usuarioEnfermeria.urlsUe')),
]