from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from login.models import *
from usuarioJefa.models import Paciente
from django.utils import timezone
from usuarioJefa.forms import PacienteForm
from django.contrib.auth.decorators import login_required
from .models import *
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt 
from datetime import datetime, timedelta
from usuarioDoctor.models import *
from usuarioEnfermeria.models import *
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Paciente
from usuarioEnfermeria.models import SeguimientoCuidados, FormularioSeguimiento
from django.utils import timezone
import calendar


def menu_jefa(request):
    return render(request, 'usuarioJefa/menu_jefa.html')

def pacientes_jefa(request):
    pacientes = Paciente.objects.select_related(
        'area', 
        'doctor_actual', 
        'enfermero_actual'
    ).filter(esta_activo=True)
    
    print(f"Número de pacientes activos: {pacientes.count()}")  # Debug
    
    context = {
        'pacientes': pacientes,
    }
    return render(request, 'usuarioJefa/pacientes_jefa.html', context)

@csrf_exempt  # Temporal para pruebas
def dar_alta_paciente(request, paciente_id):
    if request.method == 'POST':
        try:
            paciente = Paciente.objects.get(id=paciente_id)
            print(f"Dando de alta al paciente: {paciente.id}")  # Debug
            paciente.esta_activo = False
            paciente.estado = 'INACTIVO'
            paciente.fecha_alta = timezone.now()
            paciente.save()
            print(f"Estado actualizado: activo={paciente.esta_activo}, estado={paciente.estado}")  # Debug
            return JsonResponse({'status': 'success'})
        except Paciente.DoesNotExist:
            print(f"Paciente no encontrado: {paciente_id}")  # Debug
            return JsonResponse({'status': 'error', 'message': 'Paciente no encontrado'}, status=404)
        except Exception as e:
            print(f"Error al dar de alta: {str(e)}")  # Debug
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

def agregar_pacientes(request):
    if request.method == 'POST':
        form = PacienteForm(request.POST)
        if form.is_valid():
            try:
                paciente = form.save()
                messages.success(request, 'Paciente agregado exitosamente.')
            except Exception as e:
                messages.error(request, 'No se pudo crear el paciente. Por favor, intente nuevamente.')
        else:
            messages.error(request, 'Por favor, corrija los errores en el formulario.')
    else:
        form = PacienteForm()
    
    return render(request, 'usuarioJefa/agregar_pacientes.html', {
        'form': form,
        'titulo': 'Agregar Nuevo Paciente'
    })

def historiales_(request):
    tipo_historial = request.GET.get('tipo', 'pacientes')
    busqueda = request.GET.get('busqueda', '')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    if tipo_historial == 'pacientes':
        # Query para pacientes
        registros = Paciente.objects.all().select_related(
            'area',
            'doctor_actual',
            'enfermero_actual'
        ).prefetch_related(
            'recetas_doctor',
            'diagnosticos'
        )

        # Obtener doctores y enfermeros disponibles
        doctores = Usuarios.objects.filter(tipoUsuario='DR', estaActivo=True)
        enfermeros = Usuarios.objects.filter(tipoUsuario='EN', estaActivo=True)

        if busqueda:
            registros = registros.filter(
                Q(nombres__icontains=busqueda) |
                Q(apellidos__icontains=busqueda) |
                Q(num_seguridad_social__icontains=busqueda)
            )

        if fecha_inicio:
            registros = registros.filter(fecha_ingreso__gte=fecha_inicio)
        
        if fecha_fin:
            registros = registros.filter(fecha_ingreso__lte=fecha_fin)
            
        context = {
            'registros': registros,
            'tipo_historial': tipo_historial
        }
    else:
        # Query para empleados separados por tipo
        enfermeros = Usuarios.objects.filter(tipoUsuario='EN')
        doctores = Usuarios.objects.filter(tipoUsuario='DR')
        jefas = Usuarios.objects.filter(tipoUsuario='JP')
        cocina = Usuarios.objects.filter(tipoUsuario='CO')

        if busqueda:
            enfermeros = enfermeros.filter(
                Q(first_name__icontains=busqueda) |
                Q(apellidos__icontains=busqueda)
            )
            doctores = doctores.filter(
                Q(first_name__icontains=busqueda) |
                Q(apellidos__icontains=busqueda)
            )
            jefas = jefas.filter(
                Q(first_name__icontains=busqueda) |
                Q(apellidos__icontains=busqueda)
            )
            cocina = cocina.filter(
                Q(first_name__icontains=busqueda) |
                Q(apellidos__icontains=busqueda)
            )

        context = {
            'enfermeros': enfermeros.select_related('areaEspecialidad').prefetch_related('fortalezas'),
            'doctores': doctores.select_related('areaEspecialidad').prefetch_related('fortalezas'),
            'jefas': jefas.select_related('areaEspecialidad'),
            'cocina': cocina.select_related('areaEspecialidad'),
            'tipo_historial': tipo_historial,
            'busqueda': busqueda
        }

    return render(request, 'usuarioJefa/historiales.html', context)

def historial_empleados(request):
    # Obtener todos los usuarios
    usuarios = Usuarios.objects.all().select_related('areaEspecialidad').prefetch_related('fortalezas')
    
    # Ordenar por fecha de registro
    usuarios = usuarios.order_by('-fechaRegistro')

    return render(request, 'usuarioJefa/historial_empleados.html', {
        'usuarios': usuarios
    })

def historial_pacientes(request):
    busqueda = request.GET.get('busqueda', '')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    # Query base
    pacientes = Paciente.objects.all()

    # Aplicar filtros
    if busqueda:
        pacientes = pacientes.filter(
            Q(nombres__icontains=busqueda) | 
            Q(apellidos__icontains=busqueda) |
            Q(num_seguridad_social__icontains=busqueda)
        )

    if fecha_inicio:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        pacientes = pacientes.filter(fecha_ingreso__gte=fecha_inicio)

    if fecha_fin:
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
        pacientes = pacientes.filter(fecha_ingreso__lte=fecha_fin)

    # Prefetch related para optimizar consultas
    pacientes = pacientes.prefetch_related(
        'recetas_doctor',
        'diagnosticos',
        'recetas_doctor__detalles',
        'recetas_doctor__padecimientos',
        'recetas_doctor__cuidados'
    )

    context = {
        'pacientes': pacientes,
    }
    
    return render(request, 'usuarioJefa/historial_pacientes.html', context) 

def detalle_historial(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    
    # Obtener todos los números de ingreso únicos
    numeros_ingreso = set()
    numeros_ingreso.update(
        paciente.diagnosticos.values_list('numero_ingreso', flat=True),
        paciente.recetas_doctor.values_list('numero_ingreso', flat=True),
        SeguimientoCuidados.objects.filter(paciente=paciente).values_list('numero_ingreso', flat=True),
        FormularioSeguimiento.objects.filter(paciente=paciente).values_list('numero_ingreso', flat=True)
    )
    numeros_ingreso = sorted(numeros_ingreso, reverse=True)  # Ordenado de más reciente a más antiguo

    # Crear un diccionario con la información por ingreso
    historiales_por_ingreso = []
    for num_ingreso in numeros_ingreso:
        historial = {
            'numero_ingreso': num_ingreso,
            'diagnosticos': paciente.diagnosticos.filter(numero_ingreso=num_ingreso).order_by('-fecha_creacion'),
            'recetas': paciente.recetas_doctor.filter(numero_ingreso=num_ingreso).order_by('-fecha_creacion'),
            'seguimientos': SeguimientoCuidados.objects.filter(
                paciente=paciente, 
                numero_ingreso=num_ingreso
            ).order_by('-fecha_registro'),
            'formularios': FormularioSeguimiento.objects.filter(
                paciente=paciente, 
                numero_ingreso=num_ingreso
            ).order_by('-fecha_registro')
        }
        historiales_por_ingreso.append(historial)

    context = {
        'paciente': paciente,
        'historiales_por_ingreso': historiales_por_ingreso,
    }
    
    return render(request, 'usuarioJefa/detalle_historial.html', context)

@csrf_exempt
def reactivar_paciente(request, paciente_id):
    if request.method == 'POST':
        try:
            paciente = Paciente.objects.get(id=paciente_id)
            if not paciente.esta_activo:
                paciente.esta_activo = True
                paciente.estado = 'ACTIVO'
                paciente.numero_ingresos += 1
                paciente.fecha_ingreso = timezone.now()
                paciente.fecha_alta = None
                paciente.save()
                return JsonResponse({'status': 'success'})
            return JsonResponse({'status': 'error', 'message': 'El paciente ya está activo'})
        except Paciente.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Paciente no encontrado'}, status=404)
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

def usuarios_(request):
    # Datos para gestionar usuarios
    usuarios_activos = Usuarios.objects.filter(estaActivo=True)
    areas = AreaEspecialidad.objects.all()
    fortalezas = Fortaleza.objects.all()

    if request.method == 'POST':
        # Procesar formulario de creación de usuarios
        nombre = request.POST.get('nombre')
        apellidos = request.POST.get('apellidos')
        edad = request.POST.get('edad')
        fecha_nacimiento = request.POST.get('fecha_nacimiento')
        area_especialidad_id = request.POST.get('area_especialidad')
        fortalezas_ids = request.POST.getlist('fortalezas')
        tipo_usuario = request.POST.get('tipo_usuario')
        cedula = request.POST.get('cedula')
        nombre_temporal = request.POST.get('nombre_temporal')
        contraseña = request.POST.get('contraseña')

        try:
            # Obtener el área de especialidad
            area_especialidad = AreaEspecialidad.objects.get(id=area_especialidad_id)

            # Crear el usuario
            usuario = Usuarios.objects.create(
                first_name=nombre,
                apellidos=apellidos,
                edad=edad,
                fechaNacimiento=fecha_nacimiento,
                areaEspecialidad=area_especialidad,
                tipoUsuario=tipo_usuario,
                cedula=cedula,
                username=nombre_temporal,
                estaActivo=True,
                primerIngreso=True
            )

            # Asignar la contraseña al usuario
            usuario.set_password(contraseña)
            usuario.save()

            # Asignar las fortalezas al usuario
            usuario.fortalezas.set(fortalezas_ids)

            messages.success(request, 'Usuario creado exitosamente.')
            return redirect('jefa:usuarios_')  # Recargar la página principal
        except AreaEspecialidad.DoesNotExist:
            messages.error(request, 'El área de especialidad seleccionada no existe.')
        except Exception as e:
            messages.error(request, f'Error al crear el usuario: {str(e)}')

    return render(request, 'usuarioJefa/usuarios_.html', {
        'usuarios': usuarios_activos,
        'areas': areas,
        'fortalezas': fortalezas
    })

def gestionar_usuarios(request):
    # Filtrar solo usuarios activos
    usuarios = Usuarios.objects.filter(estaActivo=True).order_by('tipoUsuario', 'first_name')
    return render(request, 'usuarioJefa/gestionar_usuarios.html', {'usuarios': usuarios})

from datetime import date
from django.shortcuts import render, redirect
from django.contrib import messages

def crear_usuarios(request):
    if request.method == 'POST':
        # Obtener los datos del formulario
        nombre = request.POST.get('nombre')
        apellidos = request.POST.get('apellidos')
        fecha_nacimiento = request.POST.get('fecha_nacimiento')
        area_especialidad_id = request.POST.get('area_especialidad')
        fortalezas_ids = request.POST.getlist('fortalezas')
        tipo_usuario = request.POST.get('tipo_usuario')
        cedula = request.POST.get('cedula')
        nombre_temporal = request.POST.get('nombre_temporal')
        contraseña = request.POST.get('contraseña')

        try:
            # Validar la fecha de nacimiento y calcular la edad
            if fecha_nacimiento:
                nacimiento = date.fromisoformat(fecha_nacimiento)
                hoy = date.today()
                edad = hoy.year - nacimiento.year - ((hoy.month, hoy.day) < (nacimiento.month, nacimiento.day))

                if edad < 18:
                    messages.error(request, 'El usuario debe ser mayor de 18 años.')
                    return redirect('jefa:crear_usuario')

            # Obtener el área de especialidad
            area_especialidad = AreaEspecialidad.objects.get(id=area_especialidad_id)

            # Crear el usuario
            usuario = Usuarios.objects.create(
                first_name=nombre,
                apellidos=apellidos,
                edad=edad,
                fechaNacimiento=fecha_nacimiento,
                areaEspecialidad=area_especialidad,
                tipoUsuario=tipo_usuario,
                cedula=cedula,
                username=nombre_temporal,
                estaActivo=True,
                primerIngreso=True
            )

            # Asignar la contraseña al usuario
            usuario.set_password(contraseña)
            usuario.save()

            # Asignar las fortalezas al usuario
            usuario.fortalezas.set(fortalezas_ids)

            messages.success(request, 'Usuario creado exitosamente.')
            return redirect('jefa:usuarios_')

        except AreaEspecialidad.DoesNotExist:
            messages.error(request, 'El área de especialidad seleccionada no existe.')
        except Exception as e:
            messages.error(request, f'Error al crear el usuario: {str(e)}')

    areas = AreaEspecialidad.objects.all()
    fortalezas = Fortaleza.objects.all()

    context = {
        'areas': areas,
        'fortalezas': fortalezas,
    }
    return render(request, 'usuarioJefa/crear_usuarios.html', context)


def editar_usuario(request, usuario_id):
    usuario = get_object_or_404(Usuarios, id=usuario_id)
    
    if request.method == 'POST':
        try:
            # Actualizar solo los campos que se enviaron
            if request.POST.get('nombre'):
                usuario.first_name = request.POST.get('nombre')
            if request.POST.get('apellidos'):
                usuario.apellidos = request.POST.get('apellidos')
            if request.POST.get('edad'):
                usuario.edad = request.POST.get('edad')
            if request.POST.get('fecha_nacimiento'):
                usuario.fechaNacimiento = request.POST.get('fecha_nacimiento')
            if request.POST.get('area_especialidad'):
                usuario.areaEspecialidad_id = request.POST.get('area_especialidad')
            if request.POST.getlist('fortalezas'):
                usuario.fortalezas.set(request.POST.getlist('fortalezas'))
            if request.POST.get('tipo_usuario'):
                usuario.tipoUsuario = request.POST.get('tipo_usuario')
            if request.POST.get('cedula'):
                usuario.cedula = request.POST.get('cedula')
                
            usuario.save()
            messages.success(request, 'Usuario actualizado correctamente')
            return redirect('jefa:usuarios_')
            
        except Exception as e:
            messages.error(request, f'Error al actualizar el usuario: {str(e)}')
    
    # Para GET request, enviamos el mismo template con los datos actuales
    context = {
        'usuario': usuario,
        'areas': AreaEspecialidad.objects.all(),
        'fortalezas': Fortaleza.objects.all(),
        'modo_edicion': True  # Para identificar que estamos editando
    }
    return render(request, 'usuarioJefa/editar_usuario.html', context)

def toggle_usuario(request, usuario_id):
    if request.method == 'POST':
        usuario = get_object_or_404(Usuarios, id=usuario_id)
        action = request.POST.get('action')
        # Obtener la URL de la página anterior
        referer = request.META.get('HTTP_REFERER')
        
        try:
            if action == 'desactivar':
                usuario.estaActivo = False
                fecha_eliminacion = timezone.now()
                usuario.fechaEliminacion = fecha_eliminacion
                usuario.save()
                messages.success(request, 'Usuario desactivado correctamente')
            
            elif action == 'activar':
                usuario.estaActivo = True
                usuario.fechaEliminacion = None
                usuario.save()
                messages.success(request, 'Usuario activado correctamente')
                
        except Exception as e:
            messages.error(request, f'Error al modificar el estado del usuario: {str(e)}')
        
        # Si viene de historial, redirigir allí
        if 'historial' in referer:
            return redirect('jefa:historiales_')
        # Si no, redirigir a gestionar usuarios
        return redirect('jefa:usuarios_')
    
    return redirect('jefa:usuarios_')

@login_required
def almacen_(request):
    tipo_vista = request.GET.get('tipo', 'medicamentos')  # Por defecto muestra medicamentos
    
    if request.method == 'POST':
        if 'agregar_medicamento' in request.POST:
            try:
                nombre = request.POST.get('nombre')
                gramaje = request.POST.get('gramaje')
                cantidad = request.POST.get('cantidad', 0)
                compuestos = request.POST.getlist('compuestos')

                medicamento = Medicamento.objects.create(
                    nombre=nombre,
                    gramaje=gramaje,
                    cantidad_disponible=cantidad
                )
                medicamento.compuestos.set(compuestos)
                messages.success(request, 'Medicamento agregado exitosamente')
            except Exception as e:
                messages.error(request, f'Error al agregar medicamento: {str(e)}')

        elif 'agregar_instrumento' in request.POST:
            try:
                nombre = request.POST.get('nombre')
                cantidad = request.POST.get('cantidad', 0)
                especificaciones = request.POST.get('especificaciones')

                Instrumento.objects.create(
                    nombre=nombre,
                    cantidad=cantidad,
                    especificaciones=especificaciones
                )
                messages.success(request, 'Instrumento agregado exitosamente')
            except Exception as e:
                messages.error(request, f'Error al agregar instrumento: {str(e)}')

    # Siempre cargar ambos tipos de datos
    context = {
        'tipo_vista': tipo_vista,
        'medicamentos': Medicamento.objects.all().prefetch_related('compuestos'),
        'instrumentos': Instrumento.objects.all(),
        'compuestos': Compuesto.objects.all(),
    }
    return render(request, 'usuarioJefa/almacen_.html', context)

@login_required
def editar_medicamento(request, medicamento_id):
    medicamento = get_object_or_404(Medicamento, id=medicamento_id)
    if request.method == 'POST':
        try:
            medicamento.nombre = request.POST.get('nombre')
            medicamento.gramaje = request.POST.get('gramaje')
            medicamento.cantidad_disponible = request.POST.get('cantidad')
            medicamento.compuestos.set(request.POST.getlist('compuestos'))
            medicamento.save()
            messages.success(request, 'Medicamento actualizado exitosamente')
        except Exception as e:
            messages.error(request, f'Error al actualizar medicamento: {str(e)}')
        return redirect(f'{reverse("jefa:almacen_")}?tipo=medicamentos')
    return redirect(f'{reverse("jefa:almacen_")}?tipo=medicamentos')

@login_required
def editar_instrumento(request, instrumento_id):
    instrumento = get_object_or_404(Instrumento, id=instrumento_id)
    if request.method == 'POST':
        try:
            instrumento.nombre = request.POST.get('nombre')
            instrumento.cantidad = request.POST.get('cantidad')
            instrumento.especificaciones = request.POST.get('especificaciones')
            instrumento.save()
            messages.success(request, 'Instrumento actualizado exitosamente')
        except Exception as e:
            messages.error(request, f'Error al actualizar instrumento: {str(e)}')
        return redirect(f'{reverse('jefa:almacen_')}?tipo=instrumentos')
    return redirect(f'{reverse('jefa:almacen_')}?tipo=instrumentos')

@login_required
def eliminar_medicamento(request, medicamento_id):
    if request.method == 'POST':
        try:
            medicamento = get_object_or_404(Medicamento, id=medicamento_id)
            medicamento.delete()
            messages.success(request, 'Medicamento eliminado exitosamente')
        except Exception as e:
            messages.error(request, f'Error al eliminar medicamento: {str(e)}')
    return redirect('jefa:almacen_')

@login_required
def eliminar_instrumento(request, instrumento_id):
    if request.method == 'POST':
        try:
            instrumento = get_object_or_404(Instrumento, id=instrumento_id)
            instrumento.delete()
            messages.success(request, 'Instrumento eliminado exitosamente')
        except Exception as e:
            messages.error(request, f'Error al eliminar instrumento: {str(e)}')
    return redirect(f'{reverse('jefa:almacen_')}?tipo=instrumentos')

@login_required
def get_medicamento(request, medicamento_id):
    medicamento = get_object_or_404(Medicamento, id=medicamento_id)
    return JsonResponse({
        'nombre': medicamento.nombre,
        'gramaje': medicamento.gramaje,
        'cantidad_disponible': medicamento.cantidad_disponible,
        'compuestos': list(medicamento.compuestos.values_list('id', flat=True))
    })

@login_required
def get_instrumento(request, instrumento_id):

    instrumento = get_object_or_404(Instrumento, id=instrumento_id)
    return JsonResponse({
        'nombre': instrumento.nombre,
        'cantidad': instrumento.cantidad,
        'especificaciones': instrumento.especificaciones
    })


#//////////////////////////////////////////////////////////////////
#////////////////////////////////////////////////////////////////////
#/777777777777777777777777777777777777777777777777777777777777777777

# views.py
def calendario_area(request):
    areas = AreaEspecialidad.objects.all()
    enfermeros = Usuarios.objects.filter(tipoUsuario='EN', estaActivo=True)
    bimestres = range(1,7)
    area_seleccionada = request.GET.get('area')

    # Para cada enfermero, obtener su última área asignada
    areas_excluidas = {}
    for enfermero in enfermeros:
        ultima_asignacion = AsignacionCalendario.objects.filter(
            enfermero=enfermero
        ).order_by('-year', '-bimestre').first()
        
        if ultima_asignacion:
            areas_excluidas[enfermero.id] = ultima_asignacion.area.id
    
    if area_seleccionada:
        area = AreaEspecialidad.objects.get(id=area_seleccionada)
        mes_actual = datetime.now().month
        año_actual = datetime.now().year
        cal = calendar.monthcalendar(año_actual, mes_actual)
        
        # Obtener asignaciones del mes actual
        asignaciones = AsignacionCalendario.objects.filter(
            area=area,
            fecha_inicio__year=año_actual,
            fecha_inicio__month=mes_actual
        ).select_related('enfermero')
        
        # Obtener TODO el historial de cambios para el área sin filtrar por fecha
        historial = HistorialCambios.objects.filter(
            Q(area_anterior_id=area_seleccionada) | Q(area_nueva_id=area_seleccionada)
        ).select_related(
            'asignacion__enfermero',
            'area_anterior',
            'area_nueva'
        ).order_by('-fecha_cambio')
        
        # Debug para verificar si hay registros
        print(f"Historial encontrado: {historial.count()} registros")
    else:
        area = None
        cal = None
        asignaciones = None
        historial = None
        mes_actual = datetime.now().month
        año_actual = datetime.now().year

    if area_seleccionada:
        area = AreaEspecialidad.objects.get(id=area_seleccionada)
        mes_actual = datetime.now().month
        año_actual = datetime.now().year
        cal = calendar.monthcalendar(año_actual, mes_actual)
        
        # Asignaciones del mes actual
        asignaciones = AsignacionCalendario.objects.filter(
            area=area,
            fecha_inicio__year=año_actual,
            fecha_inicio__month=mes_actual
        ).select_related('enfermero')
        
        # Historial completo de asignaciones para el área
        historial_asignaciones = AsignacionCalendario.objects.filter(
            area=area
        ).select_related('enfermero').order_by('-fecha_inicio')
        
        # Historial de modificaciones
        historial = HistorialCambios.objects.filter(
            Q(area_anterior_id=area_seleccionada) | Q(area_nueva_id=area_seleccionada)
        ).select_related(
            'asignacion__enfermero',
            'area_anterior',
            'area_nueva'
        ).order_by('-fecha_cambio')
        
    else:
        area = None
        cal = None
        asignaciones = None
        historial = None
        historial_asignaciones = None
        mes_actual = datetime.now().month
        año_actual = datetime.now().year

    context = {
        'areas': areas,
        'all_areas': areas,
        'enfermeros': enfermeros,
        'area_seleccionada': area,
        'calendario': cal,
        'asignaciones': asignaciones,
        'areas_excluidas': areas_excluidas,
        'bimestres': bimestres,
        'mes_actual': mes_actual,
        'año_actual': año_actual,
        'historial': historial,
        'historial_asignaciones': historial_asignaciones,
    }
    
    return render(request, 'usuariojefa/calendario.html', context)

def get_dias_bimestre(bimestre, año):
   """Calcula los días del bimestre considerando año bisiesto"""
   
   # Determinar si es año bisiesto
   es_bisiesto = año % 4 == 0 and (año % 100 != 0 or año % 400 == 0)
   
   # Días por mes considerando febrero bisiesto
   dias_por_mes = [31, 29 if es_bisiesto else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
   
   # Determinar meses del bimestre
   mes_inicio = ((bimestre - 1) * 2) + 1
   mes_fin = mes_inicio + 1 if mes_inicio < 12 else 12
   
   # Sumar días de los dos meses
   total_dias = dias_por_mes[mes_inicio-1] + dias_por_mes[mes_fin-1]
   
   return total_dias

def crear_asignacion(request):
   if request.method == 'GET':
       enfermeros = Usuarios.objects.filter(tipoUsuario='EN', estaActivo=True)
       all_areas = AreaEspecialidad.objects.all()
       bimestres = range(1,7)

       # Para cada enfermero, obtener su última área asignada
       areas_excluidas = {}
       for enfermero in enfermeros:
           ultima_asignacion = AsignacionCalendario.objects.filter(
               enfermero=enfermero
           ).order_by('-year', '-bimestre').first()
           
           if ultima_asignacion:
               areas_excluidas[enfermero.id] = ultima_asignacion.area.id

       context = {
           'enfermeros': enfermeros,
           'all_areas': all_areas,
           'areas_excluidas': areas_excluidas,
           'bimestres': bimestres
       }
       return render(request, 'usuariojefa/crear_asignacion.html', context)

   if request.method == 'POST':
       enfermero_id = request.POST.get('enfermero') 
       area_id = request.POST.get('area')
       bimestre = int(request.POST.get('bimestre'))
       año_actual = datetime.now().year

       if not all([enfermero_id, area_id, bimestre]):
           messages.error(request, 'Todos los campos son requeridos')
           return redirect('jefa:calendario_area')

       if not 1 <= bimestre <= 6:
           messages.error(request, 'El bimestre debe estar entre 1 y 6')
           return redirect('jefa:calendario_area')

       # Validar área no repetida
       ultima_asignacion = AsignacionCalendario.objects.filter(
           enfermero_id=enfermero_id
       ).order_by('-year', '-bimestre').first()

       if ultima_asignacion and ultima_asignacion.area_id == int(area_id):
           messages.error(request, 'No se puede asignar la misma área dos bimestres seguidos')
           return redirect('jefa:calendario_area')

       mes_inicio = ((bimestre - 1) * 2) + 1
       fecha_inicio = datetime(año_actual, mes_inicio, 1)
       dias_bimestre = get_dias_bimestre(bimestre, año_actual)
       fecha_fin = fecha_inicio + timedelta(days=dias_bimestre-1)

       # Validar solapamiento
       solapamiento = AsignacionCalendario.objects.filter(
           enfermero_id=enfermero_id,
           fecha_inicio__lt=fecha_fin,
           fecha_fin__gt=fecha_inicio
       ).exists()

       if solapamiento:
           messages.error(request, 'Ya existe una asignación en ese periodo')
           return redirect('jefa:calendario_area')

       try:
           AsignacionCalendario.objects.create(
               enfermero_id=enfermero_id,
               area_id=area_id,
               fecha_inicio=fecha_inicio,
               fecha_fin=fecha_fin,
               bimestre=bimestre,
               year=año_actual
           )
           messages.success(request, 'Asignación creada exitosamente')
       except Exception as e:
           messages.error(request, f'Error al crear asignación: {str(e)}')
       
       return redirect('jefa:calendario_area')

def modificar_asignacion(request):
    if request.method == 'POST':
        enfermero_id = request.POST.get('enfermero')
        area_nueva_id = request.POST.get('area')
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')

        try:
            # Obtener la asignación actual usando la fecha proporcionada
            asignacion = AsignacionCalendario.objects.get(
                enfermero_id=enfermero_id,
                activo=True,
                fecha_inicio__lte=fecha_inicio,
                fecha_fin__gte=fecha_inicio
            )
            
            # Guardar datos anteriores antes de modificar
            area_anterior = asignacion.area
            fecha_inicio_anterior = asignacion.fecha_inicio
            fecha_fin_anterior = asignacion.fecha_fin
            
            # Realizar la modificación
            nueva_area = AreaEspecialidad.objects.get(id=area_nueva_id)
            asignacion.area = nueva_area
            asignacion.fecha_inicio = fecha_inicio
            asignacion.fecha_fin = fecha_fin
            asignacion.save()
            
            # Registrar el cambio en el historial
            HistorialCambios.objects.create(
                asignacion=asignacion,
                area_anterior=area_anterior,
                area_nueva=nueva_area,
                fecha_inicio_anterior=fecha_inicio_anterior,
                fecha_fin_anterior=fecha_fin_anterior,
                fecha_inicio_nueva=fecha_inicio,
                fecha_fin_nueva=fecha_fin
            )
            
            messages.success(request, 'Asignación modificada exitosamente')
        except AsignacionCalendario.DoesNotExist:
            messages.error(request, 'No se encontró una asignación activa para este enfermero en las fechas seleccionadas')
        except AsignacionCalendario.MultipleObjectsReturned:
            messages.error(request, 'Hay múltiples asignaciones para este enfermero en las fechas seleccionadas')
        except Exception as e:
            messages.error(request, f'Error al modificar asignación: {str(e)}')

        return redirect('jefa:calendario_area')
    
def eliminar_asignacion(request, asignacion_id):
    try:
        asignacion = AsignacionCalendario.objects.get(id=asignacion_id)
        asignacion.delete()
        messages.success(request, 'Asignación eliminada exitosamente')
    except Exception as e:
        messages.error(request, f'Error al eliminar asignación: {str(e)}')
    
    return redirect('calendario_area')