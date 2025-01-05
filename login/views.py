from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Usuarios 

def login_view(request):
    if request.method == 'POST':
        usuario = request.POST.get('usuario')
        contraseña = request.POST.get('contraseña')
        user = authenticate(username=usuario, password=contraseña)
        
        if user is not None:
            # Verificar si es primer ingreso
            if user.primerIngreso:
                login(request, user)
                return redirect('login:primer_ingreso')
                
            login(request, user)
            # Redirección según tipo de usuario
            if user.tipoUsuario == 'JP':
                return redirect('jefa_piso:dashboard')
            elif user.tipoUsuario == 'EN':
                return redirect('enfermeria:pacientes_enfermeria')
            elif user.tipoUsuario == 'DR':
                return redirect('doctor:dashboard')
            elif user.tipoUsuario == 'CO':
                return redirect('cocina:dashboard')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
    
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