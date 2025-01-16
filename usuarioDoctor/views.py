from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from usuarioJefa.models import *
from .models import *
from django.contrib import messages

@login_required
def pacientes_doctor(request):
    # Obtener el doctor actualmente logueado
    doctor_actual = request.user
    
    # Obtener solo los pacientes asignados a este doctor y que estén activos
    pacientes_asignados = Paciente.objects.filter(
        doctor_actual=doctor_actual,
        esta_activo=True
    ).select_related('area')

    return render(request, 'usuarioDoctor/pacientes_doctor.html', {
        'pacientes': pacientes_asignados,
        'doctor': doctor_actual
    })

@login_required
def receta_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    
    if request.method == 'POST':
        try:
            # Validar que el doctor tenga permisos sobre este paciente
            if paciente.doctor_actual != request.user:
                messages.error(request, 'No tienes permiso para modificar la receta de este paciente')
                return redirect('doctor:pacientes_doctor')

            # Crear diagnóstico
            diagnostico = Diagnostico.objects.create(
                paciente=paciente,
                doctor=request.user,
                descripcion=request.POST.get('descripcion', ''),
                cuidados_especificos=request.POST.get('cuidados', '')
            )

            # Agregar padecimientos al diagnóstico
            padecimientos = request.POST.getlist('padecimientos')
            niveles_gravedad = request.POST.getlist('niveles_gravedad')
            comentarios_padecimientos = request.POST.getlist('comentarios_padecimientos')

            for i in range(len(padecimientos)):
                PadecimientoDiagnostico.objects.create(
                    diagnostico=diagnostico,
                    padecimiento_id=padecimientos[i],
                    nivel_gravedad=niveles_gravedad[i],
                    comentarios=comentarios_padecimientos[i] if i < len(comentarios_padecimientos) else ''
                )

            # Crear receta
            receta = Receta.objects.create(
                paciente=paciente,
                doctor=request.user,
                diagnostico=diagnostico
            )

            # Agregar detalles de la receta
            medicamentos = request.POST.getlist('medicamentos')
            dosis = request.POST.getlist('dosis')
            horarios = request.POST.getlist('horarios')
            instrucciones = request.POST.getlist('instrucciones')

            for i in range(len(medicamentos)):
                DetalleReceta.objects.create(
                    receta=receta,
                    medicamento_id=medicamentos[i],
                    dosis=dosis[i],
                    horario=horarios[i],
                    instrucciones=instrucciones[i]
                )

            messages.success(request, 'Receta y diagnóstico creados exitosamente')
            return redirect('doctor:pacientes_doctor')

        except Exception as e:
            messages.error(request, f'Error al crear la receta y diagnóstico: {str(e)}')
    
    context = {
        'paciente': paciente,
        'medicamentos': Medicamento.objects.all(),  # Pendiente este modelo
        'padecimientos': Padecimiento.objects.all(),
    }
    return render(request, 'usuarioDoctor/receta_paciente.html', context)

def cuidados_paciente(request):
    return render(request, 'usuarioDoctor/cuidados_pacienteD.html')  
