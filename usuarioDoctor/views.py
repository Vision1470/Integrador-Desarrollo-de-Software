from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from usuarioJefa.models import *
from .models import *
from django.contrib import messages
from django.http import JsonResponse

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
            if paciente.doctor_actual != request.user:
                messages.error(request, 'No tienes permiso para crear recetas para este paciente')
                return redirect('doctor:pacientes_doctor')

            # Desactivar receta actual si existe
            receta_actual = Receta.objects.filter(paciente=paciente, activa=True).first()
            if receta_actual:
                receta_actual.activa = False
                receta_actual.save()

            # Crear diagnóstico
            diagnostico = Diagnostico.objects.create(
                paciente=paciente,
                doctor=request.user,
                descripcion=request.POST.get('descripcion_diagnostico', ''),
                cuidados_especificos=''
            )

            # Crear nueva receta
            receta = Receta.objects.create(
                paciente=paciente,
                doctor=request.user,
                diagnostico=diagnostico
            )

            # Procesar padecimientos (modificado)
            padecimientos_ids = request.POST.getlist('padecimientos[]')
            niveles_gravedad = request.POST.getlist('niveles_gravedad[]')
            
            for i in range(len(padecimientos_ids)):
                if padecimientos_ids[i]:
                    RecetaPadecimiento.objects.create(
                        receta=receta,
                        padecimiento_id=int(padecimientos_ids[i]),
                        nivel_gravedad=niveles_gravedad[i]
                    )

            # El resto de la vista se mantiene igual...
            # Procesar cuidados
            cuidados_nombres = request.POST.getlist('cuidados[]')
            for nombre in cuidados_nombres:
                if nombre.strip():
                    cuidado = Cuidado.objects.create(
                        nombre=nombre.strip()
                    )
                    RecetaCuidado.objects.create(
                        receta=receta,
                        cuidado=cuidado
                    )

            # Procesar medicamentos...
            # [Código existente para medicamentos se mantiene igual]

            messages.success(request, 'Receta creada exitosamente')
            return redirect('doctor:pacientes_doctor')

        except Exception as e:
            messages.error(request, f'Error al crear receta: {str(e)}')
            return redirect('doctor:receta_paciente', paciente_id=paciente_id)

    # Para GET request
    receta_actual = Receta.objects.filter(
        paciente=paciente,
        activa=True
    ).select_related('diagnostico').first()

    context = {
        'paciente': paciente,
        'medicamentos': Medicamento.objects.filter(cantidad_disponible__gt=0),
        'niveles_gravedad': Diagnostico.NIVELES_GRAVEDAD,
        'receta_actual': receta_actual,
        'padecimientos_disponibles': Padecimiento.objects.filter(activo=True)  # Añadido
    }

    if receta_actual:
        context.update({
            'padecimientos': RecetaPadecimiento.objects.filter(receta=receta_actual).select_related('padecimiento'),
            'cuidados': RecetaCuidado.objects.filter(receta=receta_actual).select_related('cuidado'),
            'detalles_medicamentos': DetalleReceta.objects.filter(receta=receta_actual).select_related('medicamento'),
            'diagnostico': receta_actual.diagnostico,
        })
    
    return render(request, 'usuarioDoctor/receta_paciente.html', context)

@login_required
def get_medicamento_info(request, medicamento_id):
    try:
        medicamento = Medicamento.objects.get(id=medicamento_id)
        return JsonResponse({
            'id': medicamento.id,
            'nombre': medicamento.nombre,
            'gramaje': medicamento.gramaje,
            'compuestos': list(medicamento.compuestos.values('id', 'nombre')),
            'cantidad_disponible': medicamento.cantidad_disponible
        })
    except Medicamento.DoesNotExist:
        return JsonResponse({'error': 'Medicamento no encontrado'}, status=404)

def cuidados_paciente(request):
    return render(request, 'usuarioDoctor/cuidados_pacienteD.html')  

@login_required
def ver_receta_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    
    # Obtener la receta activa más reciente
    receta = Receta.objects.filter(
        paciente=paciente,
        activa=True
    ).select_related('diagnostico').prefetch_related(
        'padecimientos',
        'cuidados',
        'detalles'
    ).order_by('-fecha_creacion').first()
    
    if not receta:
        messages.warning(request, 'El paciente no tiene una receta activa.')
        return redirect('doctor:pacientes_doctor')
    
    context = {
        'paciente': paciente,
        'receta': receta,
        'padecimientos': RecetaPadecimiento.objects.filter(receta=receta).select_related('padecimiento'),
        'cuidados': RecetaCuidado.objects.filter(receta=receta).select_related('cuidado'),
        'detalles_medicamentos': DetalleReceta.objects.filter(receta=receta).select_related('medicamento'),
        'diagnostico': receta.diagnostico,
    }
    
    return render(request, 'usuarioDoctor/ver_receta_paciente.html', context)