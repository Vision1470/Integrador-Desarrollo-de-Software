from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login

def menu_jefa(request):
    return render(request, 'usuarioJefa/menu_jefa.html')

def pacientes_jefa(request):
    return render(request, 'usuarioJefa/pacientes_jefa.html')

def historiales_(request):
    return render(request, 'usuarioJefa/historiales.html')  

def historial_empleados(request):
    return render(request, 'usuarioJefa/historial_empleados.html')

def historial_pacientes(request):
    return render(request, 'usuarioJefa/historial_pacientes.html') 

def calendario_(request):
    return render(request, 'usuarioJefa/calendario.html')  