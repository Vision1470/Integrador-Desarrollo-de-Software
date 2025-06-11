from django.shortcuts import redirect
from django.contrib.auth import logout
from django.contrib import messages
from django.urls import reverse

class VerificarUsuarioActivoMiddleware:
    """
    Middleware que verifica si el usuario autenticado sigue activo.
    Si no está activo, cierra la sesión automáticamente.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Verificar solo si el usuario está autenticado
        if request.user.is_authenticated:
            # Verificar si el usuario sigue activo
            if hasattr(request.user, 'estaActivo') and not request.user.estaActivo:
                # Cerrar sesión si el usuario fue desactivado
                logout(request)
                messages.warning(request, 'Tu cuenta ha sido desactivada. Contacta al administrador.')
                return redirect('login:login')
        
        response = self.get_response(request)
        return response