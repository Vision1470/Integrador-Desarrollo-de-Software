from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt  # Añade este decorador
def pacientes_doctor(request):
    return render(request, 'usuarioDoctor/pacientes_doctor.html')

def receta_paciente(request):
    return render(request, 'usuarioDoctor/receta_paciente.html')

def cuidados_paciente(request):
    return render(request, 'usuarioDoctor/cuidados_pacienteD.html')  
