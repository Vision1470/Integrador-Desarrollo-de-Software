from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login

def pacientes_enfermeria(request):
    #if request.method == 'POST':
        # Aquí va la lógica de procesamiento del formulario
      #  return render(request, 'usuarioEnfermeria/formulario_paciente.html')
    return render(request, 'usuarioEnfermeria/pacientes_enfermeria.html')

def formulario_paciente(request):
    return render(request, 'usuarioEnfermeria/formulario_paciente.html')  # Agregado usuarioEnfermeria/

def cuidados_paciente(request):
    return render(request, 'usuarioEnfermeria/cuidados_paciente.html')  # Agregado usuarioEnfermeria/