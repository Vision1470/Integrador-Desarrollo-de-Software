from django.shortcuts import render, redirect
from django.contrib.auth import *
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import *

def login_view(request):
    print(f"DEBUG: Usuario autenticado: {request.user.is_authenticated}")
    if request.user.is_authenticated:
        print(f"DEBUG: Usuario: {request.user.username}")
        print(f"DEBUG: Activo: {getattr(request.user, 'estaActivo', 'N/A')}")
        print(f"DEBUG: Primer ingreso: {getattr(request.user, 'primerIngreso', 'N/A')}")
    
    # Si el usuario está autenticado pero accede directamente a /login/
    # NO redirigir automáticamente, mostrar el login con opción de logout
    if request.user.is_authenticated:
        # Verificar si el usuario está inactivo
        if hasattr(request.user, 'estaActivo') and not request.user.estaActivo:
            print("DEBUG: Usuario inactivo, cerrando sesión")
            logout(request)
            messages.warning(request, 'Tu cuenta ha sido desactivada. Contacta al administrador.')
            return render(request, 'login/login.html')
        
        # Si llega aquí, mostrar el login con la información de que ya está autenticado
        # El template mostrará el botón de logout que agregamos antes
        print("DEBUG: Usuario autenticado accediendo a /login/, mostrando página con opción de logout")
    
    if request.method == 'POST':
        usuario = request.POST.get('usuario', '').strip()
        contraseña = request.POST.get('contraseña', '').strip()

        # Validar que los campos no estén vacíos
        if not usuario or not contraseña:
            messages.error(request, 'Por favor ingresa tu usuario y contraseña')
            return render(request, 'login/login.html')

        try:
            # Primero verificamos si el usuario existe
            try:
                user_obj = Usuarios.objects.get(username=usuario)
                
                # Verificar si el usuario está activo
                if not user_obj.estaActivo:
                    messages.error(request, 'Tu cuenta está desactivada. Contacta al administrador.')
                    return render(request, 'login/login.html')
                    
            except Usuarios.DoesNotExist:
                messages.error(request, 'El usuario ingresado no existe')
                return render(request, 'login/login.html')

            # Autenticamos al usuario
            user = authenticate(request, username=usuario, password=contraseña)
            
            if user is not None:
                # Si ya hay un usuario autenticado diferente, cerrar esa sesión primero
                if request.user.is_authenticated and request.user.username != user.username:
                    print(f"DEBUG: Cerrando sesión de {request.user.username} para iniciar con {user.username}")
                    logout(request)
                
                login(request, user)
                print(f"DEBUG: Login exitoso para {user.username}")
                
                # Verificar primer ingreso
                if user.primerIngreso:
                    return redirect('login:primer_ingreso')

                # Redirección según tipo de usuario
                if user.tipoUsuario == 'JP':
                    return redirect('jefa:menu_jefa')
                elif user.tipoUsuario == 'EN':
                    return redirect('enfermeria:pacientes_enfermeria')
                elif user.tipoUsuario == 'DR':
                    return redirect('doctor:pacientes_doctor')
                else:
                    messages.warning(request, 'Tipo de usuario no reconocido')
                    logout(request)
                    return redirect('login:login')
            else:
                # Si el usuario existe pero la autenticación falla, es por la contraseña
                messages.error(request, 'La contraseña ingresada es incorrecta')
                return render(request, 'login/login.html')

        except Exception as e:
            print(f"Error en login: {str(e)}")  # Para debugging
            messages.error(request, 'Ocurrió un error al intentar iniciar sesión. Intenta nuevamente.')
            return render(request, 'login/login.html')

    return render(request, 'login/login.html')

def logout_view(request):
    """
    Vista para cerrar sesión del usuario.
    Cierra la sesión activa y redirige al login con un mensaje de confirmación.
    """
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.success(request, f'Sesión cerrada correctamente para {username}')
    else:
        messages.info(request, 'No había una sesión activa')
    
    return redirect('login:login')

def primer_ingreso(request):
    """
    Vista simplificada para el primer ingreso.
    No requiere autenticación previa, el usuario se autentica con credenciales temporales.
    """
    
    if request.method == 'POST':
        # Obtener credenciales temporales
        nombre_temporal = request.POST.get('nombre_temporal', '').strip()
        contraseña_temporal = request.POST.get('contraseña_temporal', '').strip()
        
        # Validar que no estén vacíos
        if not nombre_temporal or not contraseña_temporal:
            messages.error(request, 'Por favor ingresa las credenciales temporales')
            return render(request, 'login/primer_ingreso.html')
        
        # Verificar credenciales temporales
        try:
            # Buscar usuario por username temporal
            user = Usuarios.objects.get(username=nombre_temporal, estaActivo=True)
            
            # Verificar que sea primer ingreso
            if not user.primerIngreso:
                messages.error(request, 'Esta cuenta ya ha sido configurada')
                return redirect('login:login')
            
            # Verificar contraseña temporal
            if not user.check_password(contraseña_temporal):
                messages.error(request, 'Las credenciales temporales son incorrectas')
                return render(request, 'login/primer_ingreso.html')
                
        except Usuarios.DoesNotExist:
            messages.error(request, 'Las credenciales temporales no existen en el sistema o el usuario está inactivo')
            return render(request, 'login/primer_ingreso.html')
        except Exception as e:
            print(f"Error al buscar usuario temporal: {str(e)}")
            messages.error(request, 'Error al verificar las credenciales temporales')
            return render(request, 'login/primer_ingreso.html')
        
        # Obtener datos del nuevo usuario
        username = request.POST.get('usuario', '').strip()
        password = request.POST.get('contraseña', '').strip()
        password_confirm = request.POST.get('contraseña_confirmar', '').strip()
        email = request.POST.get('correo', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        
        # Validaciones
        if not username or not password or not password_confirm:
            messages.error(request, 'Todos los campos son obligatorios')
            return render(request, 'login/primer_ingreso.html')
        
        # Verificar que las contraseñas coincidan
        if password != password_confirm:
            messages.error(request, 'Las contraseñas no coinciden')
            return render(request, 'login/primer_ingreso.html')
            
        # Verificar longitud mínima de contraseña
        if len(password) < 6:
            messages.error(request, 'La contraseña debe tener al menos 6 caracteres')
            return render(request, 'login/primer_ingreso.html')
            
        # Verificar que el nuevo username no exista ya (excepto el actual)
        if Usuarios.objects.filter(username=username).exclude(id=user.id).exists():
            messages.error(request, 'Este nombre de usuario ya está en uso')
            return render(request, 'login/primer_ingreso.html')
        
        try:
            # Actualizar datos del usuario
            user.username = username
            user.set_password(password)
            if email:
                user.email = email
            if telefono:
                user.telefono = telefono
            user.primerIngreso = False
            user.save()
            
            # Log out si estaba autenticado (por si acaso)
            if request.user.is_authenticated:
                logout(request)
            
            messages.success(request, 'Datos actualizados correctamente. Por favor inicia sesión con tus nuevas credenciales')
            return redirect('login:login')
            
        except Exception as e:
            print(f"Error al actualizar usuario: {str(e)}")  # Para debugging
            messages.error(request, f'Error al actualizar los datos: {str(e)}')
            return render(request, 'login/primer_ingreso.html')
    
    # Para GET request, simplemente mostrar el formulario
    return render(request, 'login/primer_ingreso.html')

def pacientes_enfermera(request):
    if request.method == 'POST':
        usuario = request.POST.get('usuario')
        contraseña = request.POST.get('contraseña')
        user = authenticate(username=usuario, password=contraseña)
        if user is not None:
            login(request, user)
            return redirect('enfermeria:pacientes-enfermeria')
    return redirect('login:login')

def recuperar_usuario(request):
    return render(request, 'login/recuperar_usuario.html')

def recuperar_contrasenia(request):
    return render(request, 'login/recuperar_contrasenia.html')

def confirmar_correo(request):
    return render(request, 'login/confirmar_correo.html')