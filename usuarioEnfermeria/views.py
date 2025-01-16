from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from usuarioJefa.models import Paciente

@login_required
def pacientes_enfermeria(request):
    enfermero_actual = request.user
    print("Enfermero actual:", enfermero_actual.username, enfermero_actual.tipoUsuario)  # Debug
    
    pacientes_asignados = Paciente.objects.filter(
        enfermero_actual=enfermero_actual,
        esta_activo=True
    ).select_related('area', 'doctor_actual')
    
    print("Número de pacientes:", pacientes_asignados.count())  # Debug
    print("Query SQL:", pacientes_asignados.query)  # Debug
    
    return render(request, 'usuarioEnfermeria/pacientes_enfermeria.html', {
        'pacientes': pacientes_asignados,
        'enfermero': enfermero_actual
    })

def formulario_paciente(request):
    return render(request, 'usuarioEnfermeria/formulario_paciente.html')  # Agregado usuarioEnfermeria/

def cuidados_paciente(request):
    return render(request, 'usuarioEnfermeria/cuidados_paciente.html')  # Agregado usuarioEnfermeria/