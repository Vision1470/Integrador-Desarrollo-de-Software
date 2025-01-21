from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from usuarioJefa.models import Paciente
from django.contrib import messages
from django.utils import timezone
from .models import *
from usuarioDoctor.models import *

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

@login_required
def cuidados_paciente(request, paciente_id):
    if request.user.tipoUsuario not in ['EN', 'JP']:
        messages.error(request, 'No tienes permiso para acceder a esta sección')
        return redirect('login')
    
    paciente = get_object_or_404(Paciente, id=paciente_id)
    receta_actual = Receta.objects.filter(
        paciente=paciente,
        activa=True
    ).select_related('diagnostico').first()

    if request.method == 'POST':
        print("POST Data:", request.POST)
        try:
            # Crear el registro de seguimiento con número de ingreso
            seguimiento = SeguimientoCuidados.objects.create(
                paciente=paciente,
                registrado_por=request.user,
                numero_ingreso=paciente.numero_ingresos  # Añadido
            )

            # Procesar cuidados marcados
            for cuidado in receta_actual.cuidados.all():
                if request.POST.get(f'cuidado_{cuidado.id}') == 'on':
                    RegistroCuidado.objects.create(
                        seguimiento=seguimiento,
                        cuidado=cuidado,
                        completado=True,
                        fecha_completado=timezone.now()
                    )

            # Procesar medicamentos marcados
            for medicamento in receta_actual.detalles.all():
                if request.POST.get(f'medicamento_{medicamento.id}') == 'on':
                    RegistroMedicamento.objects.create(
                        seguimiento=seguimiento,
                        medicamento=medicamento,
                        administrado=True,
                        fecha_administracion=timezone.now()
                    )

            messages.success(request, 'Registro guardado exitosamente')
            return redirect('enfermeria:cuidados_paciente', paciente_id=paciente_id)

        except Exception as e:
            messages.error(request, f'Error al guardar el registro: {str(e)}')
            return redirect('enfermeria:cuidados_paciente', paciente_id=paciente_id)

    # Para GET request
    context = {
        'paciente': paciente,
        'receta': receta_actual,
        'padecimientos': RecetaPadecimiento.objects.filter(receta=receta_actual).select_related('padecimiento') if receta_actual else None,
        'cuidados': RecetaCuidado.objects.filter(receta=receta_actual).select_related('cuidado') if receta_actual else None,
        'medicamentos': DetalleReceta.objects.filter(receta=receta_actual).select_related('medicamento') if receta_actual else None,
        'registros_recientes': SeguimientoCuidados.objects.filter(
            paciente=paciente
        ).order_by('-fecha_registro')[:5],
        'ultimo_registro': SeguimientoCuidados.objects.filter(
            paciente=paciente
        ).order_by('-fecha_registro').first()
    }

    return render(request, 'usuarioEnfermeria/cuidados_paciente.html', context)

@login_required
def formulario_paciente(request, paciente_id):
    if request.user.tipoUsuario not in ['EN', 'JP']:
        messages.error(request, 'No tienes permiso para acceder a esta sección')
        return redirect('login')
    
    paciente = get_object_or_404(Paciente, id=paciente_id)
    receta_actual = Receta.objects.filter(
        paciente=paciente,
        activa=True
    ).select_related('diagnostico').first()

    if request.method == 'POST':
        try:
            # Crear nuevo formulario de seguimiento con número de ingreso
            formulario = FormularioSeguimiento.objects.create(
                paciente=paciente,
                enfermero=request.user,
                notas_generales=request.POST.get('notas_generales', ''),
                numero_ingreso=paciente.numero_ingresos  # Añadido
            )

            # Procesar evaluación de padecimientos
            for padecimiento in receta_actual.padecimientos.all():
                estado = request.POST.get(f'estado_padecimiento_{padecimiento.id}')
                notas = request.POST.get(f'notas_padecimiento_{padecimiento.id}', '')
                
                if estado:
                    EvaluacionPadecimiento.objects.create(
                        formulario=formulario,
                        padecimiento=padecimiento,
                        estado=estado,
                        notas=notas
                    )

            # Procesar cuidados faltantes
            for cuidado in receta_actual.cuidados.all():
                if request.POST.get(f'cuidado_faltante_{cuidado.id}') == 'on':
                    motivo = request.POST.get(f'motivo_cuidado_{cuidado.id}', '')
                    CuidadoFaltante.objects.create(
                        formulario=formulario,
                        cuidado=cuidado,
                        motivo=motivo
                    )

            # Procesar medicamentos faltantes
            for medicamento in receta_actual.detalles.all():
                if request.POST.get(f'medicamento_faltante_{medicamento.id}') == 'on':
                    motivo = request.POST.get(f'motivo_medicamento_{medicamento.id}', '')
                    MedicamentoFaltante.objects.create(
                        formulario=formulario,
                        medicamento=medicamento,
                        motivo=motivo
                    )

            messages.success(request, 'Formulario guardado exitosamente')
            return redirect('enfermeria:formulario_paciente', paciente_id=paciente_id)

        except Exception as e:
            messages.error(request, f'Error al guardar el formulario: {str(e)}')
            return redirect('enfermeria:formulario_paciente', paciente_id=paciente_id)

    # Obtener el último registro explícitamente
    ultimo_registro = SeguimientoCuidados.objects.filter(
        paciente=paciente
    ).order_by('-fecha_registro').first()

    # Inicializar listas vacías
    cuidados_no_realizados = []
    medicamentos_no_administrados = []

    if receta_actual and ultimo_registro:
        # Obtener IDs de cuidados completados del último registro
        cuidados_realizados_ids = ultimo_registro.registrocuidado_set.filter(
            completado=True
        ).values_list('cuidado_id', flat=True)
        
        # Obtener cuidados no realizados
        cuidados_no_realizados = RecetaCuidado.objects.filter(
            receta=receta_actual
        ).exclude(
            id__in=cuidados_realizados_ids
        ).select_related('cuidado')

        # Obtener IDs de medicamentos administrados del último registro
        medicamentos_administrados_ids = ultimo_registro.registromedicamento_set.filter(
            administrado=True
        ).values_list('medicamento_id', flat=True)
        
        # Obtener medicamentos no administrados
        medicamentos_no_administrados = DetalleReceta.objects.filter(
            receta=receta_actual
        ).exclude(
            id__in=medicamentos_administrados_ids
        ).select_related('medicamento')

    context = {
        'paciente': paciente,
        'receta': receta_actual,
        'padecimientos': RecetaPadecimiento.objects.filter(receta=receta_actual).select_related('padecimiento') if receta_actual else None,
        'cuidados_no_realizados': cuidados_no_realizados,
        'medicamentos_no_administrados': medicamentos_no_administrados,
        'estados_padecimiento': FormularioSeguimiento.ESTADO_PADECIMIENTO,
        'registros_recientes': FormularioSeguimiento.objects.filter(
            paciente=paciente
        ).select_related(
            'enfermero'
        ).prefetch_related(
            'evaluacionpadecimiento_set__padecimiento__padecimiento',
            'cuidadofaltante_set__cuidado__cuidado',
            'medicamentofaltante_set__medicamento__medicamento'
        ).order_by('-fecha_registro')[:5]
    }

    return render(request, 'usuarioEnfermeria/formulario_paciente.html', context)