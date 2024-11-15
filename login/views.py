from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login

def login_view(request):
    return render(request, 'login.html')

def primer_ingreso(request):
    return render(request, 'primer_ingreso.html')

def pacientes_enfermera(request):
    if request.method == 'POST':
        usuario = request.POST.get('usuario')
        contraseña = request.POST.get('contraseña')
        user = authenticate(username=usuario, password=contraseña)
        if user is not None:
            login(request, user)
            return render(request, 'pacientes_enfermera.html')
    return redirect('login')

def recuperar_usuario(request):
    return render(request, 'recuperar_usuario.html')

def recuperar_contrasenia(request):
    return render(request, 'recuperar_contrasenia.html')

def confirmar_correo(request):
    return render(request, 'confirmar_correo.html')