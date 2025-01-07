from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Usuarios 

def login_view(request):
    if request.method == 'POST':
        usuario = request.POST.get('usuario', '').strip()
        contraseña = request.POST.get('contraseña', '')

        # Validaciones previas...
        
        try:
            user_exists = Usuarios.objects.filter(username=usuario).exists()
            if not user_exists:
                messages.error(request, 'El usuario ingresado no existe')
                return render(request, 'login/login.html')
            
            user = authenticate(username=usuario, password=contraseña)
            if user is not None:
                if user.primerIngreso:
                    login(request, user)
                    return redirect('login:primer_ingreso')
                    
                login(request, user)
                # Redirección según tipo de usuario
                if user.tipoUsuario == 'JP':
                    return redirect('jefa:menu_jefa')  # Cambiado
                elif user.tipoUsuario == 'EN':
                    return redirect('enfermeria:pacientes_enfermeria')
                elif user.tipoUsuario == 'DR':
                    return redirect('doctor:pacientes_doctor')  # Cambiado
                elif user.tipoUsuario == 'CO':
                    # Podemos omitir esta parte por ahora
                    pass
            else:
                messages.error(request, 'La contraseña ingresada es incorrecta')
                return render(request, 'login/login.html')
                
        except Exception as e:
            messages.error(request, 'Ocurrió un error al intentar iniciar sesión')
            return render(request, 'login/login.html')
    
    return render(request, 'login/login.html')

def primer_ingreso(request):
    if request.method == 'POST':
        user = request.user
        username = request.POST.get('usuario')
        password = request.POST.get('contraseña')
        email = request.POST.get('correo')
        telefono = request.POST.get('telefono')
        
        # Verificar que el username no exista ya
        if Usuarios.objects.filter(username=username).exists():
            messages.error(request, 'Este nombre de usuario ya está en uso')
            return render(request, 'login/primer_ingreso.html')
            
        # Actualizar datos del usuario
        user.username = username
        user.set_password(password)
        user.email = email
        user.telefono = telefono
        user.primerIngreso = False
        user.save()
        
        messages.success(request, 'Datos actualizados correctamente')
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