from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import *

def login_view(request):
    if request.method == 'POST':
        usuario = request.POST.get('usuario', '').strip()
        contraseña = request.POST.get('contraseña', '')

        try:
            # Primero verificamos si el usuario existe
            try:
                user_obj = Usuarios.objects.get(username=usuario)
                user_exists = True
            except Usuarios.DoesNotExist:
                user_exists = False
            
            if not user_exists:
                messages.error(request, 'El usuario ingresado no existe')
                return render(request, 'login/login.html')

            # Autenticamos al usuario
            user = authenticate(request, username=usuario, password=contraseña)
            
            if user is not None:
                if user.primerIngreso:
                    login(request, user)
                    return redirect('login:primer_ingreso')

                login(request, user)
                # Redirección según tipo de usuario
                if user.tipoUsuario == 'JP':
                    return redirect('jefa:menu_jefa')
                elif user.tipoUsuario == 'EN':
                    return redirect('enfermeria:pacientes_enfermeria')
                elif user.tipoUsuario == 'DR':
                    return redirect('doctor:pacientes_doctor')
                elif user.tipoUsuario == 'CO':
                    # Podemos omitir esta parte por ahora
                    pass
            else:
                # Si el usuario existe pero la autenticación falla, es por la contraseña
                messages.error(request, 'La contraseña ingresada es incorrecta')
                return render(request, 'login/login.html')

        except Exception as e:
            print(f"Error en login: {str(e)}")  # Para debugging
            messages.error(request, f'Ocurrió un error al intentar iniciar sesión: {str(e)}')
            return render(request, 'login/login.html')

    return render(request, 'login/login.html')

def primer_ingreso(request):
    if request.method == 'POST':
        # Obtener credenciales temporales
        nombre_temporal = request.POST.get('nombre_temporal')
        contraseña_temporal = request.POST.get('contraseña_temporal')
        
        # Verificar credenciales temporales
        user = authenticate(username=nombre_temporal, password=contraseña_temporal)
        
        if user is None or not user.primerIngreso:
            messages.error(request, 'Credenciales temporales inválidas o cuenta ya configurada')
            return render(request, 'login/primer_ingreso.html')
        
        # Obtener datos del nuevo usuario
        username = request.POST.get('usuario')
        password = request.POST.get('contraseña')
        password_confirm = request.POST.get('contraseña_confirmar')
        email = request.POST.get('correo')
        telefono = request.POST.get('telefono')
        
        # Verificar que las contraseñas coincidan
        if password != password_confirm:
            messages.error(request, 'Las contraseñas no coinciden')
            return render(request, 'login/primer_ingreso.html')
            
        # Verificar que el username no exista ya
        if Usuarios.objects.filter(username=username).exists() and username != nombre_temporal:
            messages.error(request, 'Este nombre de usuario ya está en uso')
            return render(request, 'login/primer_ingreso.html')
            
        # Actualizar datos del usuario
        user.username = username
        user.set_password(password)
        user.email = email
        user.telefono = telefono
        user.primerIngreso = False
        user.save()
        
        messages.success(request, 'Datos actualizados correctamente. Por favor inicie sesión con sus nuevas credenciales')
        return redirect('login:login')
        
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