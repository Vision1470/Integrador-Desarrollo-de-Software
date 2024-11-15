from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login

def pacientes_enfermeria(request):
    return render(request, 'pacientes_enfermeria.html')

def formulario_paciente(request):
    return render(request, 'formulario_paciente.html')

def cuidados_paciente(request):
    return render(request, 'cuidados_paciente.html')
