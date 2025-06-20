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
from django.db.models import Q, Count
from .models import Paciente
from usuarioEnfermeria.models import SeguimientoCuidados, FormularioSeguimiento
from django.utils import timezone
import calendar
from .forms import *
from django.db import transaction
from functools import wraps
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
        try:
            if form.is_valid():
                paciente = form.save()
                messages.success(request, 'Paciente agregado exitosamente.')
                return redirect('jefa:pacientes_jefa')
        except form.ValidationError as e:
            if str(e) == "['INACTIVO']":
                print("Paciente inactivo encontrado")  # Debug
                paciente_inactivo = form.paciente_inactivo
                print(f"ID del paciente: {paciente_inactivo.id}")  # Debug
                context = {
                    'form': form,
                    'paciente_inactivo': paciente_inactivo,
                    'titulo': 'Paciente Encontrado',
                    'confirmar_reactivacion': True  # Asegurándonos que esto es True
                }
                print("Context:", context)  # Debug
                return render(request, 'usuarioJefa/agregar_pacientes.html', context)
            else:
                messages.error(request, str(e))
    else:
        form = PacienteForm()
    
    return render(request, 'usuarioJefa/agregar_pacientes.html', {
        'form': form,
        'titulo': 'Agregar Nuevo Paciente'
    })

def reactivar_paciente_(request, paciente_id):
    if request.method == 'POST':
        try:
            paciente = Paciente.objects.get(id=paciente_id)
            if not paciente.esta_activo:
                paciente.esta_activo = True
                paciente.estado = 'ACTIVO'
                paciente.fecha_alta = None
                paciente.fecha_ingreso = timezone.now()
                paciente.numero_ingresos += 1
                paciente.save()
                messages.success(request, 'Paciente reactivado exitosamente.')
            else:
                messages.error(request, 'El paciente ya está activo.')
        except Paciente.DoesNotExist:
            messages.error(request, 'No se encontró el paciente.')
        except Exception as e:
            messages.error(request, f'Error al reactivar paciente: {str(e)}')
    
    return redirect('jefa:pacientes_jefa')

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
    usuarios_activos = Usuarios.objects.filter(estaActivo=True).order_by(
    models.Case(
        models.When(tipoUsuario='JP', then=models.Value(1)),
        models.When(tipoUsuario='EN', then=models.Value(2)),
        models.When(tipoUsuario='DR', then=models.Value(3)),
        default=models.Value(4),
        output_field=models.IntegerField()
    ),
    'first_name',
    'apellidos'
    )
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
            # Obtener el área de especialidad solo si se proporcionó
            area_especialidad = None
            if area_especialidad_id and area_especialidad_id.strip():
                try:
                    area_especialidad = AreaEspecialidad.objects.get(id=area_especialidad_id)
                except AreaEspecialidad.DoesNotExist:
                    messages.error(request, 'El área de especialidad seleccionada no existe.')
                    return render(request, 'usuarioJefa/usuarios_.html', {
                        'usuarios': usuarios_activos,
                        'areas': areas,
                        'fortalezas': fortalezas
                    })

            # Validar que enfermería tenga área de especialidad
            if tipo_usuario == 'EN' and not area_especialidad:
                messages.error(request, 'El área de especialidad es obligatoria para usuarios de Enfermería.')
                return render(request, 'usuarioJefa/usuarios_.html', {
                    'usuarios': usuarios_activos,
                    'areas': areas,
                    'fortalezas': fortalezas
                })

            # Crear el usuario
            usuario = Usuarios.objects.create(
                first_name=nombre,
                apellidos=apellidos,
                edad=edad,
                fechaNacimiento=fecha_nacimiento,
                areaEspecialidad=area_especialidad,  # Puede ser None para doctores
                tipoUsuario=tipo_usuario,
                cedula=cedula,
                username=nombre_temporal,
                estaActivo=True,
                primerIngreso=True
            )

            # Asignar la contraseña al usuario
            usuario.set_password(contraseña)
            usuario.save()

            # Asignar las fortalezas al usuario solo si hay alguna seleccionada
            if fortalezas_ids:
                usuario.fortalezas.set(fortalezas_ids)

            messages.success(request, 'Usuario creado exitosamente.')
            return redirect('jefa:usuarios_')  # Recargar la página principal
            
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
            edad = None  # Valor por defecto
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
                edad=edad,  # Ahora puede ser None
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

# usuarioJefa/views.py - Views actualizadas para múltiples áreas

from django.db import transaction
from usuarioDoctor.models import Padecimiento

# usuarioJefa/views.py - Views actualizadas para múltiples áreas

from django.db import transaction
from usuarioDoctor.models import Padecimiento

# usuarioJefa/views.py - Views actualizadas para múltiples áreas

from django.db import transaction
from usuarioDoctor.models import Padecimiento

@login_required
def areas_fortalezas(request):
    """
    Vista unificada integrada con la funcionalidad existente
    """
    areas = AreaEspecialidad.objects.all().prefetch_related('fortalezas', 'padecimientos_relacionados')
    fortalezas = Fortaleza.objects.all().prefetch_related('areas', 'padecimientos_asociados')
    padecimientos = Padecimiento.objects.filter(activo=True).prefetch_related('areas', 'fortalezas')
    
    context = {
        'areas': areas,
        'fortalezas': fortalezas,
        'padecimientos': padecimientos,
    }
    
    return render(request, 'usuarioJefa/areas_fortalezas.html', context)

@login_required
@transaction.atomic
def crear_area(request):
    """
    Crear área con fortalezas y padecimientos - VERSIÓN CORREGIDA
    """
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion', '')
        fortalezas_ids = request.POST.getlist('fortalezas')
        padecimientos_ids = request.POST.getlist('padecimientos')
        
        try:
            # Validar datos básicos
            if not nombre or not nombre.strip():
                messages.error(request, 'El nombre del área es obligatorio')
                return redirect('jefa:areas_fortalezas')
            
            # Verificar que no exista otra área con el mismo nombre
            if AreaEspecialidad.objects.filter(nombre=nombre.strip()).exists():
                messages.error(request, f'Ya existe un área con el nombre "{nombre}"')
                return redirect('jefa:areas_fortalezas')
            
            # Validar máximo 4 fortalezas
            if len(fortalezas_ids) > 4:
                messages.error(request, 'No se pueden asignar más de 4 fortalezas a un área.')
                return redirect('jefa:areas_fortalezas')
            
            # Crear área
            area = AreaEspecialidad.objects.create(
                nombre=nombre.strip(),
                descripcion=descripcion.strip()
            )
            
            # CORRECCIÓN: Asignar fortalezas usando relación bidireccional
            if fortalezas_ids:
                fortalezas = Fortaleza.objects.filter(id__in=fortalezas_ids)
                
                # Asignar desde el área hacia las fortalezas
                area.fortalezas.set(fortalezas)
                
                # IMPORTANTE: También actualizar la relación inversa
                for fortaleza in fortalezas:
                    fortaleza.areas.add(area)
            
            # Asignar padecimientos al área
            if padecimientos_ids:
                padecimientos = Padecimiento.objects.filter(id__in=padecimientos_ids)
                for padecimiento in padecimientos:
                    padecimiento.areas.add(area)
            
            messages.success(request, f'Área "{area.nombre}" creada exitosamente con {len(fortalezas_ids)} fortalezas y {len(padecimientos_ids)} padecimientos.')
            
        except Exception as e:
            messages.error(request, f'Error al crear el área: {str(e)}')
    
    return redirect('jefa:areas_fortalezas')

@login_required
@transaction.atomic
def editar_area(request, area_id):
    """
    Editar área con datos precargados - VERSIÓN CORREGIDA
    """
    area = get_object_or_404(AreaEspecialidad, id=area_id)
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion', '')
        fortalezas_ids = request.POST.getlist('fortalezas')
        padecimientos_ids = request.POST.getlist('padecimientos')
        
        try:
            # Validar datos básicos
            if not nombre or not nombre.strip():
                messages.error(request, 'El nombre del área es obligatorio')
                return redirect('jefa:areas_fortalezas')
            
            # Verificar que no exista otra área con el mismo nombre (excluyendo la actual)
            if AreaEspecialidad.objects.filter(nombre=nombre.strip()).exclude(id=area_id).exists():
                messages.error(request, f'Ya existe otra área con el nombre "{nombre}"')
                return redirect('jefa:areas_fortalezas')
            
            # Validar máximo 4 fortalezas
            if len(fortalezas_ids) > 4:
                messages.error(request, 'No se pueden asignar más de 4 fortalezas a un área.')
                return redirect('jefa:areas_fortalezas')
            
            # Actualizar datos básicos
            area.nombre = nombre.strip()
            area.descripcion = descripcion.strip()
            area.save()
            
            # CORRECCIÓN: Limpiar y reasignar fortalezas correctamente
            
            # 1. Remover esta área de todas las fortalezas que la tenían antes
            fortalezas_anteriores = list(area.fortalezas.all())
            for fortaleza_anterior in fortalezas_anteriores:
                fortaleza_anterior.areas.remove(area)
            
            # 2. Limpiar la relación desde el área
            area.fortalezas.clear()
            
            # 3. Asignar nuevas fortalezas
            if fortalezas_ids:
                fortalezas_nuevas = Fortaleza.objects.filter(id__in=fortalezas_ids)
                
                # Asignar desde el área
                area.fortalezas.set(fortalezas_nuevas)
                
                # Asignar desde las fortalezas (relación inversa)
                for fortaleza in fortalezas_nuevas:
                    fortaleza.areas.add(area)
            
            # CORRECCIÓN: Limpiar y reasignar padecimientos correctamente
            
            # 1. Remover esta área de todos los padecimientos que la tenían
            padecimientos_anteriores = Padecimiento.objects.filter(areas=area)
            for padecimiento_anterior in padecimientos_anteriores:
                padecimiento_anterior.areas.remove(area)
            
            # 2. Asignar nuevos padecimientos
            if padecimientos_ids:
                padecimientos_nuevos = Padecimiento.objects.filter(id__in=padecimientos_ids)
                for padecimiento in padecimientos_nuevos:
                    padecimiento.areas.add(area)
            
            messages.success(request, f'Área "{area.nombre}" actualizada exitosamente.')
            
        except Exception as e:
            messages.error(request, f'Error al actualizar el área: {str(e)}')
    
    # Para GET request, mostrar formulario con datos precargados
    fortalezas = Fortaleza.objects.all()
    padecimientos = Padecimiento.objects.filter(activo=True)
    
    return render(request, 'usuarioJefa/editar_area.html', {
        'area': area,
        'fortalezas': fortalezas,
        'padecimientos': padecimientos
    })

@login_required
def crear_fortaleza(request):
    """
    Mantiene la funcionalidad básica existente
    """
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        
        try:
            Fortaleza.objects.create(
                nombre=nombre,
                descripcion=descripcion
            )
            messages.success(request, 'Fortaleza creada exitosamente.')
            return redirect('jefa:areas_fortalezas')
        except Exception as e:
            messages.error(request, f'Error al crear la fortaleza: {str(e)}')
    
    return render(request, 'usuarioJefa/crear_fortaleza.html')

@login_required
def obtener_area(request, area_id):
    """
    API para obtener datos de un área específica para edición
    """
    try:
        area = get_object_or_404(AreaEspecialidad, id=area_id)
        
        return JsonResponse({
            'id': area.id,
            'nombre': area.nombre,
            'descripcion': area.descripcion or '',
            'fortalezas': list(area.fortalezas.values_list('id', flat=True)),
            'padecimientos': list(area.padecimientos_relacionados.values_list('id', flat=True))
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def editar_fortaleza(request, fortaleza_id):
    """
    Mantiene la funcionalidad básica existente
    """
    fortaleza = get_object_or_404(Fortaleza, id=fortaleza_id)
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        
        try:
            fortaleza.nombre = nombre
            fortaleza.descripcion = descripcion
            fortaleza.save()
            messages.success(request, 'Fortaleza actualizada exitosamente.')
            return redirect('jefa:areas_fortalezas')
        except Exception as e:
            messages.error(request, f'Error al actualizar la fortaleza: {str(e)}')
    
    return render(request, 'usuarioJefa/editar_fortaleza.html', {'fortaleza': fortaleza})

# =========== NUEVAS VIEWS AVANZADAS ===========

@login_required
@transaction.atomic
def crear_fortaleza_avanzada(request):
    """
    Nueva vista para crear fortalezas con múltiples áreas y padecimientos - CORREGIDA
    """
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion', '')
        areas_ids = request.POST.getlist('areas')
        padecimientos_ids = request.POST.getlist('padecimientos')
        
        try:
            # Validar datos
            if not nombre:
                messages.error(request, 'El nombre de la fortaleza es obligatorio')
                return redirect('jefa:areas_fortalezas')
            
            # Verificar que no exista otra fortaleza con el mismo nombre
            if Fortaleza.objects.filter(nombre=nombre).exists():
                messages.error(request, f'Ya existe una fortaleza con el nombre "{nombre}"')
                return redirect('jefa:areas_fortalezas')
            
            # Validar que las áreas seleccionadas no excedan el límite de 4 fortalezas
            for area_id in areas_ids:
                area = AreaEspecialidad.objects.get(id=area_id)
                fortalezas_actuales = area.fortalezas.count()
                if fortalezas_actuales >= 4:
                    messages.error(request, f'El área "{area.nombre}" ya tiene 4 fortalezas. No se pueden agregar más.')
                    return redirect('jefa:areas_fortalezas')
            
            # Crear fortaleza
            fortaleza = Fortaleza.objects.create(
                nombre=nombre,
                descripcion=descripcion
            )
            
            # CORRECCIÓN: Asociar áreas múltiples con validación bidireccional
            if areas_ids:
                for area_id in areas_ids:
                    area = AreaEspecialidad.objects.get(id=area_id)
                    
                    # Verificar nuevamente el límite antes de agregar
                    if area.fortalezas.count() < 4:
                        # Agregar desde ambos lados de la relación
                        fortaleza.areas.add(area)
                        area.fortalezas.add(fortaleza)
                    else:
                        messages.warning(request, f'No se pudo agregar a "{area.nombre}" porque ya tiene 4 fortalezas')
            
            # Asociar padecimientos
            if padecimientos_ids:
                padecimientos = Padecimiento.objects.filter(id__in=padecimientos_ids)
                for padecimiento in padecimientos:
                    padecimiento.fortalezas.add(fortaleza)
            
            messages.success(request, f'Fortaleza "{fortaleza.nombre}" creada exitosamente')
            
        except Exception as e:
            messages.error(request, f'Error al crear fortaleza: {str(e)}')
    
    return redirect('jefa:areas_fortalezas')

@login_required
@transaction.atomic
def crear_padecimiento(request):
    """
    Nueva vista para crear padecimientos con múltiples áreas y fortalezas
    """
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion', '')
        areas_ids = request.POST.getlist('areas')
        fortalezas_ids = request.POST.getlist('fortalezas')
        
        try:
            # Validar datos
            if not nombre:
                messages.error(request, 'El nombre del padecimiento es obligatorio')
                return redirect('jefa:areas_fortalezas')
            
            # Verificar que no exista otro padecimiento con el mismo nombre
            if Padecimiento.objects.filter(nombre=nombre).exists():
                messages.error(request, f'Ya existe un padecimiento con el nombre "{nombre}"')
                return redirect('jefa:areas_fortalezas')
            
            # Crear padecimiento
            padecimiento = Padecimiento.objects.create(
                nombre=nombre,
                descripcion=descripcion
            )
            
            # Asociar áreas múltiples
            if areas_ids:
                areas = AreaEspecialidad.objects.filter(id__in=areas_ids)
                padecimiento.areas.set(areas)
            
            # Asociar fortalezas
            if fortalezas_ids:
                fortalezas = Fortaleza.objects.filter(id__in=fortalezas_ids)
                padecimiento.fortalezas.set(fortalezas)
            
            messages.success(request, f'Padecimiento "{padecimiento.nombre}" creado exitosamente')
            
        except Exception as e:
            messages.error(request, f'Error al crear padecimiento: {str(e)}')
    
    return redirect('jefa:areas_fortalezas')

@login_required
@transaction.atomic
def editar_fortaleza_avanzada(request, fortaleza_id):
    """
    Nueva vista para editar fortalezas con múltiples áreas y padecimientos - CORREGIDA
    """
    fortaleza = get_object_or_404(Fortaleza, id=fortaleza_id)
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion', '')
        areas_ids = request.POST.getlist('areas')
        padecimientos_ids = request.POST.getlist('padecimientos')
        
        try:
            # Validar nombre único (excluyendo la fortaleza actual)
            if Fortaleza.objects.filter(nombre=nombre).exclude(id=fortaleza_id).exists():
                messages.error(request, f'Ya existe otra fortaleza con el nombre "{nombre}"')
                return redirect('jefa:areas_fortalezas')
            
            # Actualizar datos básicos
            fortaleza.nombre = nombre
            fortaleza.descripcion = descripcion
            fortaleza.save()
            
            # CORRECCIÓN: Limpiar y reasignar áreas con validación bidireccional
            
            # 1. Obtener áreas actuales para limpiar relaciones
            areas_actuales = list(fortaleza.areas.all())
            
            # 2. Remover esta fortaleza de todas las áreas que la tenían
            for area_actual in areas_actuales:
                area_actual.fortalezas.remove(fortaleza)
                fortaleza.areas.remove(area_actual)
            
            # 3. Validar y agregar nuevas áreas
            if areas_ids:
                for area_id in areas_ids:
                    area = AreaEspecialidad.objects.get(id=area_id)
                    
                    # Verificar límite de 4 fortalezas por área
                    if area.fortalezas.count() < 4:
                        # Agregar desde ambos lados
                        fortaleza.areas.add(area)
                        area.fortalezas.add(fortaleza)
                    else:
                        messages.warning(request, f'No se pudo agregar a "{area.nombre}" porque ya tiene 4 fortalezas')
            
            # Limpiar relaciones existentes con padecimientos
            padecimientos_actuales = list(fortaleza.padecimientos_asociados.all())
            for padecimiento in padecimientos_actuales:
                padecimiento.fortalezas.remove(fortaleza)
            
            # Establecer nuevas relaciones con padecimientos
            if padecimientos_ids:
                padecimientos_nuevos = Padecimiento.objects.filter(id__in=padecimientos_ids)
                for padecimiento in padecimientos_nuevos:
                    padecimiento.fortalezas.add(fortaleza)
            
            messages.success(request, f'Fortaleza "{fortaleza.nombre}" actualizada exitosamente')
            
        except Exception as e:
            messages.error(request, f'Error al actualizar fortaleza: {str(e)}')
    
    return redirect('jefa:areas_fortalezas')

@login_required
@transaction.atomic
def editar_padecimiento(request, padecimiento_id):
    """
    Nueva vista para editar padecimientos con múltiples áreas y fortalezas
    """
    padecimiento = get_object_or_404(Padecimiento, id=padecimiento_id)
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion', '')
        areas_ids = request.POST.getlist('areas')
        fortalezas_ids = request.POST.getlist('fortalezas')
        
        try:
            # Validar nombre único (excluyendo el padecimiento actual)
            if Padecimiento.objects.filter(nombre=nombre).exclude(id=padecimiento_id).exists():
                messages.error(request, f'Ya existe otro padecimiento con el nombre "{nombre}"')
                return redirect('jefa:areas_fortalezas')
            
            # Actualizar datos básicos
            padecimiento.nombre = nombre
            padecimiento.descripcion = descripcion
            padecimiento.save()
            
            # Actualizar áreas múltiples
            if areas_ids:
                areas = AreaEspecialidad.objects.filter(id__in=areas_ids)
                padecimiento.areas.set(areas)
            else:
                padecimiento.areas.clear()
            
            # Actualizar fortalezas
            if fortalezas_ids:
                fortalezas = Fortaleza.objects.filter(id__in=fortalezas_ids)
                padecimiento.fortalezas.set(fortalezas)
            else:
                padecimiento.fortalezas.clear()
            
            messages.success(request, f'Padecimiento "{padecimiento.nombre}" actualizado exitosamente')
            
        except Exception as e:
            messages.error(request, f'Error al actualizar padecimiento: {str(e)}')
    
    return redirect('jefa:areas_fortalezas')

@login_required
def eliminar_fortaleza(request, fortaleza_id):
    """
    Eliminar fortaleza con validaciones
    """
    if request.method == 'POST':
        try:
            fortaleza = get_object_or_404(Fortaleza, id=fortaleza_id)
            
            # Verificar si está siendo usada por usuarios
            usuarios_con_fortaleza = Usuarios.objects.filter(fortalezas=fortaleza).count()
            if usuarios_con_fortaleza > 0:
                messages.warning(
                    request, 
                    f'No se puede eliminar la fortaleza "{fortaleza.nombre}" '
                    f'porque está asignada a {usuarios_con_fortaleza} usuario(s). '
                    f'Desasigne la fortaleza de los usuarios primero.'
                )
                return redirect('jefa:areas_fortalezas')
            
            # Limpiar relaciones con padecimientos
            padecimientos_relacionados = list(fortaleza.padecimientos_asociados.all())
            for padecimiento in padecimientos_relacionados:
                padecimiento.fortalezas.remove(fortaleza)
            
            # Limpiar relaciones con áreas
            fortaleza.areas.clear()
            
            nombre_fortaleza = fortaleza.nombre
            fortaleza.delete()
            
            messages.success(request, f'Fortaleza "{nombre_fortaleza}" eliminada exitosamente')
            
        except Exception as e:
            messages.error(request, f'Error al eliminar fortaleza: {str(e)}')
    
    return redirect('jefa:areas_fortalezas')

@login_required
def eliminar_padecimiento(request, padecimiento_id):
    """
    Eliminar padecimiento con validaciones (soft delete si está en uso)
    """
    if request.method == 'POST':
        try:
            padecimiento = get_object_or_404(Padecimiento, id=padecimiento_id)
            
            # Verificar si está siendo usado en recetas activas
            from usuarioDoctor.models import RecetaPadecimiento
            recetas_activas = RecetaPadecimiento.objects.filter(
                padecimiento=padecimiento,
                receta__activa=True
            ).count()
            
            if recetas_activas > 0:
                # Soft delete - marcar como inactivo
                padecimiento.activo = False
                padecimiento.save()
                messages.warning(
                    request,
                    f'El padecimiento "{padecimiento.nombre}" se marcó como inactivo '
                    f'porque está siendo usado en {recetas_activas} receta(s) activa(s).'
                )
            else:
                # Hard delete - eliminar completamente
                # Limpiar relaciones con fortalezas
                padecimiento.fortalezas.clear()
                
                # Limpiar relaciones con áreas
                padecimiento.areas.clear()
                
                nombre_padecimiento = padecimiento.nombre
                padecimiento.delete()
                messages.success(request, f'Padecimiento "{nombre_padecimiento}" eliminado exitosamente')
            
        except Exception as e:
            messages.error(request, f'Error al eliminar padecimiento: {str(e)}')
    
    return redirect('jefa:areas_fortalezas')

# =========== APIs PARA CARGAR DATOS EN MODALES ===========

@login_required
def obtener_fortaleza(request, fortaleza_id):
    """
    API para obtener datos de una fortaleza específica para edición
    """
    try:
        fortaleza = get_object_or_404(Fortaleza, id=fortaleza_id)
        
        return JsonResponse({
            'id': fortaleza.id,
            'nombre': fortaleza.nombre,
            'descripcion': fortaleza.descripcion or '',
            'areas': list(fortaleza.areas.values_list('id', flat=True)),
            'padecimientos': list(fortaleza.padecimientos_asociados.values_list('id', flat=True))
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def obtener_padecimiento(request, padecimiento_id):
    """
    API para obtener datos de un padecimiento específico para edición
    """
    try:
        padecimiento = get_object_or_404(Padecimiento, id=padecimiento_id)
        
        return JsonResponse({
            'id': padecimiento.id,
            'nombre': padecimiento.nombre,
            'descripcion': padecimiento.descripcion or '',
            'areas': list(padecimiento.areas.values_list('id', flat=True)),
            'fortalezas': list(padecimiento.fortalezas.values_list('id', flat=True)),
            'activo': padecimiento.activo
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# =========== APIs PARA FILTRADO DINÁMICO ===========

@login_required
def get_padecimientos_por_areas(request):
    """
    API endpoint para obtener padecimientos filtrados por múltiples áreas
    """
    areas_ids = request.GET.getlist('areas_ids')
    
    if areas_ids:
        padecimientos = Padecimiento.objects.filter(
            areas__id__in=areas_ids,
            activo=True
        ).distinct().values('id', 'nombre')
    else:
        padecimientos = Padecimiento.objects.filter(
            activo=True
        ).values('id', 'nombre')
    
    return JsonResponse({
        'padecimientos': list(padecimientos)
    })

@login_required
def get_fortalezas_por_areas(request):
    """
    API endpoint para obtener fortalezas filtradas por múltiples áreas
    """
    areas_ids = request.GET.getlist('areas_ids')
    
    if areas_ids:
        fortalezas = Fortaleza.objects.filter(
            areas__id__in=areas_ids
        ).distinct().values('id', 'nombre')
    else:
        fortalezas = Fortaleza.objects.all().values('id', 'nombre')
    
    return JsonResponse({
        'fortalezas': list(fortalezas)
    })

@login_required
def get_compatibilidad_area(request):
    """
    API endpoint para obtener información de compatibilidad de un área
    """
    area_id = request.GET.get('area_id')
    
    if not area_id:
        return JsonResponse({'error': 'Area ID requerido'}, status=400)
    
    try:
        area = AreaEspecialidad.objects.get(id=area_id)
        
        # Fortalezas disponibles en esta área
        fortalezas = Fortaleza.objects.filter(areas=area).values('id', 'nombre')
        
        # Padecimientos que se manejan en esta área
        padecimientos = Padecimiento.objects.filter(
            areas=area,
            activo=True
        ).values('id', 'nombre')
        
        # Compatibilidades (fortaleza -> padecimiento en la misma área)
        compatibilidades = []
        for fortaleza in Fortaleza.objects.filter(areas=area):
            for padecimiento in fortaleza.padecimientos_asociados.filter(areas=area):
                compatibilidades.append({
                    'fortaleza': fortaleza.nombre,
                    'padecimiento': padecimiento.nombre
                })
        
        return JsonResponse({
            'area': {
                'id': area.id,
                'nombre': area.nombre,
                'descripcion': area.descripcion
            },
            'fortalezas': list(fortalezas),
            'padecimientos': list(padecimientos),
            'compatibilidades': compatibilidades
        })
        
    except AreaEspecialidad.DoesNotExist:
        return JsonResponse({'error': 'Área no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# =========== FUNCIÓN AUXILIAR PARA ALGORITMOS FUTUROS ===========

def calcular_compatibilidad_enfermero_padecimiento(enfermero, padecimiento):
    """
    Función auxiliar que calcula la compatibilidad entre un enfermero y un padecimiento
    basándose en:
    1. Si el área de especialidad del enfermero coincide con las áreas del padecimiento
    2. Si las fortalezas del enfermero coinciden con las fortalezas requeridas del padecimiento
    
    Retorna una puntuación de 0 a 100
    """
    puntuacion = 0
    
    # Verificar coincidencia de área de especialidad (40 puntos máximo)
    if enfermero.areaEspecialidad and enfermero.areaEspecialidad in padecimiento.areas.all():
        puntuacion += 40
    
    # Verificar coincidencias de fortalezas (60 puntos máximo)
    fortalezas_enfermero = set(enfermero.fortalezas.all())
    fortalezas_padecimiento = set(padecimiento.fortalezas.all())
    
    if fortalezas_padecimiento:
        coincidencias = len(fortalezas_enfermero.intersection(fortalezas_padecimiento))
        total_requeridas = len(fortalezas_padecimiento)
        porcentaje_coincidencias = (coincidencias / total_requeridas) * 100
        puntuacion += (porcentaje_coincidencias * 60) / 100
    
    return min(puntuacion, 100)  # Máximo 100 puntos

def obtener_enfermeros_compatibles_por_padecimiento(padecimiento, enfermeros_disponibles=None):
    """
    Obtiene enfermeros ordenados por compatibilidad con un padecimiento específico
    
    Args:
        padecimiento: Instancia del modelo Padecimiento
        enfermeros_disponibles: QuerySet opcional de enfermeros a considerar
    
    Returns:
        Lista de tuplas (enfermero, puntuacion_compatibilidad) ordenada por puntuación descendente
    """
    if enfermeros_disponibles is None:
        enfermeros_disponibles = Usuarios.objects.filter(
            tipoUsuario='EN',
            estaActivo=True
        )
    
    compatibilidades = []
    
    for enfermero in enfermeros_disponibles:
        puntuacion = calcular_compatibilidad_enfermero_padecimiento(enfermero, padecimiento)
        compatibilidades.append((enfermero, puntuacion))
    
    # Ordenar por puntuación descendente
    compatibilidades.sort(key=lambda x: x[1], reverse=True)
    
    return compatibilidades

def obtener_padecimientos_por_area_y_fortalezas(area, fortalezas_enfermero):
    """
    Obtiene padecimientos de un área específica que coincidan con las fortalezas de un enfermero
    
    Args:
        area: Instancia del modelo AreaEspecialidad
        fortalezas_enfermero: QuerySet de fortalezas del enfermero
    
    Returns:
        QuerySet de padecimientos compatibles ordenados por número de coincidencias
    """
    from django.db.models import Count, Q
    
    # Obtener padecimientos del área que requieran las fortalezas del enfermero
    padecimientos_compatibles = Padecimiento.objects.filter(
        areas=area,
        activo=True,
        fortalezas__in=fortalezas_enfermero
    ).annotate(
        coincidencias=Count('fortalezas', filter=Q(fortalezas__in=fortalezas_enfermero))
    ).order_by('-coincidencias')
    
    return padecimientos_compatibles

#//////////////////////////////////////////////////////////////////
#////////////////////////////////////////////////////////////////////
#/777777777777777777777777777777777777777777777777777777777777777777
# =========== FUNCIÓN AUXILIAR PARA ALGORITMOS FUTUROS ===========


# views.py
def calendario_area(request):
    """
    Vista principal del calendario híbrido con vista bimestral y mensual
    """
    areas = AreaEspecialidad.objects.all()
    enfermeros = Usuarios.objects.filter(tipoUsuario='EN', estaActivo=True)
    bimestres = range(1, 7)
    
    # Obtener parámetros de la URL
    area_seleccionada_id = request.GET.get('area')
    vista_tipo = request.GET.get('vista', 'bimestral')
    mes_param = request.GET.get('mes')
    año_param = request.GET.get('año')
    
    # Fechas actuales
    año_actual = int(año_param) if año_param else datetime.now().year
    mes_actual = int(mes_param) if mes_param else datetime.now().month
    
    context = {
        'areas': areas,
        'all_areas': areas,
        'enfermeros': enfermeros,
        'bimestres': bimestres,
        'año_actual': año_actual,
        'mes_actual': mes_actual,
        'vista_tipo': vista_tipo,
    }
    
    # Si hay área seleccionada, obtener datos específicos
    if area_seleccionada_id:
        try:
            area_seleccionada = AreaEspecialidad.objects.get(id=area_seleccionada_id)
            context['area_seleccionada'] = area_seleccionada
            
            # Datos para vista bimestral
            bimestres_data = obtener_datos_bimestres(area_seleccionada, año_actual)
            context['bimestres_data'] = bimestres_data
            
            # Datos para vista mensual
            if vista_tipo == 'mensual':
                datos_mensual = obtener_datos_mensual(area_seleccionada, mes_actual, año_actual)
                context.update(datos_mensual)
            
            # Historial de asignaciones
            historial_asignaciones = AsignacionCalendario.objects.filter(
                area=area_seleccionada
            ).select_related('enfermero').order_by('-fecha_inicio')[:10]
            context['historial_asignaciones'] = historial_asignaciones
            
            # Historial de cambios
            historial = HistorialCambios.objects.filter(
                models.Q(area_anterior=area_seleccionada) | 
                models.Q(area_nueva=area_seleccionada)
            ).select_related(
                'asignacion__enfermero',
                'area_anterior',
                'area_nueva'
            ).order_by('-fecha_cambio')[:10]
            context['historial'] = historial
            
            # Emergencias activas
            emergencias_activas = AsignacionEmergencia.objects.filter(
                models.Q(area_origen=area_seleccionada) | 
                models.Q(area_destino=area_seleccionada),
                activa=True
            ).select_related('enfermero', 'area_origen', 'area_destino', 'creada_por')
            context['emergencias_activas'] = emergencias_activas
            
        except AreaEspecialidad.DoesNotExist:
            messages.error(request, 'Área no encontrada')
    
    return render(request, 'usuarioJefa/calendario.html', context)

def obtener_datos_bimestres(area, año):
    """
    Obtiene datos de asignaciones para todos los bimestres del año con indicadores de emergencia CORREGIDOS
    """
    bimestres_data = []
    
    for bimestre in range(1, 7):
        # Obtener asignaciones normales del bimestre
        asignaciones_normales = AsignacionCalendario.objects.filter(
            area=area,
            bimestre=bimestre,
            year=año,
            activo=True
        ).select_related('enfermero')
        
        # Obtener fechas del bimestre
        mes_inicio = (bimestre - 1) * 2 + 1
        mes_fin = mes_inicio + 1 if mes_inicio < 12 else 12
        
        fecha_inicio = datetime(año, mes_inicio, 1).date()
        if mes_fin == 12:
            fecha_fin = datetime(año, 12, 31).date()
        else:
            ultimo_dia = calendar.monthrange(año, mes_fin)[1]
            fecha_fin = datetime(año, mes_fin, ultimo_dia).date()
        
        # Convertir a timezone-aware para emergencias
        fecha_inicio_tz = timezone.make_aware(datetime.combine(fecha_inicio, datetime.min.time()))
        fecha_fin_tz = timezone.make_aware(datetime.combine(fecha_fin, datetime.max.time()))
        
        # Emergencias que LLEGAN a esta área
        emergencias_llegada = AsignacionEmergencia.objects.filter(
            area_destino=area,
            activa=True,
            fecha_inicio__lte=fecha_fin_tz,
            fecha_fin__gte=fecha_inicio_tz
        ).select_related('enfermero', 'area_origen')
        
        # Emergencias que SALEN de esta área
        emergencias_salida = AsignacionEmergencia.objects.filter(
            area_origen=area,
            activa=True,
            fecha_inicio__lte=fecha_fin_tz,
            fecha_fin__gte=fecha_inicio_tz
        ).select_related('enfermero', 'area_destino')
        
        print(f"DEBUG Bimestre {bimestre}: {asignaciones_normales.count()} normales, "
              f"{emergencias_llegada.count()} llegadas, {emergencias_salida.count()} salidas")
        
        # Combinar asignaciones
        asignaciones_combinadas = []
        
        # Agregar asignaciones normales
        for asignacion in asignaciones_normales:
            # Verificar si este enfermero tiene emergencias de salida en este bimestre
            emergencia_salida = emergencias_salida.filter(
                enfermero=asignacion.enfermero
            ).first()
            
            if emergencia_salida:
                # El enfermero tiene una emergencia que lo saca temporalmente
                # Formatear fechas para mostrar en el tooltip
                fecha_inicio_emergencia = emergencia_salida.fecha_inicio.strftime("%d/%m")
                fecha_fin_emergencia = emergencia_salida.fecha_fin.strftime("%d/%m")
                
                asignaciones_combinadas.append({
                    'enfermero': asignacion.enfermero,
                    'es_emergencia': False,
                    'tipo': 'normal_con_ausencia_temporal',
                    'area_temporal': emergencia_salida.area_destino.nombre,
                    'fecha_inicio_emergencia': fecha_inicio_emergencia,
                    'fecha_fin_emergencia': fecha_fin_emergencia,
                    'motivo': emergencia_salida.motivo,
                    'tooltip': f"Temporalmente en {emergencia_salida.area_destino.nombre} ({fecha_inicio_emergencia} - {fecha_fin_emergencia}): {emergencia_salida.motivo}"
                })
            else:
                # El enfermero está normalmente en esta área
                asignaciones_combinadas.append({
                    'enfermero': asignacion.enfermero,
                    'es_emergencia': False,
                    'tipo': 'normal'
                })
        
        # Agregar emergencias de llegada
        for emergencia in emergencias_llegada:
            fecha_inicio_emergencia = emergencia.fecha_inicio.strftime("%d/%m")
            fecha_fin_emergencia = emergencia.fecha_fin.strftime("%d/%m")
            
            asignaciones_combinadas.append({
                'enfermero': emergencia.enfermero,
                'es_emergencia': True,
                'tipo': 'emergencia_llegada',
                'area_origen': emergencia.area_origen.nombre,
                'motivo': emergencia.motivo,
                'fecha_inicio': fecha_inicio_emergencia,
                'fecha_fin': fecha_fin_emergencia,
                'tooltip': f"Emergencia desde {emergencia.area_origen.nombre} ({fecha_inicio_emergencia} - {fecha_fin_emergencia}): {emergencia.motivo}"
            })
        
        bimestres_data.append({
            'numero': bimestre,
            'mes_inicio': mes_inicio,
            'mes_fin': mes_fin,
            'asignaciones': asignaciones_combinadas
        })
    
    return bimestres_data

def obtener_datos_mensual(area, mes, año):
    """
    Obtiene datos detallados para la vista mensual con indicadores de emergencia CORREGIDOS
    """
    # Generar calendario del mes
    cal = calendar.monthcalendar(año, mes)
    
    # Obtener asignaciones del mes
    primer_dia = datetime(año, mes, 1).date()
    ultimo_dia = datetime(año, mes, calendar.monthrange(año, mes)[1]).date()
    
    print(f"DEBUG: Obteniendo datos para {area.nombre} - {mes}/{año}")
    print(f"DEBUG: Rango de fechas: {primer_dia} a {ultimo_dia}")
    
    # Asignaciones normales activas en el mes
    asignaciones_normales = AsignacionCalendario.objects.filter(
        area=area,
        fecha_inicio__lte=ultimo_dia,
        fecha_fin__gte=primer_dia,
        activo=True
    ).select_related('enfermero')
    
    print(f"DEBUG: Asignaciones normales encontradas: {asignaciones_normales.count()}")
    
    # Convertir fechas a timezone-aware para comparar con emergencias
    primer_dia_tz = timezone.make_aware(datetime.combine(primer_dia, datetime.min.time()))
    ultimo_dia_tz = timezone.make_aware(datetime.combine(ultimo_dia, datetime.max.time()))
    
    # Emergencias que LLEGAN a esta área
    emergencias_llegada = AsignacionEmergencia.objects.filter(
        area_destino=area,
        activa=True,
        fecha_inicio__lte=ultimo_dia_tz,
        fecha_fin__gte=primer_dia_tz
    ).select_related('enfermero', 'area_origen')
    
    # Emergencias que SALEN de esta área
    emergencias_salida = AsignacionEmergencia.objects.filter(
        area_origen=area,
        activa=True,
        fecha_inicio__lte=ultimo_dia_tz,
        fecha_fin__gte=primer_dia_tz
    ).select_related('enfermero', 'area_destino')
    
    print(f"DEBUG: Emergencias de llegada: {emergencias_llegada.count()}")
    print(f"DEBUG: Emergencias de salida: {emergencias_salida.count()}")
    
    # Procesar asignaciones por día
    asignaciones_dia = []
    dias_mes = calendar.monthrange(año, mes)[1]
    
    for dia in range(1, dias_mes + 1):
        fecha_dia = datetime(año, mes, dia).date()
        
        # CORRECCIÓN: Crear rangos de tiempo específicos para el día
        inicio_dia_tz = timezone.make_aware(datetime.combine(fecha_dia, datetime.min.time()))
        fin_dia_tz = timezone.make_aware(datetime.combine(fecha_dia, datetime.max.time()))
        
        print(f"DEBUG: Procesando día {dia} - Rango: {inicio_dia_tz} a {fin_dia_tz}")
        
        # Asignaciones normales para este día
        for asignacion in asignaciones_normales:
            if asignacion.fecha_inicio <= fecha_dia <= asignacion.fecha_fin:
                # CORRECCIÓN: Verificar si hay emergencia que cubra EXACTAMENTE este día
                emergencia_salida = emergencias_salida.filter(
                    enfermero=asignacion.enfermero,
                    fecha_inicio__lte=fin_dia_tz,      # La emergencia debe haber empezado antes del fin del día
                    fecha_fin__gte=inicio_dia_tz       # La emergencia debe terminar después del inicio del día
                ).first()
                
                if emergencia_salida:
                    # Verificación adicional: ¿La emergencia realmente cubre este día específico?
                    emergencia_inicio_date = emergencia_salida.fecha_inicio.date()
                    emergencia_fin_date = emergencia_salida.fecha_fin.date()
                    
                    print(f"DEBUG: Emergencia encontrada para {asignacion.enfermero.username}")
                    print(f"DEBUG: Emergencia del {emergencia_inicio_date} al {emergencia_fin_date}")
                    print(f"DEBUG: Día actual: {fecha_dia}")
                    
                    # VERIFICACIÓN FINAL: Solo mostrar ausencia si la fecha del día está EN el rango de emergencia
                    if emergencia_inicio_date <= fecha_dia <= emergencia_fin_date:
                        print(f"DEBUG: ✅ Día {dia} - {asignacion.enfermero.username} está EN emergencia")
                        asignaciones_dia.append({
                            'aplica_dia': dia,
                            'enfermero': asignacion.enfermero,
                            'es_emergencia': False,
                            'tipo': 'temporal_ausente',
                            'area_temporal': emergencia_salida.area_destino.nombre,
                            'motivo_emergencia': emergencia_salida.motivo,
                            'tooltip': f"Temporalmente en {emergencia_salida.area_destino.nombre}: {emergencia_salida.motivo}"
                        })
                    else:
                        print(f"DEBUG: ❌ Día {dia} - {asignacion.enfermero.username} NO está en emergencia este día")
                        # El enfermero está normalmente en su área este día
                        asignaciones_dia.append({
                            'aplica_dia': dia,
                            'enfermero': asignacion.enfermero,
                            'es_emergencia': False,
                            'tipo': 'normal'
                        })
                else:
                    print(f"DEBUG: ➡️ Día {dia} - {asignacion.enfermero.username} asignación normal")
                    # El enfermero está normalmente en su área este día
                    asignaciones_dia.append({
                        'aplica_dia': dia,
                        'enfermero': asignacion.enfermero,
                        'es_emergencia': False,
                        'tipo': 'normal'
                    })
        
        # Emergencias de LLEGADA para este día específico
        for emergencia in emergencias_llegada:
            emergencia_inicio_date = emergencia.fecha_inicio.date()
            emergencia_fin_date = emergencia.fecha_fin.date()
            
            # VERIFICACIÓN: Solo mostrar llegada si la fecha del día está EN el rango de emergencia
            if emergencia_inicio_date <= fecha_dia <= emergencia_fin_date:
                print(f"DEBUG: ✅ Día {dia} - Llegada de emergencia: {emergencia.enfermero.username}")
                asignaciones_dia.append({
                    'aplica_dia': dia,
                    'enfermero': emergencia.enfermero,
                    'es_emergencia': True,
                    'tipo': 'emergencia_llegada',
                    'area_origen': emergencia.area_origen.nombre,
                    'motivo': emergencia.motivo,
                    'tooltip': f"Emergencia desde {emergencia.area_origen.nombre}: {emergencia.motivo}"
                })
    
    print(f"DEBUG: Total asignaciones por día procesadas: {len(asignaciones_dia)}")
    
    return {
        'calendario': cal,
        'asignaciones_dia': asignaciones_dia,
    }

def limpiar_todas_asignaciones(request):
    """
    Elimina todas las asignaciones y emergencias para pruebas
    """
    if request.method == 'POST':
        try:
            # Contar asignaciones antes de eliminar
            total_asignaciones = AsignacionCalendario.objects.filter(activo=True).count()
            total_emergencias = AsignacionEmergencia.objects.filter(activa=True).count()
            total_historial = HistorialCambios.objects.count()
            
            # Desactivar todas las asignaciones
            AsignacionCalendario.objects.filter(activo=True).update(activo=False)
            
            # Desactivar todas las emergencias
            AsignacionEmergencia.objects.filter(activa=True).update(activa=False)
            
            # Opcionalmente, eliminar el historial de cambios
            HistorialCambios.objects.all().delete()
            
            # También limpiar distribuciones de pacientes si existen
            try:
                from .models import DistribucionPacientes, AsignacionPaciente
                total_distribuciones = DistribucionPacientes.objects.filter(activo=True).count()
                DistribucionPacientes.objects.filter(activo=True).update(activo=False)
                AsignacionPaciente.objects.all().delete()
                
                messages.success(
                    request, 
                    f'Sistema limpiado completamente: '
                    f'{total_asignaciones} asignaciones, '
                    f'{total_emergencias} emergencias, '
                    f'{total_distribuciones} distribuciones y '
                    f'{total_historial} registros de historial desactivados/eliminados.'
                )
            except:
                # Si no existen esos modelos, continuar sin error
                messages.success(
                    request, 
                    f'Sistema limpiado: '
                    f'{total_asignaciones} asignaciones, '
                    f'{total_emergencias} emergencias y '
                    f'{total_historial} registros de historial desactivados/eliminados.'
                )
            
        except Exception as e:
            messages.error(request, f'Error al limpiar el sistema: {str(e)}')
    
    return redirect('jefa:calendario_area')

@transaction.atomic
@transaction.atomic
def crear_emergencia(request):
    """
    Crea una nueva asignación de emergencia (CORREGIDA)
    """
    if request.method == 'POST':
        try:
            enfermero_id = request.POST.get('enfermero')
            area_destino_id = request.POST.get('area_destino')
            fecha_inicio_str = request.POST.get('fecha_inicio')
            fecha_fin_str = request.POST.get('fecha_fin')
            motivo = request.POST.get('motivo')
            
            # Validaciones básicas
            if not all([enfermero_id, area_destino_id, fecha_inicio_str, fecha_fin_str, motivo]):
                messages.error(request, '❌ Error: Todos los campos son obligatorios para crear una emergencia.')
                return redirect('jefa:calendario_area')
            
            if len(motivo.strip()) < 10:
                messages.error(request, '📝 Error: El motivo debe tener al menos 10 caracteres.')
                return redirect('jefa:calendario_area')
            
            # Obtener objetos
            enfermero = get_object_or_404(Usuarios, id=enfermero_id, tipoUsuario='EN')
            area_destino = get_object_or_404(AreaEspecialidad, id=area_destino_id)
            
            if not enfermero.estaActivo:
                messages.error(request, f'👤 El enfermero {enfermero.first_name} {enfermero.apellidos} está inactivo.')
                return redirect('jefa:calendario_area')
            
            # Convertir fechas a timezone-aware
            try:
                fecha_inicio = timezone.make_aware(datetime.fromisoformat(fecha_inicio_str))
                fecha_fin = timezone.make_aware(datetime.fromisoformat(fecha_fin_str))
            except ValueError:
                messages.error(request, '📅 Error: Formato de fecha inválido.')
                return redirect('jefa:calendario_area')
            
            # Validar fechas
            if fecha_fin <= fecha_inicio:
                messages.error(
                    request, 
                    f'📅 Error: La fecha de fin debe ser posterior a la fecha de inicio.'
                )
                return redirect('jefa:calendario_area')
            
            # Obtener área origen - MEJORAR la búsqueda
            area_origen = None
            
            # Buscar asignación activa que cubra la fecha de inicio
            asignacion_origen = AsignacionCalendario.objects.filter(
                enfermero=enfermero,
                fecha_inicio__lte=fecha_inicio.date(),
                fecha_fin__gte=fecha_inicio.date(),
                activo=True
            ).first()
            
            if asignacion_origen:
                area_origen = asignacion_origen.area
                print(f"DEBUG: Área origen encontrada: {area_origen.nombre}")
            else:
                # Si no hay asignación exacta, buscar la más cercana
                asignacion_cercana = AsignacionCalendario.objects.filter(
                    enfermero=enfermero,
                    activo=True
                ).order_by(
                    # Buscar la asignación más cercana a la fecha de inicio
                    models.Case(
                        models.When(fecha_inicio__lte=fecha_inicio.date(), then=models.F('fecha_fin')),
                        default=models.F('fecha_inicio')
                    )
                ).first()
                
                if asignacion_cercana:
                    area_origen = asignacion_cercana.area
                    messages.warning(
                        request,
                        f'⚠️ No hay asignación exacta para la fecha de inicio. '
                        f'Usando área más cercana: {area_origen.nombre}'
                    )
                else:
                    messages.error(
                        request, 
                        f'🔍 No se encontró asignación de origen para {enfermero.first_name} {enfermero.apellidos}. '
                        f'El enfermero debe tener al menos una asignación activa.'
                    )
                    return redirect('jefa:calendario_area')
            
            if area_origen == area_destino:
                messages.error(
                    request, 
                    f'🔄 Error: El enfermero ya está en el área "{area_destino.nombre}".'
                )
                return redirect('jefa:calendario_area')
            
            # Verificar conflictos con otras emergencias
            conflictos = AsignacionEmergencia.objects.filter(
                enfermero=enfermero,
                activa=True,
                fecha_inicio__lt=fecha_fin,
                fecha_fin__gt=fecha_inicio
            )
            
            if conflictos.exists():
                conflicto = conflictos.first()
                messages.error(
                    request, 
                    f'⚠️ Conflicto: Ya existe una emergencia activa para este enfermero '
                    f'({conflicto.fecha_inicio.strftime("%d/%m/%Y %H:%M")} - {conflicto.fecha_fin.strftime("%d/%m/%Y %H:%M")})'
                )
                return redirect('jefa:calendario_area')
            
            # Crear asignación de emergencia
            emergencia = AsignacionEmergencia.objects.create(
                enfermero=enfermero,
                area_origen=area_origen,
                area_destino=area_destino,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                motivo=motivo,
                creada_por=request.user
            )
            
            print(f"DEBUG: Emergencia creada - ID: {emergencia.id}")
            print(f"DEBUG: {enfermero.username}: {area_origen.nombre} → {area_destino.nombre}")
            print(f"DEBUG: Fechas: {fecha_inicio} - {fecha_fin}")
            
            # Calcular duración
            duracion = fecha_fin - fecha_inicio
            duracion_dias = duracion.days
            duracion_horas = duracion.seconds // 3600
            
            duracion_texto = f"{duracion_dias} día{'s' if duracion_dias != 1 else ''}"
            if duracion_horas > 0:
                duracion_texto += f" y {duracion_horas} hora{'s' if duracion_horas != 1 else ''}"
            
            messages.success(
                request, 
                f'🚨 Emergencia creada: {enfermero.first_name} {enfermero.apellidos} '
                f'movido temporalmente de "{area_origen.nombre}" a "{area_destino.nombre}" '
                f'por {duracion_texto}. Motivo: {motivo}'
            )
            
            return redirect(f'{reverse("jefa:calendario_area")}?area={area_destino_id}')
            
        except Exception as e:
            print(f"DEBUG: Error en crear_emergencia: {str(e)}")
            messages.error(request, f'❌ Error al crear emergencia: {str(e)}')
    
    return redirect('jefa:calendario_area')

def finalizar_emergencia(request, emergencia_id):
    """
    Finaliza una asignación de emergencia
    """
    if request.method == 'POST':
        try:
            emergencia = get_object_or_404(
                AsignacionEmergencia, 
                id=emergencia_id, 
                activa=True
            )
            
            emergencia.finalizar()
            
            messages.success(
                request, 
                f'Asignación de emergencia finalizada: {emergencia.enfermero.username}'
            )
            
        except Exception as e:
            messages.error(request, f'Error al finalizar emergencia: {str(e)}')
    
    return redirect('jefa:calendario_area')

def obtener_area_actual_enfermero(enfermero, fecha=None):
    """
    Obtiene el área actual de un enfermero en una fecha específica
    """
    if fecha is None:
        fecha = timezone.now().date()
    
    # Buscar asignación normal activa
    asignacion_actual = AsignacionCalendario.objects.filter(
        enfermero=enfermero,
        fecha_inicio__lte=fecha,
        fecha_fin__gte=fecha,
        activo=True
    ).first()
    
    if asignacion_actual:
        return asignacion_actual.area
    
    return None

def ver_distribucion(request, area_id):
    """
    Muestra la distribución actual de pacientes en un área
    """
    area = get_object_or_404(AreaEspecialidad, id=area_id)
    
    # Obtener distribuciones activas para esta área
    distribuciones_activas = DistribucionPacientes.objects.filter(
        area=area,
        activo=True
    ).select_related('enfermero').order_by('enfermero__username')
    
    # Preparar datos para la plantilla
    distribuciones_data = []
    total_pacientes_area = 0
    
    for distribucion in distribuciones_activas:
        # Obtener pacientes asignados específicamente a esta distribución
        pacientes_asignados = Paciente.objects.filter(
            asignacionpaciente__distribucion=distribucion,
            esta_activo=True
        ).select_related('area')
        
        # Si no hay asignaciones específicas, obtener por enfermero actual
        if not pacientes_asignados.exists():
            pacientes_asignados = Paciente.objects.filter(
                enfermero_actual=distribucion.enfermero,
                area=area,
                esta_activo=True
            )
        
        total_pacientes = distribucion.total_pacientes()
        total_pacientes_area += total_pacientes
        
        # Calcular carga de trabajo
        carga_maxima = 1*3 + 2*2 + 3*1  # 1 grave + 2 medios + 3 leves = 10
        carga_actual = (
            (distribucion.pacientes_gravedad_3 * 3) + 
            (distribucion.pacientes_gravedad_2 * 2) + 
            (distribucion.pacientes_gravedad_1 * 1)
        )
        carga_trabajo = int((carga_actual / carga_maxima) * 100) if carga_maxima > 0 else 0
        
        distribuciones_data.append({
            'distribucion': distribucion,
            'enfermero': distribucion.enfermero,
            'pacientes_asignados': pacientes_asignados,
            'total_pacientes': total_pacientes,
            'carga_trabajo': carga_trabajo,
            'gravedad_1': distribucion.pacientes_gravedad_1,
            'gravedad_2': distribucion.pacientes_gravedad_2,
            'gravedad_3': distribucion.pacientes_gravedad_3,
        })
    
    # Calcular estadísticas del área
    enfermeros_activos = len(distribuciones_activas)
    promedio_pacientes = total_pacientes_area / enfermeros_activos if enfermeros_activos > 0 else 0
    
    context = {
        'area': area,
        'distribuciones_data': distribuciones_data,
        'total_pacientes_area': total_pacientes_area,
        'enfermeros_activos': enfermeros_activos,
        'promedio_pacientes': round(promedio_pacientes, 1),
    }
    
    return render(request, 'usuarioJefa/ver_distribucion.html', context)

def get_datos_mes_ajax(request):
    """
    Endpoint AJAX para obtener datos de un mes específico
    """
    if request.method == 'GET':
        area_id = request.GET.get('area_id')
        mes = int(request.GET.get('mes', datetime.now().month))
        año = int(request.GET.get('año', datetime.now().year))
        
        try:
            area = get_object_or_404(AreaEspecialidad, id=area_id)
            datos = obtener_datos_mensual(area, mes, año)
            
            # Convertir datos para JSON
            calendario_json = []
            for semana in datos['calendario']:
                semana_json = []
                for dia in semana:
                    dia_data = {'numero': dia, 'asignaciones': []}
                    
                    # Agregar asignaciones del día
                    for asig in datos['asignaciones_dia']:
                        if asig['aplica_dia'] == dia:
                            dia_data['asignaciones'].append({
                                'enfermero': asig['enfermero'].username,
                                'es_emergencia': asig['es_emergencia']
                            })
                    
                    semana_json.append(dia_data)
                calendario_json.append(semana_json)
            
            return JsonResponse({
                'success': True,
                'calendario': calendario_json,
                'mes': mes,
                'año': año
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

def get_dias_bimestre(bimestre, año):
    """
    Calcula los días del bimestre considerando año bisiesto
    """
    # Determinar si es año bisiesto
    es_bisiesto = año % 4 == 0 and (año % 100 != 0 or año % 400 == 0)
    
    # Días por mes considerando febrero bisiesto
    dias_por_mes = [31, 29 if es_bisiesto else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    
    # Determinar meses del bimestre
    mes_inicio = ((bimestre - 1) * 2) + 1
    mes_fin = mes_inicio + 1 if mes_inicio < 12 else 12
    
    # Sumar días de los dos meses
    total_dias = dias_por_mes[mes_inicio-1]
    if mes_fin <= 12:
        total_dias += dias_por_mes[mes_fin-1]
    
    return total_dias

@transaction.atomic
def crear_asignacion(request):
    """
    Crea una nueva asignación bimestral con mensajes de error mejorados
    """
    if request.method == 'POST':
        enfermero_id = request.POST.get('enfermero') 
        area_id = request.POST.get('area')
        bimestre = request.POST.get('bimestre')
        año_actual = datetime.now().year

        # Validar que todos los campos estén presentes
        if not all([enfermero_id, area_id, bimestre]):
            messages.error(request, '❌ Error: Todos los campos son obligatorios. Por favor completa la información del enfermero, área y bimestre.')
            return redirect('jefa:calendario_area')

        try:
            # Convertir a enteros
            bimestre = int(bimestre)
            enfermero_id = int(enfermero_id)
            area_id = int(area_id)
        except (ValueError, TypeError):
            messages.error(request, '❌ Error: Los valores ingresados no son válidos. Por favor verifica la información e intenta nuevamente.')
            return redirect('jefa:calendario_area')

        # Validar rango del bimestre
        if not 1 <= bimestre <= 6:
            messages.error(request, f'❌ Error: El bimestre debe estar entre 1 y 6. Valor recibido: {bimestre}')
            return redirect('jefa:calendario_area')

        try:
            # Obtener objetos
            enfermero = get_object_or_404(Usuarios, id=enfermero_id, tipoUsuario='EN')
            area = get_object_or_404(AreaEspecialidad, id=area_id)

            # Calcular fechas del bimestre solicitado
            mes_inicio = ((bimestre - 1) * 2) + 1
            fecha_inicio = datetime(año_actual, mes_inicio, 1)
            
            # Calcular fecha fin del bimestre
            if mes_inicio + 1 <= 12:
                # Bimestre normal (no cruza año)
                ultimo_dia_mes2 = calendar.monthrange(año_actual, mes_inicio + 1)[1]
                fecha_fin = datetime(año_actual, mes_inicio + 1, ultimo_dia_mes2)
            else:
                # Bimestre 6 (noviembre-diciembre)
                fecha_fin = datetime(año_actual, 12, 31)

            print(f"DEBUG: Creando asignación - Enfermero: {enfermero.username}, Área: {area.nombre}, Bimestre: {bimestre}")
            print(f"DEBUG: Fechas - Inicio: {fecha_inicio.date()}, Fin: {fecha_fin.date()}")

            # Validar que no haya otra asignación en el mismo bimestre/año para el enfermero
            conflicto_bimestre = AsignacionCalendario.objects.filter(
                enfermero=enfermero,
                bimestre=bimestre,
                year=año_actual,
                activo=True
            ).first()

            if conflicto_bimestre:
                messages.error(
                    request, 
                    f'⚠️ Conflicto de asignación: El enfermero {enfermero.first_name} {enfermero.apellidos} '
                    f'ya tiene una asignación activa en el bimestre {bimestre} del año {año_actual}. '
                    f'Actualmente está asignado al área "{conflicto_bimestre.area.nombre}" '
                    f'del {conflicto_bimestre.fecha_inicio.strftime("%d/%m/%Y")} al {conflicto_bimestre.fecha_fin.strftime("%d/%m/%Y")}.'
                )
                return redirect(f'{reverse("jefa:calendario_area")}?area={area_id}')

            # Validación inteligente de área no repetida consecutiva
            bimestre_anterior = bimestre - 1
            año_anterior = año_actual
            
            # Si es bimestre 1, verificar bimestre 6 del año anterior
            if bimestre_anterior == 0:
                bimestre_anterior = 6
                año_anterior = año_actual - 1

            asignacion_anterior = AsignacionCalendario.objects.filter(
                enfermero=enfermero,
                bimestre=bimestre_anterior,
                year=año_anterior,
                activo=True
            ).first()

            # Solo validar si hay una asignación anterior y es la misma área
            if asignacion_anterior and asignacion_anterior.area == area:
                # Obtener nombres de meses para hacer el mensaje más claro
                meses = [
                    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
                ]
                
                mes_anterior_inicio = ((bimestre_anterior - 1) * 2) + 1
                mes_anterior_fin = mes_anterior_inicio + 1 if mes_anterior_inicio < 12 else 12
                
                mes_actual_inicio = ((bimestre - 1) * 2) + 1
                mes_actual_fin = mes_actual_inicio + 1 if mes_actual_inicio < 12 else 12
                
                messages.error(
                    request, 
                    f'🚫 Área repetida en bimestres consecutivos: No se puede asignar al enfermero '
                    f'{enfermero.first_name} {enfermero.apellidos} al área "{area.nombre}" '
                    f'en el bimestre {bimestre} ({meses[mes_actual_inicio-1]}-{meses[mes_actual_fin-1]} {año_actual}) '
                    f'porque ya estuvo en la misma área en el bimestre {bimestre_anterior} '
                    f'({meses[mes_anterior_inicio-1]}-{meses[mes_anterior_fin-1]} {año_anterior}). '
                    f'Por favor selecciona un área diferente para cumplir con la política de rotación.'
                )
                return redirect(f'{reverse("jefa:calendario_area")}?area={area_id}')

            # Validar solapamiento de fechas con otras asignaciones activas
            solapamiento = AsignacionCalendario.objects.filter(
                enfermero=enfermero,
                fecha_inicio__lt=fecha_fin.date(),
                fecha_fin__gt=fecha_inicio.date(),
                activo=True
            ).first()

            if solapamiento:
                messages.error(
                    request, 
                    f'📅 Conflicto de fechas: Ya existe una asignación activa para el enfermero '
                    f'{enfermero.first_name} {enfermero.apellidos} que se solapa con el período solicitado. '
                    f'Asignación existente: {solapamiento.area.nombre} '
                    f'del {solapamiento.fecha_inicio.strftime("%d/%m/%Y")} al {solapamiento.fecha_fin.strftime("%d/%m/%Y")}. '
                    f'Período solicitado: del {fecha_inicio.date().strftime("%d/%m/%Y")} al {fecha_fin.date().strftime("%d/%m/%Y")}.'
                )
                return redirect(f'{reverse("jefa:calendario_area")}?area={area_id}')

            # Validación adicional: verificar si el enfermero está activo
            if not enfermero.estaActivo:
                messages.error(
                    request,
                    f'👤 Usuario inactivo: El enfermero {enfermero.first_name} {enfermero.apellidos} '
                    f'está marcado como inactivo en el sistema. No se pueden crear asignaciones '
                    f'para usuarios inactivos. Por favor contacta al administrador si necesitas reactivar este usuario.'
                )
                return redirect(f'{reverse("jefa:calendario_area")}?area={area_id}')

            # Verificar si el área tiene enfermeros suficientes (opcional - puedes comentar esto si no lo necesitas)
            enfermeros_en_area = AsignacionCalendario.objects.filter(
                area=area,
                bimestre=bimestre,
                year=año_actual,
                activo=True
            ).count()
            
            if enfermeros_en_area >= 10:  # Límite ejemplo, ajusta según tus necesidades
                messages.warning(
                    request,
                    f'⚠️ Advertencia: El área "{area.nombre}" ya tiene {enfermeros_en_area} enfermeros asignados '
                    f'en el bimestre {bimestre}. ¿Estás seguro de que deseas agregar otro enfermero? '
                    f'La asignación se creará, pero considera si es necesaria.'
                )

            # CREAR LA ASIGNACIÓN
            asignacion = AsignacionCalendario.objects.create(
                enfermero=enfermero,
                area=area,
                fecha_inicio=fecha_inicio.date(),
                fecha_fin=fecha_fin.date(),
                bimestre=bimestre,
                year=año_actual,
                activo=True
            )

            print(f"DEBUG: Asignación creada exitosamente - ID: {asignacion.id}")

            # Obtener nombres de meses para el mensaje de éxito
            meses = [
                'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
            ]
            
            mes_inicio_nombre = meses[mes_inicio - 1]
            mes_fin_nombre = meses[mes_inicio] if mes_inicio < 12 else meses[11]

            messages.success(
                request, 
                f'✅ Asignación creada exitosamente: '
                f'{enfermero.first_name} {enfermero.apellidos} → {area.nombre} '
                f'(Bimestre {bimestre}: {mes_inicio_nombre}-{mes_fin_nombre} {año_actual})'
            )
            
            # Redirigir con área seleccionada
            return redirect(f'{reverse("jefa:calendario_area")}?area={area_id}')

        except Usuarios.DoesNotExist:
            messages.error(request, f'❌ Error: No se encontró el enfermero seleccionado (ID: {enfermero_id}). Por favor actualiza la página e intenta nuevamente.')
        except AreaEspecialidad.DoesNotExist:
            messages.error(request, f'❌ Error: No se encontró el área seleccionada (ID: {area_id}). Por favor actualiza la página e intenta nuevamente.')
        except Exception as e:
            print(f"DEBUG: Error en crear_asignacion: {str(e)}")
            messages.error(request, f'❌ Error inesperado al crear la asignación: {str(e)}. Por favor intenta nuevamente o contacta al administrador si el problema persiste.')
       
    return redirect('jefa:calendario_area')

@transaction.atomic
@transaction.atomic
def modificar_asignacion(request):
    """
    Modifica una asignación existente creando períodos específicos sin afectar 
    las fechas no modificadas de la asignación original.
    """
    if request.method == 'POST':
        enfermero_id = request.POST.get('enfermero')
        area_nueva_id = request.POST.get('area')
        fecha_inicio_str = request.POST.get('fecha_inicio')
        fecha_fin_str = request.POST.get('fecha_fin')

        # Validar que todos los campos estén presentes
        if not all([enfermero_id, area_nueva_id, fecha_inicio_str, fecha_fin_str]):
            messages.error(request, '❌ Error: Todos los campos son obligatorios para modificar una asignación.')
            return redirect('jefa:calendario_area')

        try:
            enfermero = get_object_or_404(Usuarios, id=enfermero_id, tipoUsuario='EN')
            area_nueva = get_object_or_404(AreaEspecialidad, id=area_nueva_id)
            fecha_inicio_mod = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
            fecha_fin_mod = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()

            # Validar fechas
            if fecha_fin_mod <= fecha_inicio_mod:
                messages.error(
                    request, 
                    f'📅 Error de fechas: La fecha de fin ({fecha_fin_mod.strftime("%d/%m/%Y")}) '
                    f'debe ser posterior a la fecha de inicio ({fecha_inicio_mod.strftime("%d/%m/%Y")}).'
                )
                return redirect('jefa:calendario_area')

            # Buscar asignación original que cubra el período de modificación
            asignacion_original = AsignacionCalendario.objects.filter(
                enfermero=enfermero,
                activo=True,
                fecha_inicio__lte=fecha_inicio_mod,
                fecha_fin__gte=fecha_inicio_mod
            ).first()
            
            if not asignacion_original:
                # Buscar asignaciones activas del enfermero para dar información
                asignaciones_activas = AsignacionCalendario.objects.filter(
                    enfermero=enfermero,
                    activo=True
                ).order_by('fecha_inicio')
                
                if asignaciones_activas.exists():
                    asignaciones_info = []
                    for asig in asignaciones_activas:
                        asignaciones_info.append(
                            f"• {asig.area.nombre}: {asig.fecha_inicio.strftime('%d/%m/%Y')} - {asig.fecha_fin.strftime('%d/%m/%Y')}"
                        )
                    
                    messages.error(
                        request, 
                        f'🔍 No se encontró una asignación activa para el enfermero '
                        f'{enfermero.first_name} {enfermero.apellidos} que cubra la fecha de inicio '
                        f'{fecha_inicio_mod.strftime("%d/%m/%Y")}. '
                        f'Asignaciones activas:\n' + '\n'.join(asignaciones_info)
                    )
                else:
                    messages.error(
                        request,
                        f'🔍 No se encontraron asignaciones activas para el enfermero '
                        f'{enfermero.first_name} {enfermero.apellidos}.'
                    )
                return redirect('jefa:calendario_area')

            # Verificar que la fecha de fin de modificación no exceda la asignación original
            if fecha_fin_mod > asignacion_original.fecha_fin:
                messages.error(
                    request,
                    f'📅 Error: La fecha de fin de la modificación ({fecha_fin_mod.strftime("%d/%m/%Y")}) '
                    f'no puede ser posterior al fin de la asignación original ({asignacion_original.fecha_fin.strftime("%d/%m/%Y")}).'
                )
                return redirect('jefa:calendario_area')

            # Verificar conflictos con otras asignaciones (excluyendo la original)
            conflictos = AsignacionCalendario.objects.filter(
                enfermero=enfermero,
                activo=True,
                fecha_inicio__lt=fecha_fin_mod,
                fecha_fin__gt=fecha_inicio_mod
            ).exclude(id=asignacion_original.id)
            
            if conflictos.exists():
                conflicto = conflictos.first()
                messages.error(
                    request, 
                    f'⚠️ Conflicto de fechas: Las fechas de modificación entran en conflicto '
                    f'con otra asignación: {conflicto.area.nombre} '
                    f'({conflicto.fecha_inicio.strftime("%d/%m/%Y")} - {conflicto.fecha_fin.strftime("%d/%m/%Y")}).'
                )
                return redirect('jefa:calendario_area')

            # Verificar si el cambio es realmente necesario
            if (area_nueva == asignacion_original.area and 
                fecha_inicio_mod == asignacion_original.fecha_inicio and 
                fecha_fin_mod == asignacion_original.fecha_fin):
                messages.info(
                    request,
                    f'ℹ️ Sin cambios: La modificación es idéntica a la asignación existente.'
                )
                return redirect(f'{reverse("jefa:calendario_area")}?area={area_nueva_id}')

            # LÓGICA DE MODIFICACIÓN INTELIGENTE
            
            # Paso 1: Guardar datos originales para el historial
            area_original = asignacion_original.area
            fecha_inicio_original = asignacion_original.fecha_inicio
            fecha_fin_original = asignacion_original.fecha_fin
            bimestre_original = asignacion_original.bimestre
            year_original = asignacion_original.year

            # Paso 2: Calcular qué partes de la asignación original mantener
            
            # ¿Hay período ANTES de la modificación que debemos mantener?
            periodo_anterior = None
            if fecha_inicio_mod > fecha_inicio_original:
                periodo_anterior = {
                    'fecha_inicio': fecha_inicio_original,
                    'fecha_fin': fecha_inicio_mod - timedelta(days=1),
                    'area': area_original
                }

            # ¿Hay período DESPUÉS de la modificación que debemos mantener?
            periodo_posterior = None
            if fecha_fin_mod < fecha_fin_original:
                periodo_posterior = {
                    'fecha_inicio': fecha_fin_mod + timedelta(days=1),
                    'fecha_fin': fecha_fin_original,
                    'area': area_original
                }

            # Paso 3: Desactivar la asignación original
            asignacion_original.activo = False
            asignacion_original.save()

            # Paso 4: Crear las nuevas asignaciones
            
            asignaciones_creadas = []
            
            # Crear período anterior (mantiene área original)
            if periodo_anterior:
                asignacion_anterior = AsignacionCalendario.objects.create(
                    enfermero=enfermero,
                    area=periodo_anterior['area'],
                    fecha_inicio=periodo_anterior['fecha_inicio'],
                    fecha_fin=periodo_anterior['fecha_fin'],
                    bimestre=bimestre_original,
                    year=year_original,
                    activo=True
                )
                asignaciones_creadas.append(f"Período mantenido: {periodo_anterior['area'].nombre} ({periodo_anterior['fecha_inicio'].strftime('%d/%m/%Y')} - {periodo_anterior['fecha_fin'].strftime('%d/%m/%Y')})")

            # Crear período de modificación (nueva área)
            asignacion_modificada = AsignacionCalendario.objects.create(
                enfermero=enfermero,
                area=area_nueva,
                fecha_inicio=fecha_inicio_mod,
                fecha_fin=fecha_fin_mod,
                bimestre=bimestre_original,  # Mantener bimestre original
                year=year_original,
                activo=True
            )
            asignaciones_creadas.append(f"Período modificado: {area_nueva.nombre} ({fecha_inicio_mod.strftime('%d/%m/%Y')} - {fecha_fin_mod.strftime('%d/%m/%Y')})")

            # Crear período posterior (mantiene área original)
            if periodo_posterior:
                asignacion_posterior = AsignacionCalendario.objects.create(
                    enfermero=enfermero,
                    area=periodo_posterior['area'],
                    fecha_inicio=periodo_posterior['fecha_inicio'],
                    fecha_fin=periodo_posterior['fecha_fin'],
                    bimestre=bimestre_original,
                    year=year_original,
                    activo=True
                )
                asignaciones_creadas.append(f"Período mantenido: {periodo_posterior['area'].nombre} ({periodo_posterior['fecha_inicio'].strftime('%d/%m/%Y')} - {periodo_posterior['fecha_fin'].strftime('%d/%m/%Y')})")

            # Paso 5: Registrar el cambio en el historial
            # Usamos la asignación modificada como referencia
            HistorialCambios.objects.create(
                asignacion=asignacion_modificada,
                area_anterior=area_original,
                area_nueva=area_nueva,
                fecha_inicio_anterior=fecha_inicio_original,
                fecha_fin_anterior=fecha_fin_original,
                fecha_inicio_nueva=fecha_inicio_mod,
                fecha_fin_nueva=fecha_fin_mod
            )

            # Paso 6: Mensaje de éxito detallado
            messages.success(
                request, 
                f'✅ Modificación aplicada exitosamente para {enfermero.first_name} {enfermero.apellidos}. '
                f'Se ha dividido la asignación original preservando los períodos no modificados:\n\n'
                f'• Asignación original: {area_original.nombre} ({fecha_inicio_original.strftime("%d/%m/%Y")} - {fecha_fin_original.strftime("%d/%m/%Y")})\n'
                f'• Nuevas asignaciones creadas:\n' + '\n'.join([f'  - {creada}' for creada in asignaciones_creadas])
            )

            # Redirigir mostrando ambas áreas si es necesario
            return redirect(f'{reverse("jefa:calendario_area")}?area={area_nueva_id}')

        except ValueError as e:
            messages.error(request, f'📅 Error de formato en las fechas: {str(e)}')
        except Usuarios.DoesNotExist:
            messages.error(request, f'👤 Error: No se encontró el enfermero seleccionado.')
        except AreaEspecialidad.DoesNotExist:
            messages.error(request, f'🏢 Error: No se encontró el área seleccionada.')
        except Exception as e:
            messages.error(request, f'❌ Error inesperado: {str(e)}')

    return redirect('jefa:calendario_area')
    
def eliminar_asignacion(request, asignacion_id):
    """
    Elimina una asignación (marcarla como inactiva es mejor)
    """
    if request.method == 'POST':
        try:
            asignacion = get_object_or_404(AsignacionCalendario, id=asignacion_id)
            
            # En lugar de eliminar, marcar como inactiva
            asignacion.activo = False
            asignacion.save()
            
            messages.success(request, 'Asignación desactivada correctamente')
            
        except Exception as e:
            messages.error(request, f'Error al desactivar asignación: {str(e)}')
    
    return redirect('jefa:calendario_area')

def obtener_enfermeros_disponibles(request):
    """
    API endpoint para obtener enfermeros disponibles en una fecha/hora específica
    """
    if request.method == 'GET':
        fecha_str = request.GET.get('fecha')
        area_excluir_id = request.GET.get('area_excluir')
        
        try:
            fecha = datetime.fromisoformat(fecha_str) if fecha_str else timezone.now()
            
            # Obtener enfermeros que no estén en emergencia en esa fecha
            enfermeros_ocupados = AsignacionEmergencia.objects.filter(
                activa=True,
                fecha_inicio__lte=fecha,
                fecha_fin__gte=fecha
            ).values_list('enfermero_id', flat=True)
            
            # Filtrar enfermeros disponibles
            enfermeros_disponibles = Usuarios.objects.filter(
                tipoUsuario='EN',
                estaActivo=True
            ).exclude(id__in=enfermeros_ocupados)
            
            # Si se especifica área a excluir, también excluir enfermeros asignados normalmente a esa área
            if area_excluir_id:
                asignados_area = AsignacionCalendario.objects.filter(
                    area_id=area_excluir_id,
                    fecha_inicio__lte=fecha.date(),
                    fecha_fin__gte=fecha.date(),
                    activo=True
                ).values_list('enfermero_id', flat=True)
                
                enfermeros_disponibles = enfermeros_disponibles.exclude(id__in=asignados_area)
            
            # Convertir a JSON
            enfermeros_data = []
            for enfermero in enfermeros_disponibles:
                area_actual = obtener_area_actual_enfermero(enfermero, fecha.date())
                enfermeros_data.append({
                    'id': enfermero.id,
                    'username': enfermero.username,
                    'nombre_completo': f"{enfermero.first_name} {enfermero.apellidos}",
                    'area_actual': area_actual.nombre if area_actual else 'Sin asignar'
                })
            
            return JsonResponse({
                'success': True,
                'enfermeros': enfermeros_data
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

# Función auxiliar para validar permisos
def usuario_puede_gestionar_calendario(user):
    """
    Verifica si un usuario puede gestionar el calendario
    """
    return user.tipoUsuario == 'JP' and user.estaActivo

def requiere_jefa_piso(view_func):
    """
    Decorador que requiere que el usuario sea jefa de piso
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not usuario_puede_gestionar_calendario(request.user):
            messages.error(request, 'No tienes permisos para realizar esta acción')
            return redirect('jefa:menu_jefa')
        return view_func(request, *args, **kwargs)
    return _wrapped_view




def generar_sugerencias_anuales(request, año=None):
    """
    Vista para generar sugerencias automáticas de asignaciones anuales
    CUMPLE: RQF32, RQNF76-89
    """
    if año is None:
        año = datetime.now().year
    
    # Obtener todos los enfermeros activos
    enfermeros = Usuarios.objects.filter(tipoUsuario='EN', estaActivo=True)
    areas = AreaEspecialidad.objects.all()
    
    if request.method == 'POST':
        # SEPARAR: ¿Es para generar o para aplicar?
        if request.POST.get('aplicar_sugerencias') == 'true':
            # APLICAR sugerencias que ya fueron generadas previamente
            try:
                sugerencias_generadas = algoritmo_sugerencias_anuales_requerimientos(enfermeros, areas, año)
                aplicar_sugerencias_automaticas(sugerencias_generadas, año)
                messages.success(request, f'✅ Sugerencias aplicadas para el año {año} siguiendo requerimientos RQNF77-85')
                return redirect('jefa:calendario_area')
            except Exception as e:
                messages.error(request, f'Error al aplicar sugerencias: {str(e)}')
                return redirect('jefa:generar_sugerencias_anuales')
        
        else:
            # GENERAR sugerencias para mostrar (SIN aplicar)
            try:
                print(f"🔍 DEBUG - Generando sugerencias para mostrar (año: {año})")
                sugerencias_generadas = algoritmo_sugerencias_anuales_requerimientos(enfermeros, areas, año)
                
                print(f"🔍 DEBUG - Sugerencias generadas: {len(sugerencias_generadas)} bimestres")
                for bimestre, sugerencias in sugerencias_generadas.items():
                    print(f"  - Bimestre {bimestre}: {len(sugerencias)} sugerencias")
                
                # Si no hay sugerencias nuevas, mostrar mensaje explicativo
                total_nuevas = sum(
                    len([s for s in sugs if not s.get('existente', False)]) 
                    for sugs in sugerencias_generadas.values()
                )
                
                if total_nuevas == 0:
                    messages.info(request, f'ℹ️ Todos los enfermeros ya tienen asignaciones para el año {año}. Las sugerencias mostradas representan el estado actual.')
                else:
                    messages.success(request, f'✅ Se generaron {total_nuevas} nuevas sugerencias para el año {año}. Revisa la distribución antes de aplicar.')
                
                # MOSTRAR sugerencias sin aplicar
                context = {
                    'sugerencias_generadas': sugerencias_generadas,
                    'año': año,
                    'total_enfermeros': len(enfermeros),
                    'total_areas': len(areas),
                    'enfermeros': enfermeros,
                    'areas': areas,
                    'estadisticas': calcular_estadisticas_sugerencias(sugerencias_generadas),
                    'modo': 'mostrar'  # Indicador de que estamos mostrando
                }
                
                return render(request, 'usuarioJefa/sugerencias_anuales.html', context)
                
            except Exception as e:
                print(f"🔍 DEBUG - Error en generar sugerencias: {str(e)}")
                import traceback
                traceback.print_exc()
                messages.error(request, f'Error al generar sugerencias: {str(e)}')
    
    # Para GET request, mostrar interfaz de selección de año
    areas_nivel_bajo = []
    for area in areas:
        try:
            nivel = NivelPrioridadArea.objects.filter(area=area).first()
            if nivel and nivel.nivel_prioridad <= 2:
                areas_nivel_bajo.append(area)
            elif not nivel:
                areas_nivel_bajo.append(area)
        except:
            areas_nivel_bajo.append(area)
    
    context = {
        'año': año,
        'enfermeros': enfermeros,
        'areas': areas,
        'bimestres': range(1, 7),
        'areas_nivel_bajo': areas_nivel_bajo,
        'modo': 'seleccionar'  # Indicador de que estamos en selección
    }
    
    return render(request, 'usuarioJefa/generar_sugerencias_anuales.html', context)

def algoritmo_sugerencias_anuales_requerimientos(enfermeros, areas, año):
    """
    Algoritmo que sigue EXACTAMENTE los requerimientos RQNF77-85
    MODIFICADO para ignorar duplicados y trabajar con datos limpios
    """
    print(f"🔄 Generando sugerencias anuales según requerimientos para {len(enfermeros)} enfermeros")
    
    # Estructura para almacenar sugerencias
    sugerencias_por_bimestre = {}
    historial_asignaciones = {enfermero.id: [] for enfermero in enfermeros}
    
    # CAMBIO: Obtener solo UNA asignación por enfermero/bimestre (la más reciente)
    asignaciones_existentes = []
    for enfermero in enfermeros:
        for bimestre in range(1, 7):
            # Buscar la asignación más reciente para este enfermero/bimestre
            asignacion = AsignacionCalendario.objects.filter(
                enfermero=enfermero,
                bimestre=bimestre,
                year=año,
                activo=True
            ).order_by('-id').first()  # Tomar la más reciente
            
            if asignacion:
                asignaciones_existentes.append(asignacion)
    
    print(f"🔍 Asignaciones existentes encontradas: {len(asignaciones_existentes)}")
    
    # Mapear asignaciones existentes por enfermero (sin duplicados)
    for asignacion in asignaciones_existentes:
        historial_asignaciones[asignacion.enfermero.id].append({
            'bimestre': asignacion.bimestre,
            'area': asignacion.area,
            'existente': True
        })
    
    # RQNF76: 5 rotaciones bimestrales (6 bimestres)
    for bimestre in range(1, 7):
        print(f"📅 Procesando bimestre {bimestre}")
        
        if bimestre == 1:
            # RQNF77: Primera rotación - solo área y actividades de mayor desempeño
            sugerencias_bimestre = generar_primera_rotacion_mejorada(enfermeros, areas, historial_asignaciones)
        else:
            # RQNF85: Rotaciones subsecuentes - mismos parámetros + no repetir área anterior
            sugerencias_bimestre = generar_rotacion_subsecuente_mejorada(
                enfermeros, areas, bimestre, historial_asignaciones
            )
        
        sugerencias_por_bimestre[bimestre] = sugerencias_bimestre
        
        # Actualizar historial para siguiente bimestre
        for sugerencia in sugerencias_bimestre:
            if not sugerencia.get('existente', False):
                historial_asignaciones[sugerencia['enfermero'].id].append({
                    'bimestre': bimestre,
                    'area': sugerencia['area_sugerida'],
                    'existente': False,
                    'es_sugerencia': True
                })
    
    return sugerencias_por_bimestre

def generar_primera_rotacion_mejorada(enfermeros, areas, historial_asignaciones):
    """
    RQNF77: Primera rotación - VERSIÓN MEJORADA que ignora duplicados
    """
    print("  🎯 Generando primera rotación (RQNF77) - Versión mejorada")
    sugerencias = []
    
    for enfermero in enfermeros:
        # Verificar si ya tiene asignación en bimestre 1
        asignacion_existente = None
        for asig in historial_asignaciones[enfermero.id]:
            if asig['bimestre'] == 1 and asig.get('existente', False):
                asignacion_existente = asig
                break
        
        if asignacion_existente:
            # Incluir asignación existente
            sugerencias.append({
                'enfermero': enfermero,
                'area_sugerida': asignacion_existente['area'],
                'motivo': 'Asignación existente (reactivar)',
                'puntuacion': 0,
                'bimestre': 1,
                'existente': True,
                'categoria': 'existente'
            })
        else:
            # Generar nueva sugerencia según parámetros
            if enfermero.areaEspecialidad:
                # PRIORIDAD 1: Área de especialidad
                sugerencias.append({
                    'enfermero': enfermero,
                    'area_sugerida': enfermero.areaEspecialidad,
                    'motivo': f"Área de especialidad: {enfermero.areaEspecialidad.nombre}",
                    'puntuacion': 10,
                    'bimestre': 1,
                    'existente': False,
                    'categoria': 'especialidad'
                })
            elif enfermero.fortalezas.exists():
                # PRIORIDAD 2: Fortalezas
                area_sugerida, coincidencias = encontrar_area_por_fortalezas_segura(enfermero, areas)
                sugerencias.append({
                    'enfermero': enfermero,
                    'area_sugerida': area_sugerida,
                    'motivo': f"Fortalezas coincidentes ({coincidencias}): {area_sugerida.nombre}",
                    'puntuacion': coincidencias,
                    'bimestre': 1,
                    'existente': False,
                    'categoria': 'fortalezas'
                })
            else:
                # PRIORIDAD 3: Asignación aleatoria equitativa
                area_sugerida = asignacion_aleatoria_segura(enfermero, areas)
                sugerencias.append({
                    'enfermero': enfermero,
                    'area_sugerida': area_sugerida,
                    'motivo': 'Asignación aleatoria equitativa (sin parámetros)',
                    'puntuacion': 1,
                    'bimestre': 1,
                    'existente': False,
                    'categoria': 'aleatoria'
                })
    
    return sugerencias

def generar_rotacion_subsecuente_mejorada(enfermeros, areas, bimestre, historial_asignaciones):
    print(f"  🔄 Generando rotación {bimestre} (RQNF85)")
    sugerencias = []
    
    print(f"  🔄 Generando rotación {bimestre} (RQNF85)")
    sugerencias = []
    
    for enfermero in enfermeros:
        # Verificar si ya tiene asignación en este bimestre
        tiene_asignacion = any(
            asig['bimestre'] == bimestre and asig.get('existente', False)
            for asig in historial_asignaciones[enfermero.id]
        )
        
        if tiene_asignacion:
            # Incluir asignación existente - CORREGIR AQUÍ
            asignacion_existente = None
            for asig in historial_asignaciones[enfermero.id]:
                if asig['bimestre'] == bimestre and asig.get('existente', False):
                    asignacion_existente = asig
                    break  # Tomar solo la primera que encuentre
            
            if asignacion_existente:
                sugerencias.append({
                    'enfermero': enfermero,
                    'area_sugerida': asignacion_existente['area'],
                    'motivo': 'Asignación existente',
                    'puntuacion': 0,
                    'bimestre': bimestre,
                    'existente': True,
                    'categoria': 'existente'
                })
            continue
        
        # Obtener áreas de las últimas 2 rotaciones para no repetir
        areas_prohibidas = obtener_areas_ultimas_rotaciones(enfermero.id, bimestre, historial_asignaciones, 2)
        areas_disponibles = [area for area in areas if area not in areas_prohibidas]
        
        if not areas_disponibles:
            # Si no hay áreas disponibles, usar todas (casos extremos)
            areas_disponibles = list(areas)
        
        # Aplicar misma lógica que primera rotación pero con áreas restringidas
        area_sugerida, motivo, puntuacion, categoria = calcular_mejor_area_rotacion_subsecuente(
            enfermero, areas_disponibles, bimestre, areas_prohibidas
        )
        
        sugerencias.append({
            'enfermero': enfermero,
            'area_sugerida': area_sugerida,
            'motivo': motivo,
            'puntuacion': puntuacion,
            'bimestre': bimestre,
            'existente': False,
            'categoria': categoria
        })
    
    return sugerencias

def encontrar_area_por_fortalezas(enfermero, areas):
    """
    Versión segura que no usa .get() y maneja errores
    """
    fortalezas_enfermero = set(enfermero.fortalezas.values_list('id', flat=True))
    
    mejor_area = None
    max_coincidencias = 0
    
    for area in areas:
        fortalezas_area = set(area.fortalezas.values_list('id', flat=True))
        coincidencias = len(fortalezas_enfermero.intersection(fortalezas_area))
        
        if coincidencias > max_coincidencias:
            max_coincidencias = coincidencias
            mejor_area = area
    
    # Si no hay coincidencias, asignar área con menos personal
    if max_coincidencias == 0 or mejor_area is None:
        mejor_area = min(
            areas,
            key=lambda a: AsignacionCalendario.objects.filter(
                area=a, bimestre=1, activo=True
            ).count()
        )
        max_coincidencias = 0
    
    return mejor_area, max_coincidencias

def asignacion_aleatoria_segura(enfermero, areas):
    """
    Asignación segura para enfermeros sin parámetros
    """
    # Filtrar áreas de nivel 1 y 2 de forma segura
    areas_nivel_bajo = []
    for area in areas:
        try:
            nivel = NivelPrioridadArea.objects.filter(area=area).first()
            if nivel and nivel.nivel_prioridad <= 2:
                areas_nivel_bajo.append(area)
            elif not nivel:
                areas_nivel_bajo.append(area)  # Sin nivel = nivel 1
        except:
            areas_nivel_bajo.append(area)  # En caso de error, incluir
    
    if not areas_nivel_bajo:
        areas_nivel_bajo = list(areas)
    
    # Encontrar área con menos enfermeros asignados
    area_menos_cargada = min(
        areas_nivel_bajo,
        key=lambda a: AsignacionCalendario.objects.filter(
            area=a, bimestre=1, activo=True
        ).count()
    )
    
    return area_menos_cargada

def obtener_areas_ultimas_rotaciones(enfermero_id, bimestre_actual, historial, num_rotaciones):
    """
    Obtiene las áreas de las últimas N rotaciones para evitar repetición
    """
    areas_prohibidas = []
    
    for i in range(1, num_rotaciones + 1):
        bimestre_anterior = bimestre_actual - i
        
        # Manejar caso de año anterior (bimestre 1 mira bimestre 6 del año anterior)
        if bimestre_anterior <= 0:
            bimestre_anterior = 6 + bimestre_anterior
            # Para simplificar, solo miramos el año actual en esta implementación
            continue
        
        # Buscar asignación en ese bimestre
        asignacion = next(
            (asig for asig in historial[enfermero_id] if asig['bimestre'] == bimestre_anterior),
            None
        )
        
        if asignacion:
            areas_prohibidas.append(asignacion['area'])
    
    return areas_prohibidas

def calcular_mejor_area_rotacion_subsecuente(enfermero, areas_disponibles, bimestre, areas_prohibidas):
    """
    Calcula la mejor área para rotaciones subsecuentes siguiendo los requerimientos
    """
    # PRIORIDAD 1: Área de especialidad (si está disponible)
    if enfermero.areaEspecialidad and enfermero.areaEspecialidad in areas_disponibles:
        return (
            enfermero.areaEspecialidad, 
            f"Área de especialidad disponible: {enfermero.areaEspecialidad.nombre}",
            10,
            'especialidad'
        )
    
    # PRIORIDAD 2: Área con más fortalezas coincidentes
    if enfermero.fortalezas.exists():
        area_fortalezas, coincidencias = encontrar_area_por_fortalezas(enfermero, areas_disponibles)
        if coincidencias > 0:
            return (
                area_fortalezas,
                f"Fortalezas coincidentes ({coincidencias}) - Evita: {[a.nombre for a in areas_prohibidas]}",
                coincidencias,
                'fortalezas'
            )
    
    # PRIORIDAD 3: Distribución equitativa en áreas disponibles
    area_menos_cargada = min(
        areas_disponibles,
        key=lambda a: AsignacionCalendario.objects.filter(
            area=a, bimestre=bimestre, activo=True
        ).count()
    )
    
    return (
        area_menos_cargada,
        f"Distribución equitativa - Evita: {[a.nombre for a in areas_prohibidas]}",
        1,
        'equitativa'
    )

def calcular_estadisticas_sugerencias(sugerencias_por_bimestre):
    """
    Calcula estadísticas útiles de las sugerencias generadas
    """
    estadisticas = {
        'total_sugerencias': 0,
        'por_categoria': {},
        'cobertura_por_area': {},
        'rotaciones_balanceadas': 0
    }
    
    for bimestre, sugerencias in sugerencias_por_bimestre.items():
        estadisticas['total_sugerencias'] += len([s for s in sugerencias if not s.get('existente', False)])
        
        # Contar por categoría
        for sugerencia in sugerencias:
            categoria = sugerencia.get('categoria', 'desconocida')
            if categoria not in estadisticas['por_categoria']:
                estadisticas['por_categoria'][categoria] = 0
            estadisticas['por_categoria'][categoria] += 1
    
    return estadisticas

def aplicar_sugerencias_automaticas(sugerencias_por_bimestre, año):
    """
    Aplica las sugerencias generadas al sistema real
    IGNORANDO duplicados y reactivando/creando según sea necesario
    """
    with transaction.atomic():
        # PASO 1: Desactivar TODAS las asignaciones del año
        AsignacionCalendario.objects.filter(year=año).update(activo=False)
        print(f"✅ Todas las asignaciones del año {año} desactivadas")
        
        sugerencias_aplicadas = 0
        
        for bimestre, sugerencias in sugerencias_por_bimestre.items():
            for sugerencia in sugerencias:
                # Aplicar TODAS las sugerencias (existentes y nuevas)
                enfermero = sugerencia['enfermero']
                area = sugerencia['area_sugerida']
                
                # Calcular fechas del bimestre
                mes_inicio = ((bimestre - 1) * 2) + 1
                fecha_inicio = datetime(año, mes_inicio, 1)
                
                if mes_inicio + 1 <= 12:
                    ultimo_dia_mes2 = calendar.monthrange(año, mes_inicio + 1)[1]
                    fecha_fin = datetime(año, mes_inicio + 1, ultimo_dia_mes2)
                else:
                    fecha_fin = datetime(año, 12, 31)
                
                # PASO 2: Buscar si existe una asignación similar para reutilizar
                asignacion_existente = AsignacionCalendario.objects.filter(
                    enfermero=enfermero,
                    area=area,
                    bimestre=bimestre,
                    year=año,
                    fecha_inicio=fecha_inicio.date(),
                    fecha_fin=fecha_fin.date()
                ).first()  # Usar .first() para evitar errores de múltiples
                
                if asignacion_existente:
                    # REACTIVAR la asignación existente
                    asignacion_existente.activo = True
                    asignacion_existente.save()
                    print(f"  🔄 Reactivada: {enfermero.username} → {area.nombre} (Bimestre {bimestre})")
                else:
                    # CREAR nueva asignación
                    AsignacionCalendario.objects.create(
                        enfermero=enfermero,
                        area=area,
                        fecha_inicio=fecha_inicio.date(),
                        fecha_fin=fecha_fin.date(),
                        bimestre=bimestre,
                        year=año,
                        activo=True
                    )
                    print(f"  ✨ Creada: {enfermero.username} → {area.nombre} (Bimestre {bimestre})")
                
                sugerencias_aplicadas += 1
        
        print(f"✅ {sugerencias_aplicadas} sugerencias aplicadas automáticamente")
        return sugerencias_aplicadas


#SObrecarga
#Sobrecarga
#Sobrecarha

def calcular_carga_trabajo(area):
    """
    Calcula la carga de trabajo actual en un área específica.
    Retorna un diccionario con métricas relevantes.
    """
    # Obtener total de pacientes por nivel de gravedad
    pacientes_por_gravedad = GravedadPaciente.objects.filter(
        paciente__area=area
    ).values('nivel_gravedad').annotate(
        total=Count('id')
    )
    
    # Obtener enfermeros activos en el área
    enfermeros_activos = AsignacionCalendario.objects.filter(
        area=area,
        activo=True,
        fecha_inicio__lte=timezone.now(),
        fecha_fin__gte=timezone.now()
    ).count()
    
    # Calcular métricas
    total_pacientes = sum(item['total'] for item in pacientes_por_gravedad)
    ratio_pacientes_enfermero = total_pacientes / enfermeros_activos if enfermeros_activos > 0 else float('inf')
    
    return {
        'total_pacientes': total_pacientes,
        'enfermeros_activos': enfermeros_activos,
        'ratio_pacientes_enfermero': ratio_pacientes_enfermero,
        'pacientes_por_gravedad': dict(
            (item['nivel_gravedad'], item['total']) for item in pacientes_por_gravedad
        )
    }

def activar_sobrecarga(request):
    if request.method == 'POST':
        form = ActivarSobrecargaForm(request.POST)
        if form.is_valid():
            area = form.cleaned_data['area']
            
            # Verificar si ya existe una sobrecarga activa para esta área
            sobrecarga_existente = AreaSobrecarga.objects.filter(
                area=area,
                activo=True
            ).first()
            
            if not sobrecarga_existente:
                # Crear nueva sobrecarga
                AreaSobrecarga.objects.create(
                    area=area,
                    fecha_inicio=timezone.now(),
                    activo=True
                )
                messages.success(request, f'Área {area.nombre} marcada en sobrecarga.')
            else:
                messages.error(request, f'El área {area.nombre} ya está en sobrecarga.')
            
            return redirect('jefa:lista_areas_sobrecarga')  # Corregido con namespace
    else:
        form = ActivarSobrecargaForm()
    
    return render(request, 'usuarioJefa/activar_sobrecarga.html', {'form': form})

def desactivar_sobrecarga(request, sobrecarga_id):
    sobrecarga = get_object_or_404(AreaSobrecarga, id=sobrecarga_id, activo=True)
    if request.method == 'POST':
        sobrecarga.activo = False
        sobrecarga.fecha_fin = timezone.now()
        sobrecarga.save()
        messages.success(request, f'Sobrecarga en {sobrecarga.area.nombre} desactivada.')
        return redirect('jefa:lista_areas_sobrecarga')  # Corregido con namespace
    
    return render(request, 'usuarioJefa/confirmar_desactivar_sobrecarga.html', 
                 {'sobrecarga': sobrecarga})

def lista_areas_sobrecarga(request):
    """Vista que muestra todas las áreas y permite gestionar sobrecargas"""
    # Obtener todas las áreas
    areas = AreaEspecialidad.objects.all()
    
    # Obtener áreas actualmente en sobrecarga
    areas_sobrecargadas = AreaSobrecarga.objects.filter(activo=True)
    areas_sobrecargadas_ids = [sobrecarga.area.id for sobrecarga in areas_sobrecargadas]
    
    # Si se envía un form para activar/desactivar
    if request.method == 'POST':
        accion = request.POST.get('accion')
        area_id = request.POST.get('area_id')
        
        if area_id:
            area = get_object_or_404(AreaEspecialidad, id=area_id)
            
            if accion == 'activar' and int(area_id) not in areas_sobrecargadas_ids:
                # Activar sobrecarga
                AreaSobrecarga.objects.create(
                    area=area,
                    fecha_inicio=timezone.now(),
                    activo=True
                )
                messages.success(request, f'Área {area.nombre} marcada en sobrecarga.')
                return redirect('jefa:lista_areas_sobrecarga')
                
            elif accion == 'desactivar' and int(area_id) in areas_sobrecargadas_ids:
                # Desactivar sobrecarga
                sobrecarga = AreaSobrecarga.objects.get(area_id=area_id, activo=True)
                sobrecarga.activo = False
                sobrecarga.fecha_fin = timezone.now()
                sobrecarga.save()
                messages.success(request, f'Sobrecarga en {area.nombre} desactivada.')
                return redirect('jefa:lista_areas_sobrecarga')
    
    # Calcular métricas para todas las áreas
    metricas_areas = {}
    for area in areas:
        metricas_areas[area.id] = calcular_carga_trabajo(area)
    
    # Preparar niveles de prioridad
    niveles_prioridad = {}
    for nivel in NivelPrioridadArea.objects.all():
        niveles_prioridad[nivel.area.id] = nivel.nivel_prioridad
    
    context = {
        'areas': areas,
        'areas_sobrecargadas_ids': areas_sobrecargadas_ids,
        'metricas_areas': metricas_areas,
        'niveles_prioridad': niveles_prioridad,
    }
    
    return render(request, 'usuarioJefa/lista_areas_sobrecarga.html', context)

def asignar_nivel_prioridad(request):
    # Obtener todas las áreas
    areas = AreaEspecialidad.objects.all()
    
    if request.method == 'POST':
        area_id = request.POST.get('area_id')
        nivel_prioridad = request.POST.get('nivel_prioridad')
        
        if area_id and nivel_prioridad:
            area = get_object_or_404(AreaEspecialidad, id=area_id)
            
            # Actualizar o crear el nivel de prioridad
            nivel_obj, created = NivelPrioridadArea.objects.update_or_create(
                area=area,
                defaults={'nivel_prioridad': nivel_prioridad}
            )
            
            if created:
                messages.success(request, f'Nivel de prioridad asignado a {area.nombre}.')
            else:
                messages.success(request, f'Nivel de prioridad actualizado para {area.nombre}.')
                
            return redirect('jefa:asignar_nivel_prioridad')
    
    # Obtener los niveles de prioridad existentes
    niveles_prioridad = {}
    for nivel in NivelPrioridadArea.objects.all():
        niveles_prioridad[nivel.area.id] = nivel.nivel_prioridad
    
    # Preparar contexto
    context = {
        'areas': areas,
        'niveles_prioridad': niveles_prioridad
    }
    
    return render(request, 'usuarioJefa/asignar_nivel_prioridad.html', context)


#Distribucion
#Distribucion
#Distribucion
def distribuir_pacientes(request, area_id):
    """
    Vista para distribuir pacientes en un área específica.
    Permite generar distribuciones equitativas o basadas en gravedad
    y gestionar la asignación de pacientes a enfermeros.
    """
    area = get_object_or_404(AreaEspecialidad, id=area_id)
    
    # Obtener información sobre el área
    area_sobrecarga = AreaSobrecarga.objects.filter(area=area, activo=True).first()
    area_en_sobrecarga = area_sobrecarga is not None
    
    # Obtener nivel de prioridad del área
    try:
        nivel_prioridad = NivelPrioridadArea.objects.get(area=area).nivel_prioridad
    except NivelPrioridadArea.DoesNotExist:
        nivel_prioridad = 1  # Valor por defecto si no tiene prioridad asignada
    
    # Obtener enfermeros activos en el área según el calendario
    fecha_actual = timezone.now().date()
    enfermeros_activos = AsignacionCalendario.objects.filter(
        area=area,
        fecha_inicio__lte=fecha_actual,
        fecha_fin__gte=fecha_actual,
        activo=True
    ).select_related('enfermero')
    
    # Obtener pacientes y sus niveles de gravedad en el área
    pacientes_en_area = GravedadPaciente.objects.filter(
        paciente__area=area, 
        paciente__esta_activo=True
    ).select_related('paciente').order_by('-nivel_gravedad')
    
    # Contar pacientes por nivel de gravedad
    pacientes_gravedad_1 = pacientes_en_area.filter(nivel_gravedad=1).count()
    pacientes_gravedad_2 = pacientes_en_area.filter(nivel_gravedad=2).count()
    pacientes_gravedad_3 = pacientes_en_area.filter(nivel_gravedad=3).count()
    total_pacientes = pacientes_gravedad_1 + pacientes_gravedad_2 + pacientes_gravedad_3
    
    # Calcular porcentajes para la barra visual
    total_ponderado = (pacientes_gravedad_1 * 1) + (pacientes_gravedad_2 * 2) + (pacientes_gravedad_3 * 3)
    if total_ponderado > 0:
        porcentaje_gravedad_1 = (pacientes_gravedad_1 * 1 * 100) / total_ponderado
        porcentaje_gravedad_2 = (pacientes_gravedad_2 * 2 * 100) / total_ponderado
        porcentaje_gravedad_3 = (pacientes_gravedad_3 * 3 * 100) / total_ponderado
    else:
        porcentaje_gravedad_1 = porcentaje_gravedad_2 = porcentaje_gravedad_3 = 0
    
    # Calcular ratio de pacientes por enfermero
    num_enfermeros = enfermeros_activos.count()
    ratio_pacientes_enfermero = total_pacientes / num_enfermeros if num_enfermeros > 0 else 0
    
    # Obtener distribuciones previas para esta área
    distribuciones_previas = DistribucionPacientes.objects.filter(
        area=area
    ).values('id', 'fecha_asignacion', 'descripcion').distinct().order_by('-fecha_asignacion')[:5]
    
    # Procesar el formulario si se envía
    distribucion_actual = None
    distribucion_id = None
    
    if request.method == 'POST' and 'generar_distribucion' in request.POST:
        metodo_distribucion = request.POST.get('metodo_distribucion')
        considerar_desempeno = request.POST.get('considerar_desempeno') == 'si'
        distribucion_previa_id = request.POST.get('distribucion_previa')
        descripcion = request.POST.get('descripcion', 'Distribución generada el ' + timezone.now().strftime('%d/%m/%Y %H:%M'))
        
        # Si se solicita cargar una distribución previa
        if distribucion_previa_id:
            try:
                with transaction.atomic():
                    # Obtener la distribución base que queremos activar
                    distribucion_base = get_object_or_404(DistribucionPacientes, id=distribucion_previa_id)
                    
                    # Desactivar todas las distribuciones activas del área
                    DistribucionPacientes.objects.filter(
                        area=area,
                        activo=True
                    ).update(activo=False)
                    
                    # Activar solamente las distribuciones del mismo grupo (misma fecha y descripción)
                    # Esto activará todas las distribuciones que corresponden a la misma acción
                    # de distribución, una por cada enfermero
                    DistribucionPacientes.objects.filter(
                        area=area,
                        fecha_asignacion=distribucion_base.fecha_asignacion,
                        descripcion=distribucion_base.descripcion
                    ).update(activo=True)
                
                # Ahora cargar la distribución seleccionada para mostrarla
                distribucion_actual = cargar_distribucion_previa(distribucion_previa_id)
                distribucion_id = distribucion_previa_id
                
                if distribucion_actual:
                    messages.success(request, "Se ha cargado la distribución seleccionada correctamente.")
                else:
                    messages.warning(request, "La distribución seleccionada no contiene datos para mostrar.")
            except Exception as e:
                messages.error(request, f"Error al cargar la distribución: {str(e)}")
        else:
            # Generar nueva distribución según el método seleccionado
            if metodo_distribucion == 'equitativa':
                distribucion_actual, distribucion_id = generar_distribucion_equitativa(
                    request, area, enfermeros_activos, pacientes_en_area, considerar_desempeno, descripcion
                )
                messages.success(request, "Se ha generado una distribución equitativa.")
            elif metodo_distribucion == 'gravedad':
                distribucion_actual,  distribucion_id = generar_distribucion_por_gravedad(
                    request, area, enfermeros_activos, pacientes_en_area, considerar_desempeno, descripcion
                )
                messages.success(request, "Se ha generado una distribución priorizando por gravedad.")
            elif metodo_distribucion == 'manual':
                return redirect('jefa:distribucion_manual', area_id=area.id)
    
    # Preparar contexto para la plantilla
    context = {
        'area': area,
        'area_en_sobrecarga': area_en_sobrecarga,
        'nivel_prioridad': nivel_prioridad,
        'total_pacientes': total_pacientes,
        'enfermeros_activos': num_enfermeros,
        'ratio_pacientes_enfermero': ratio_pacientes_enfermero,
        'pacientes_gravedad_1': pacientes_gravedad_1,
        'pacientes_gravedad_2': pacientes_gravedad_2,
        'pacientes_gravedad_3': pacientes_gravedad_3,
        'porcentaje_gravedad_1': porcentaje_gravedad_1,
        'porcentaje_gravedad_2': porcentaje_gravedad_2,
        'porcentaje_gravedad_3': porcentaje_gravedad_3,
        'distribuciones_previas': distribuciones_previas,
        'distribucion_actual': distribucion_actual,
        'distribucion_id': distribucion_id,
    }
    
    return render(request, 'usuarioJefa/distribuir_pacientes.html', context)

def ajustar_distribucion_manual(request, area_id):
    """
    Vista para ajustar manualmente una distribución existente.
    """
    area = get_object_or_404(AreaEspecialidad, id=area_id)
    distribucion_id = request.session.get('distribucion_id')
    
    if not distribucion_id:
        messages.error(request, "No se encontró la distribución a ajustar.")
        return redirect('jefa:distribuir_pacientes', area_id=area_id)
    
    # Obtener distribución base 
    distribucion_base = get_object_or_404(DistribucionPacientes, id=distribucion_id)
    
    # Obtener todas las distribuciones relacionadas
    distribuciones = DistribucionPacientes.objects.filter(
        area=area,
        fecha_asignacion__date=distribucion_base.fecha_asignacion.date()
    ).select_related('enfermero')
    
    # Obtener enfermeros activos en el área
    fecha_actual = timezone.now().date()
    enfermeros_activos = AsignacionCalendario.objects.filter(
        area=area,
        fecha_inicio__lte=fecha_actual,
        fecha_fin__gte=fecha_actual,
        activo=True
    ).select_related('enfermero')
    
    # Crear estructura para la plantilla
    enfermeros_data = []
    
    # Obtener todos los pacientes del área
    pacientes_area = Paciente.objects.filter(area=area, esta_activo=True)
    pacientes_asignados_ids = []
    
    for enfermero_activo in enfermeros_activos:
        enfermero = enfermero_activo.enfermero
        
        # Obtener pacientes asignados actualmente a este enfermero en esta área
        pacientes_asignados = pacientes_area.filter(enfermero_actual=enfermero)
        pacientes_asignados_ids.extend([p.id for p in pacientes_asignados])
        
        # Contar pacientes por nivel de gravedad
        gravedad_1 = 0
        gravedad_2 = 0
        gravedad_3 = 0
        
        pacientes_con_gravedad = []
        for paciente in pacientes_asignados:
            gravedad = GravedadPaciente.objects.filter(paciente=paciente).order_by('-fecha_asignacion').first()
            if gravedad:
                pacientes_con_gravedad.append({
                    'paciente': paciente,
                    'nivel_gravedad': gravedad.nivel_gravedad
                })
                
                if gravedad.nivel_gravedad == 1:
                    gravedad_1 += 1
                elif gravedad.nivel_gravedad == 2:
                    gravedad_2 += 1
                elif gravedad.nivel_gravedad == 3:
                    gravedad_3 += 1
        
        # Calcular carga de trabajo
        carga_maxima = 1*3 + 2*2 + 3*1  # 1 grave + 2 medios + 3 leves = 10
        carga_actual = (gravedad_3 * 3) + (gravedad_2 * 2) + (gravedad_1 * 1)
        carga_trabajo = int((carga_actual / carga_maxima) * 100) if carga_maxima > 0 else 0
        
        enfermeros_data.append({
            'enfermero': enfermero,
            'pacientes_asignados': pacientes_asignados,
            'pacientes_con_gravedad': pacientes_con_gravedad,
            'gravedad_1': gravedad_1,
            'gravedad_2': gravedad_2,
            'gravedad_3': gravedad_3,
            'total_pacientes': len(pacientes_asignados),
            'carga_trabajo': carga_trabajo
        })
    
    # Pacientes no asignados
    pacientes_no_asignados = pacientes_area.exclude(id__in=pacientes_asignados_ids)
    
    # Procesar el formulario de ajuste si es POST
    if request.method == 'POST':
        # Obtener asignación de pacientes a enfermeros del formulario
        for enfermero_activo in enfermeros_activos:
            enfermero = enfermero_activo.enfermero
            
            # Obtener IDs de pacientes asignados a este enfermero
            pacientes_ids = request.POST.getlist(f'pacientes_{enfermero.id}')
            
            if not pacientes_ids:
                continue  # Si no hay pacientes asignados, continuar
            
            # Contar pacientes por gravedad para validar límites
            gravedad_1 = 0
            gravedad_2 = 0
            gravedad_3 = 0
            
            for paciente_id in pacientes_ids:
                gravedad = GravedadPaciente.objects.filter(
                    paciente_id=paciente_id
                ).order_by('-fecha_asignacion').first()
                
                if gravedad:
                    if gravedad.nivel_gravedad == 1:
                        gravedad_1 += 1
                    elif gravedad.nivel_gravedad == 2:
                        gravedad_2 += 1
                    elif gravedad.nivel_gravedad == 3:
                        gravedad_3 += 1
            
            # Validar límites
            if gravedad_1 > 3:
                messages.error(request, f"El enfermero {enfermero.username} no puede atender más de 3 pacientes leves.")
                continue
            
            if gravedad_2 > 2:
                messages.error(request, f"El enfermero {enfermero.username} no puede atender más de 2 pacientes moderados.")
                continue
            
            if gravedad_3 > 1:
                messages.error(request, f"El enfermero {enfermero.username} no puede atender más de 1 paciente grave.")
                continue
            
            # Actualizar distribución existente o crear una nueva
            distribucion = distribuciones.filter(enfermero=enfermero).first()
            
            if not distribucion:
                # Crear nueva distribución
                distribucion = DistribucionPacientes.objects.create(
                    enfermero=enfermero,
                    area=area,
                    descripcion=distribucion_base.descripcion,
                    pacientes_gravedad_1=gravedad_1,
                    pacientes_gravedad_2=gravedad_2,
                    pacientes_gravedad_3=gravedad_3,
                    activo=True
                )
            else:
                # Actualizar distribución existente
                distribucion.pacientes_gravedad_1 = gravedad_1
                distribucion.pacientes_gravedad_2 = gravedad_2
                distribucion.pacientes_gravedad_3 = gravedad_3
                distribucion.save()
            
            # Actualizar la asignación de enfermero para estos pacientes
            for paciente_id in pacientes_ids:
                paciente = get_object_or_404(Paciente, id=paciente_id)
                paciente.enfermero_actual = enfermero
                paciente.save()
        
        messages.success(request, "Distribución ajustada correctamente.")
        return redirect('jefa:ver_distribucion', area_id=area.id)
    
    return render(request, 'usuarioJefa/ajustar_distribucion.html', {
        'area': area,
        'enfermeros_data': enfermeros_data,
        'pacientes_no_asignados': pacientes_no_asignados,
    })

@transaction.atomic
@transaction.atomic
def generar_distribucion_por_gravedad(request, area, enfermeros_activos, pacientes_en_area, considerar_desempeno, descripcion):
    """
    Genera una distribución priorizando la asignación de pacientes graves
    a enfermeros con mejor desempeño en el área.
    """
    # Crear nueva entrada de distribución para cada enfermero
    asignaciones = []
    distribuciones = []
    
    # Preparar lista de enfermeros
    enfermeros = [e.enfermero for e in enfermeros_activos]
    
    # Ordenar enfermeros según su desempeño (siempre para este método)
    enfermeros.sort(key=lambda e: calcular_puntuacion_desempeno(e, area), reverse=True)
    
    # Inicializar estructura para asignaciones
    for enfermero in enfermeros:
        # Crear distribución para este enfermero
        distribucion = DistribucionPacientes(
            enfermero=enfermero,
            area=area,
            descripcion=descripcion,
            pacientes_gravedad_1=0,
            pacientes_gravedad_2=0,
            pacientes_gravedad_3=0,
            activo=True
        )
        distribucion.save()
        distribuciones.append(distribucion)
        
        asignaciones.append({
            'enfermero': enfermero,
            'distribucion': distribucion,
            'pacientes': [],
            'gravedad_1': 0,
            'gravedad_2': 0,
            'gravedad_3': 0,
            'total_pacientes': 0,
            'carga_trabajo': 0
        })
    
    # Obtener listas de pacientes por gravedad
    pacientes_gravedad_3 = list(pacientes_en_area.filter(nivel_gravedad=3).select_related('paciente'))
    pacientes_gravedad_2 = list(pacientes_en_area.filter(nivel_gravedad=2).select_related('paciente'))
    pacientes_gravedad_1 = list(pacientes_en_area.filter(nivel_gravedad=1).select_related('paciente'))
    
    # Distribuir pacientes con gravedad 3 (prioridad a enfermeros con mejor desempeño)
    for i, paciente in enumerate(pacientes_gravedad_3):
        if i < len(asignaciones) and asignaciones[i]['gravedad_3'] < 1:
            asignaciones[i]['pacientes'].append(paciente.paciente)
            asignaciones[i]['gravedad_3'] += 1
            asignaciones[i]['total_pacientes'] += 1
            
            # Actualizar el modelo de distribución
            distribucion = asignaciones[i]['distribucion']
            distribucion.pacientes_gravedad_3 += 1
            distribucion.save()
            
            # Crear asignación de paciente - SIN campo 'activo'
            AsignacionPaciente.objects.create(
                paciente=paciente.paciente,
                distribucion=distribucion
            )
            
            # Actualizar enfermero del paciente
            paciente_obj = paciente.paciente
            paciente_obj.enfermero_actual = asignaciones[i]['enfermero']
            paciente_obj.save()
        else:
            # Buscar un enfermero que pueda tomar este paciente
            asignado = False
            for j in range(len(asignaciones)):
                if asignaciones[j]['gravedad_3'] < 1:
                    asignaciones[j]['pacientes'].append(paciente.paciente)
                    asignaciones[j]['gravedad_3'] += 1
                    asignaciones[j]['total_pacientes'] += 1
                    
                    # Actualizar el modelo de distribución
                    distribucion = asignaciones[j]['distribucion']
                    distribucion.pacientes_gravedad_3 += 1
                    distribucion.save()
                    
                    # Crear asignación de paciente - SIN campo 'activo'
                    AsignacionPaciente.objects.create(
                        paciente=paciente.paciente,
                        distribucion=distribucion
                    )
                    
                    # Actualizar enfermero del paciente
                    paciente_obj = paciente.paciente
                    paciente_obj.enfermero_actual = asignaciones[j]['enfermero']
                    paciente_obj.save()
                    
                    asignado = True
                    break
            
            if not asignado:
                messages.warning(request, f"No se pudo asignar al paciente {paciente.paciente} (gravedad alta).")
    
    # Distribuir pacientes con gravedad 2
    for paciente in pacientes_gravedad_2:
        # Ordenar asignaciones por número de pacientes de gravedad 2
        asignaciones_ordenadas = sorted(asignaciones, key=lambda a: a['gravedad_2'])
        
        asignado = False
        for asignacion in asignaciones_ordenadas:
            if asignacion['gravedad_2'] < 2:
                asignacion['pacientes'].append(paciente.paciente)
                asignacion['gravedad_2'] += 1
                asignacion['total_pacientes'] += 1
                
                # Actualizar el modelo de distribución
                distribucion = asignacion['distribucion']
                distribucion.pacientes_gravedad_2 += 1
                distribucion.save()
                
                # Crear asignación de paciente - SIN campo 'activo'
                AsignacionPaciente.objects.create(
                    paciente=paciente.paciente,
                    distribucion=distribucion
                )
                
                # Actualizar enfermero del paciente
                paciente_obj = paciente.paciente
                paciente_obj.enfermero_actual = asignacion['enfermero']
                paciente_obj.save()
                
                asignado = True
                break
        
        if not asignado:
            messages.warning(request, f"No se pudo asignar al paciente {paciente.paciente} (gravedad media).")
    
    # Distribuir pacientes con gravedad 1
    for paciente in pacientes_gravedad_1:
        # Ordenar asignaciones por número de pacientes de gravedad 1
        asignaciones_ordenadas = sorted(asignaciones, key=lambda a: a['gravedad_1'])
        
        asignado = False
        for asignacion in asignaciones_ordenadas:
            if asignacion['gravedad_1'] < 3:
                asignacion['pacientes'].append(paciente.paciente)
                asignacion['gravedad_1'] += 1
                asignacion['total_pacientes'] += 1
                
                # Actualizar el modelo de distribución
                distribucion = asignacion['distribucion']
                distribucion.pacientes_gravedad_1 += 1
                distribucion.save()
                
                # Crear asignación de paciente - SIN campo 'activo'
                AsignacionPaciente.objects.create(
                    paciente=paciente.paciente,
                    distribucion=distribucion
                )
                
                # Actualizar enfermero del paciente
                paciente_obj = paciente.paciente
                paciente_obj.enfermero_actual = asignacion['enfermero']
                paciente_obj.save()
                
                asignado = True
                break
        
        if not asignado:
            messages.warning(request, f"No se pudo asignar al paciente {paciente.paciente} (gravedad baja).")
    
    # Calcular carga de trabajo para cada enfermero
    for asignacion in asignaciones:
        carga_maxima = 1*3 + 2*2 + 3*1  # 1 grave + 2 medios + 3 leves = 10
        carga_actual = (asignacion['gravedad_3'] * 3) + (asignacion['gravedad_2'] * 2) + (asignacion['gravedad_1'] * 1)
        asignacion['carga_trabajo'] = int((carga_actual / carga_maxima) * 100) if carga_maxima > 0 else 0
    
    # Guardar el ID de esta distribución para referencia
    distribucion_id = distribuciones[0].id if distribuciones else None
    
    return asignaciones, distribucion_id

def calcular_puntuacion_desempeno(enfermero, area):
    """
    Calcula una puntuación de desempeño para un enfermero basada en:
    1. Si el área es su área de especialidad
    2. Coincidencias entre sus fortalezas y las fortalezas del área
    
    Retorna una puntuación numérica donde mayor es mejor.
    """
    puntuacion = 0
    
    # Verificar si el área es de especialidad del enfermero
    if enfermero.areaEspecialidad and enfermero.areaEspecialidad.id == area.id:
        puntuacion += 10  # Dar gran peso a este factor
    
    # Contar coincidencias de fortalezas
    fortalezas_enfermero = enfermero.fortalezas.all()
    fortalezas_area = area.fortalezas.all()
    
    # Convertir a conjuntos para encontrar intersección
    fortalezas_enfermero_ids = set(f.id for f in fortalezas_enfermero)
    fortalezas_area_ids = set(f.id for f in fortalezas_area)
    
    # Contar coincidencias
    coincidencias = len(fortalezas_enfermero_ids.intersection(fortalezas_area_ids))
    puntuacion += coincidencias * 3
    
    # Considerar experiencia en el área (asignaciones previas)
    asignaciones_previas = AsignacionCalendario.objects.filter(
        enfermero=enfermero,
        area=area,
        fecha_fin__lt=timezone.now().date()
    ).count()
    
    puntuacion += min(asignaciones_previas, 5)  # Máximo 5 puntos por experiencia
    
    return puntuacion

def cargar_distribucion_previa(distribucion_previa_id):
    """
    Carga una distribución previa basada en su ID y la retorna en formato compatible con la plantilla.
    """
    try:
        # Obtener la distribución base para determinar el grupo
        distribucion_base = get_object_or_404(DistribucionPacientes, id=distribucion_previa_id)
        
        # Obtener todas las distribuciones del mismo grupo (misma fecha y descripción)
        distribuciones = DistribucionPacientes.objects.filter(
            area=distribucion_base.area,
            fecha_asignacion=distribucion_base.fecha_asignacion,
            descripcion=distribucion_base.descripcion,
            activo=True  # Solo las activas
        ).select_related('enfermero')
        
        # Preparar la estructura de datos para la plantilla
        asignaciones = []
        
        for distribucion in distribuciones:
            # Obtener pacientes asignados a esta distribución
            pacientes_asignados = []
            try:
                # Si existe el modelo AsignacionPaciente
                pacientes_asignados = list(Paciente.objects.filter(
                    asignacionpaciente__distribucion=distribucion,
                    asignacionpaciente__activo=True
                ))
            except:
                # Si no existe el modelo o hay error
                pass
            
            # Preparar información de pacientes
            pacientes_info = []
            
            # Si hay pacientes asignados explícitamente
            for paciente in pacientes_asignados:
                # Obtener gravedad actual
                gravedad = GravedadPaciente.objects.filter(
                    paciente=paciente
                ).order_by('-fecha_asignacion').first()
                
                nivel = gravedad.nivel_gravedad if gravedad else 1
                
                pacientes_info.append({
                    'paciente': paciente,
                    'nivel_gravedad': nivel
                })
            
            # Si no hay pacientes asignados explícitamente, simular basado en conteos
            if not pacientes_info:
                # Crear pacientes simulados basados en los contadores
                for i in range(distribucion.pacientes_gravedad_1):
                    pacientes_info.append({
                        'paciente': {
                            'nombres': f"Paciente Leve #{i+1}",
                            'apellidos': ""
                        },
                        'nivel_gravedad': 1,
                        'es_simulado': True
                    })
                
                for i in range(distribucion.pacientes_gravedad_2):
                    pacientes_info.append({
                        'paciente': {
                            'nombres': f"Paciente Medio #{i+1}",
                            'apellidos': ""
                        },
                        'nivel_gravedad': 2,
                        'es_simulado': True
                    })
                
                for i in range(distribucion.pacientes_gravedad_3):
                    pacientes_info.append({
                        'paciente': {
                            'nombres': f"Paciente Grave #{i+1}",
                            'apellidos': ""
                        },
                        'nivel_gravedad': 3,
                        'es_simulado': True
                    })
            
            # Calcular carga de trabajo
            carga_maxima = 1*3 + 2*2 + 3*1  # 1 grave + 2 medios + 3 leves = 10
            carga_actual = (
                (distribucion.pacientes_gravedad_3 * 3) + 
                (distribucion.pacientes_gravedad_2 * 2) + 
                (distribucion.pacientes_gravedad_1 * 1)
            )
            carga_trabajo = int((carga_actual / carga_maxima) * 100) if carga_maxima > 0 else 0
            
            # Agregar al resultado
            asignaciones.append({
                'enfermero': distribucion.enfermero,
                'distribucion': distribucion,
                'pacientes': pacientes_info,
                'total_pacientes': len(pacientes_info),
                'carga_trabajo': carga_trabajo,
                'gravedad_1': distribucion.pacientes_gravedad_1,
                'gravedad_2': distribucion.pacientes_gravedad_2,
                'gravedad_3': distribucion.pacientes_gravedad_3,
                'descripcion': distribucion.descripcion  # Añadir esto
            })
        
        return asignaciones
    
    except Exception as e:
        print(f"Error cargando distribución: {str(e)}")
        return []

@transaction.atomic
def generar_distribucion_equitativa(request, area, enfermeros_activos, pacientes_en_area, considerar_desempeno, descripcion=None):
    """
    Genera una distribución donde la carga de pacientes se reparte 
    lo más equitativamente posible entre los enfermeros.
    """
    # Crear nueva entrada de distribución para cada enfermero
    asignaciones = []
    distribuciones = []
    
    # Preparar lista de enfermeros
    enfermeros = [e.enfermero for e in enfermeros_activos]
    
    # Ordenar enfermeros según su desempeño si se considera
    if considerar_desempeno:
        enfermeros.sort(key=lambda e: calcular_puntuacion_desempeno(e, area), reverse=True)
    
    # Inicializar estructura para asignaciones
    for enfermero in enfermeros:
        # Crear distribución para este enfermero
        distribucion = DistribucionPacientes(
            enfermero=enfermero,
            area=area,
            descripcion=descripcion,
            pacientes_gravedad_1=0,
            pacientes_gravedad_2=0,
            pacientes_gravedad_3=0,
            activo=True
        )
        distribucion.save()
        distribuciones.append(distribucion)
        
        asignaciones.append({
            'enfermero': enfermero,
            'distribucion': distribucion,
            'pacientes': [],
            'gravedad_1': 0,
            'gravedad_2': 0,
            'gravedad_3': 0,
            'total_pacientes': 0,
            'carga_trabajo': 0
        })
    
    # Obtener todos los pacientes
    todos_pacientes = list(pacientes_en_area.select_related('paciente'))
    
    # Contar total de pacientes por tipo de gravedad
    total_pacientes = len(todos_pacientes)
    total_enfermeros = len(enfermeros)
    
    if total_enfermeros == 0:
        messages.error(request, "No hay enfermeros disponibles para asignar.")
        return [], None
    
    # Calcular cuántos pacientes deberían ir a cada enfermero
    pacientes_por_enfermero = total_pacientes // total_enfermeros
    pacientes_extras = total_pacientes % total_enfermeros
    
    # Distribuir pacientes por gravedad, priorizando graves y medios primero
    pacientes_por_gravedad = {
        3: list(pacientes_en_area.filter(nivel_gravedad=3).select_related('paciente')),
        2: list(pacientes_en_area.filter(nivel_gravedad=2).select_related('paciente')),
        1: list(pacientes_en_area.filter(nivel_gravedad=1).select_related('paciente'))
    }
    
    # Verificar capacidad
    for gravedad, pacientes in pacientes_por_gravedad.items():
        max_por_enfermero = 1 if gravedad == 3 else (2 if gravedad == 2 else 3)
        total_capacidad = max_por_enfermero * total_enfermeros
        if len(pacientes) > total_capacidad:
            messages.warning(
                request, 
                f"Hay más pacientes de gravedad {gravedad} ({len(pacientes)}) que la capacidad total ({total_capacidad})."
            )
    
    # Distribuir pacientes de gravedad 3 primero (máximo 1 por enfermero)
    for i, paciente in enumerate(pacientes_por_gravedad[3]):
        if i < len(asignaciones):
            if asignaciones[i]['gravedad_3'] < 1:
                asignaciones[i]['pacientes'].append(paciente.paciente)
                asignaciones[i]['gravedad_3'] += 1
                asignaciones[i]['total_pacientes'] += 1
                
                # Actualizar el modelo de distribución
                distribucion = asignaciones[i]['distribucion']
                distribucion.pacientes_gravedad_3 += 1
                distribucion.save()
                
                # Crear asignación de paciente - SIN campo 'activo'
                AsignacionPaciente.objects.create(
                    paciente=paciente.paciente,
                    distribucion=distribucion
                )
                
                # Actualizar enfermero del paciente
                paciente_obj = paciente.paciente
                paciente_obj.enfermero_actual = asignaciones[i]['enfermero']
                paciente_obj.save()
            else:
                messages.warning(
                    request, 
                    f"No se pudo asignar al paciente {paciente.paciente} (gravedad alta) porque el enfermero ya tiene un paciente grave."
                )
        else:
            messages.warning(
                request, 
                f"No se pudo asignar al paciente {paciente.paciente} (gravedad alta) porque no hay suficientes enfermeros."
            )
    
    # Distribuir pacientes de gravedad 2 (máximo 2 por enfermero)
    for paciente in pacientes_por_gravedad[2]:
        # Ordenar por número de pacientes de gravedad 2 y total
        asignaciones_ordenadas = sorted(
            asignaciones, 
            key=lambda a: (a['gravedad_2'], a['total_pacientes'])
        )
        
        asignado = False
        for asignacion in asignaciones_ordenadas:
            if asignacion['gravedad_2'] < 2:
                asignacion['pacientes'].append(paciente.paciente)
                asignacion['gravedad_2'] += 1
                asignacion['total_pacientes'] += 1
                
                # Actualizar el modelo de distribución
                distribucion = asignacion['distribucion']
                distribucion.pacientes_gravedad_2 += 1
                distribucion.save()
                
                # Crear asignación de paciente - SIN campo 'activo'
                AsignacionPaciente.objects.create(
                    paciente=paciente.paciente,
                    distribucion=distribucion
                )
                
                # Actualizar enfermero del paciente
                paciente_obj = paciente.paciente
                paciente_obj.enfermero_actual = asignacion['enfermero']
                paciente_obj.save()
                
                asignado = True
                break
        
        if not asignado:
            messages.warning(request, f"No se pudo asignar al paciente {paciente.paciente} (gravedad media).")
    
    # Distribuir pacientes de gravedad 1 (máximo 3 por enfermero)
    for paciente in pacientes_por_gravedad[1]:
        # Ordenar por número total de pacientes para equilibrar carga
        asignaciones_ordenadas = sorted(
            asignaciones, 
            key=lambda a: (a['total_pacientes'], a['gravedad_1'])
        )
        
        asignado = False
        for asignacion in asignaciones_ordenadas:
            if asignacion['gravedad_1'] < 3:
                asignacion['pacientes'].append(paciente.paciente)
                asignacion['gravedad_1'] += 1
                asignacion['total_pacientes'] += 1
                
                # Actualizar el modelo de distribución
                distribucion = asignacion['distribucion']
                distribucion.pacientes_gravedad_1 += 1
                distribucion.save()
                
                # Crear asignación de paciente - SIN campo 'activo'
                AsignacionPaciente.objects.create(
                    paciente=paciente.paciente,
                    distribucion=distribucion
                )
                
                # Actualizar enfermero del paciente
                paciente_obj = paciente.paciente
                paciente_obj.enfermero_actual = asignacion['enfermero']
                paciente_obj.save()
                
                asignado = True
                break
        
        if not asignado:
            messages.warning(request, f"No se pudo asignar al paciente {paciente.paciente} (gravedad baja).")
    
    # Calcular carga de trabajo para cada enfermero
    for asignacion in asignaciones:
        carga_maxima = 1*3 + 2*2 + 3*1  # 1 grave + 2 medios + 3 leves = 10
        carga_actual = (asignacion['gravedad_3'] * 3) + (asignacion['gravedad_2'] * 2) + (asignacion['gravedad_1'] * 1)
        asignacion['carga_trabajo'] = int((carga_actual / carga_maxima) * 100) if carga_maxima > 0 else 0
    
    # Guardar el ID de esta distribución para referencia
    distribucion_id = distribuciones[0].id if distribuciones else None
    
    return asignaciones, distribucion_id

@transaction.atomic
def guardar_distribucion(request, area_id):
    """
    Guarda la distribución actual en la base de datos y actualiza los enfermeros de los pacientes.
    """
    if request.method == 'POST':
        distribucion_id = request.POST.get('distribucion_id')
        
        # Buscar todas las distribuciones relacionadas (una por enfermero)
        distribuciones = DistribucionPacientes.objects.filter(
            id=distribucion_id
        ).first()
        
        if not distribuciones:
            messages.error(request, "No se encontró la distribución para guardar.")
            return redirect('jefa:distribuir_pacientes', area_id=area_id)
        
        # Obtener todas las distribuciones asociadas por área y fecha
        todas_distribuciones = DistribucionPacientes.objects.filter(
            area_id=area_id,
            fecha_asignacion__date=distribuciones.fecha_asignacion.date()
        )
        
        # Marcar todas las distribuciones anteriores como inactivas
        DistribucionPacientes.objects.filter(
            area_id=area_id
        ).exclude(
            id__in=[d.id for d in todas_distribuciones]
        ).update(activo=False)
        
        # Para cada distribución, actualizar el enfermero asignado a los pacientes
        for distribucion in todas_distribuciones:
            # Obtener pacientes asignados a esta distribución
            pacientes_asignados = Paciente.objects.filter(
                asignacionpaciente__distribucion=distribucion
            )
            
            # Actualizar el enfermero de cada paciente
            for paciente in pacientes_asignados:
                paciente.enfermero_actual = distribucion.enfermero
                paciente.save()
            
            # Marcar distribución como activa
            distribucion.activo = True
            distribucion.save()
        
        messages.success(request, "Distribución guardada correctamente y enfermeros asignados a pacientes.")
    
    return redirect('jefa:ver_distribucion', area_id=area_id)

@transaction.atomic
def ajustar_distribucion(request, area_id):
    """
    Redirecciona a una vista para ajustar manualmente la distribución.
    """
    if request.method == 'POST':
        distribucion_id = request.POST.get('distribucion_id')
        
        # Guardar distribucion_id en sesión para recuperarlo en la vista de ajuste
        request.session['distribucion_id'] = distribucion_id
        
        return redirect('jefa:ajustar_distribucion_manual', area_id=area_id)
    
    return redirect('jefa:distribuir_pacientes', area_id=area_id)

@transaction.atomic
def cancelar_distribucion(request, area_id):
    """
    Cancela la distribución actual y regresa a la vista principal.
    """
    if request.method == 'POST':
        distribucion_id = request.POST.get('distribucion_id')
        
        if distribucion_id:
            # Buscar distribución inicial para obtener fecha
            distribucion_base = DistribucionPacientes.objects.filter(id=distribucion_id).first()
            
            if distribucion_base:
                # Eliminar todas las distribuciones asociadas
                DistribucionPacientes.objects.filter(
                    area_id=area_id,
                    fecha_asignacion__date=distribucion_base.fecha_asignacion.date()
                ).delete()
        
        messages.info(request, "Se ha cancelado la distribución.")
    
    return redirect('jefa:lista_areas_sobrecarga')

def distribucion_manual(request, area_id):
    """
    Vista para realizar una distribución manual de pacientes.
    """
    area = get_object_or_404(AreaEspecialidad, id=area_id)
    
    # Obtener enfermeros activos en el área
    fecha_actual = timezone.now().date()
    enfermeros_activos = AsignacionCalendario.objects.filter(
        area=area,
        fecha_inicio__lte=fecha_actual,
        fecha_fin__gte=fecha_actual,
        activo=True
    ).select_related('enfermero')
    
    # Obtener pacientes en el área
    pacientes_en_area = GravedadPaciente.objects.filter(
        paciente__area=area, 
        paciente__esta_activo=True
    ).select_related('paciente').order_by('-nivel_gravedad')
    
    # Procesar el formulario de distribución manual
    if request.method == 'POST':
        descripcion = request.POST.get('descripcion', 'Distribución manual - ' + timezone.now().strftime('%d/%m/%Y %H:%M'))
        
        # Limpiar distribuciones anteriores para esta área
        DistribucionPacientes.objects.filter(area=area, activo=True).update(activo=False)
        
        # Crear distribuciones para cada enfermero
        for enfermero_activo in enfermeros_activos:
            enfermero = enfermero_activo.enfermero
            
            # Obtener pacientes asignados a este enfermero
            pacientes_ids = request.POST.getlist(f'pacientes_{enfermero.id}')
            
            if not pacientes_ids:
                continue  # Si no hay pacientes asignados, continuar con el siguiente enfermero
            
            # Contar pacientes por gravedad
            gravedad_1 = 0
            gravedad_2 = 0
            gravedad_3 = 0
            
            for paciente_id in pacientes_ids:
                gravedad = GravedadPaciente.objects.filter(
                    paciente_id=paciente_id
                ).order_by('-fecha_asignacion').first()
                
                if gravedad:
                    if gravedad.nivel_gravedad == 1:
                        gravedad_1 += 1
                    elif gravedad.nivel_gravedad == 2:
                        gravedad_2 += 1
                    elif gravedad.nivel_gravedad == 3:
                        gravedad_3 += 1
            
            # Validar los límites de pacientes por gravedad
            if gravedad_1 > 3:
                messages.error(request, f"El enfermero {enfermero.username} no puede atender a más de 3 pacientes leves.")
                continue
            
            if gravedad_2 > 2:
                messages.error(request, f"El enfermero {enfermero.username} no puede atender a más de 2 pacientes moderados.")
                continue
            
            if gravedad_3 > 1:
                messages.error(request, f"El enfermero {enfermero.username} no puede atender a más de 1 paciente grave.")
                continue
            
            # Crear distribución
            distribucion = DistribucionPacientes.objects.create(
                enfermero=enfermero,
                area=area,
                descripcion=descripcion,
                pacientes_gravedad_1=gravedad_1,
                pacientes_gravedad_2=gravedad_2,
                pacientes_gravedad_3=gravedad_3,
                activo=True
            )
            
            # Asociar pacientes a la distribución
            for paciente_id in pacientes_ids:
                AsignacionPaciente.objects.create(
                    distribucion=distribucion,
                    paciente_id=paciente_id
                )
                
                # Actualizar enfermero del paciente
                paciente = get_object_or_404(Paciente, id=paciente_id)
                paciente.enfermero_actual = enfermero
                paciente.save()
        
        messages.success(request, "Distribución manual creada correctamente.")
        return redirect('jefa:ver_distribucion', area_id=area.id)
    
    return render(request, 'usuarioJefa/distribucion_manual.html', {
        'area': area,
        'enfermeros': enfermeros_activos,
        'pacientes': pacientes_en_area,
    })

def ajustar_distribucion_manual(request, area_id):
    """
    Vista para ajustar manualmente una distribución existente.
    """
    area = get_object_or_404(AreaEspecialidad, id=area_id)
    distribucion_id = request.session.get('distribucion_id')
    
    if not distribucion_id:
        messages.error(request, "No se encontró la distribución a ajustar.")
        return redirect('jefa:distribuir_pacientes', area_id=area_id)
    
    # Obtener distribución base 
    distribucion_base = get_object_or_404(DistribucionPacientes, id=distribucion_id)
    
    # Obtener todas las distribuciones relacionadas
    distribuciones = DistribucionPacientes.objects.filter(
        area=area,
        fecha_asignacion__date=distribucion_base.fecha_asignacion.date()
    ).select_related('enfermero')
    
    # Obtener enfermeros activos en el área
    fecha_actual = timezone.now().date()
    enfermeros_activos = AsignacionCalendario.objects.filter(
        area=area,
        fecha_inicio__lte=fecha_actual,
        fecha_fin__gte=fecha_actual,
        activo=True
    ).select_related('enfermero')
    
    # Crear estructura para la plantilla
    enfermeros_data = []
    
    # Obtener todos los pacientes del área
    pacientes_area = Paciente.objects.filter(area=area, esta_activo=True)
    pacientes_asignados_ids = []
    
    for enfermero_activo in enfermeros_activos:
        enfermero = enfermero_activo.enfermero
        
        # Obtener pacientes asignados actualmente a este enfermero en esta área
        pacientes_asignados = pacientes_area.filter(enfermero_actual=enfermero)
        pacientes_asignados_ids.extend([p.id for p in pacientes_asignados])
        
        # Contar pacientes por nivel de gravedad
        gravedad_1 = 0
        gravedad_2 = 0
        gravedad_3 = 0
        
        pacientes_con_gravedad = []
        for paciente in pacientes_asignados:
            gravedad = GravedadPaciente.objects.filter(paciente=paciente).order_by('-fecha_asignacion').first()
            if gravedad:
                pacientes_con_gravedad.append({
                    'paciente': paciente,
                    'nivel_gravedad': gravedad.nivel_gravedad
                })
                
                if gravedad.nivel_gravedad == 1:
                    gravedad_1 += 1
                elif gravedad.nivel_gravedad == 2:
                    gravedad_2 += 1
                elif gravedad.nivel_gravedad == 3:
                    gravedad_3 += 1
        
        # Calcular carga de trabajo
        carga_maxima = 1*3 + 2*2 + 3*1  # 1 grave + 2 medios + 3 leves = 10
        carga_actual = (gravedad_3 * 3) + (gravedad_2 * 2) + (gravedad_1 * 1)
        carga_trabajo = int((carga_actual / carga_maxima) * 100) if carga_maxima > 0 else 0
        
        enfermeros_data.append({
            'enfermero': enfermero,
            'pacientes_asignados': pacientes_asignados,
            'pacientes_con_gravedad': pacientes_con_gravedad,
            'gravedad_1': gravedad_1,
            'gravedad_2': gravedad_2,
            'gravedad_3': gravedad_3,
            'total_pacientes': len(pacientes_asignados),
            'carga_trabajo': carga_trabajo
        })
    
    # Pacientes no asignados
    pacientes_no_asignados = pacientes_area.exclude(id__in=pacientes_asignados_ids)
    
    # Procesar el formulario de ajuste si es POST
    if request.method == 'POST':
        # Obtener asignación de pacientes a enfermeros del formulario
        for enfermero_activo in enfermeros_activos:
            enfermero = enfermero_activo.enfermero
            
            # Obtener IDs de pacientes asignados a este enfermero
            pacientes_ids = request.POST.getlist(f'pacientes_{enfermero.id}')
            
            if not pacientes_ids:
                continue  # Si no hay pacientes asignados, continuar
            
            # Contar pacientes por gravedad para validar límites
            gravedad_1 = 0
            gravedad_2 = 0
            gravedad_3 = 0
            
            for paciente_id in pacientes_ids:
                gravedad = GravedadPaciente.objects.filter(
                    paciente_id=paciente_id
                ).order_by('-fecha_asignacion').first()
                
                if gravedad:
                    if gravedad.nivel_gravedad == 1:
                        gravedad_1 += 1
                    elif gravedad.nivel_gravedad == 2:
                        gravedad_2 += 1
                    elif gravedad.nivel_gravedad == 3:
                        gravedad_3 += 1
            
            # Validar límites
            if gravedad_1 > 3:
                messages.error(request, f"El enfermero {enfermero.username} no puede atender más de 3 pacientes leves.")
                continue
            
            if gravedad_2 > 2:
                messages.error(request, f"El enfermero {enfermero.username} no puede atender más de 2 pacientes moderados.")
                continue
            
            if gravedad_3 > 1:
                messages.error(request, f"El enfermero {enfermero.username} no puede atender más de 1 paciente grave.")
                continue
            
            # Actualizar distribución existente o crear una nueva
            distribucion = distribuciones.filter(enfermero=enfermero).first()
            
            if not distribucion:
                # Crear nueva distribución
                distribucion = DistribucionPacientes.objects.create(
                    enfermero=enfermero,
                    area=area,
                    descripcion=distribucion_base.descripcion,
                    pacientes_gravedad_1=gravedad_1,
                    pacientes_gravedad_2=gravedad_2,
                    pacientes_gravedad_3=gravedad_3,
                    activo=True
                )
            else:
                # Actualizar distribución existente
                distribucion.pacientes_gravedad_1 = gravedad_1
                distribucion.pacientes_gravedad_2 = gravedad_2
                distribucion.pacientes_gravedad_3 = gravedad_3
                distribucion.save()
            
            # Actualizar la asignación de enfermero para estos pacientes
            for paciente_id in pacientes_ids:
                paciente = get_object_or_404(Paciente, id=paciente_id)
                paciente.enfermero_actual = enfermero
                paciente.save()
        
        messages.success(request, "Distribución ajustada correctamente.")
        return redirect('jefa:ver_distribucion', area_id=area.id)
    
    return render(request, 'usuarioJefa/ajustar_distribucion.html', {
        'area': area,
        'enfermeros_data': enfermeros_data,
        'pacientes_no_asignados': pacientes_no_asignados,
    })

def ver_distribucion(request, area_id):    
    """
    Vista para visualizar la distribución actual de pacientes en un área.
    """
    area = get_object_or_404(AreaEspecialidad, id=area_id)
    
    # Buscar las distribuciones activas para esta área
    distribuciones = DistribucionPacientes.objects.filter(
        area=area,
        activo=True
    ).select_related('enfermero')
    
    if not distribuciones.exists():
        messages.info(request, "No hay una distribución activa para esta área.")
        return redirect('jefa:distribuir_pacientes', area_id=area_id)
    
    # Obtener información de cada distribución
    enfermeros_data = []
    total_pacientes = 0
    pacientes_gravedad_1 = 0
    pacientes_gravedad_2 = 0
    pacientes_gravedad_3 = 0
    
    for distribucion in distribuciones:
        # Obtener pacientes asignados
        pacientes_asignados = Paciente.objects.filter(
            asignacionpaciente__distribucion=distribucion
        )
        
        # Para cada paciente asignado, obtener su gravedad actual
        pacientes_con_gravedad = []
        for paciente in pacientes_asignados:
            gravedad = GravedadPaciente.objects.filter(paciente=paciente).order_by('-fecha_asignacion').first()
            
            if gravedad:
                pacientes_con_gravedad.append({
                    'paciente': paciente,
                    'nivel_gravedad': gravedad.nivel_gravedad
                })
                
                # Actualizar contadores generales
                if gravedad.nivel_gravedad == 1:
                    pacientes_gravedad_1 += 1
                elif gravedad.nivel_gravedad == 2:
                    pacientes_gravedad_2 += 1
                elif gravedad.nivel_gravedad == 3:
                    pacientes_gravedad_3 += 1
                
                total_pacientes += 1
        
        # Calcular carga de trabajo
        carga_maxima = 1*3 + 2*2 + 3*1  # 1 grave + 2 medios + 3 leves = 10
        carga_actual = (distribucion.pacientes_gravedad_3 * 3) + (distribucion.pacientes_gravedad_2 * 2) + (distribucion.pacientes_gravedad_1 * 1)
        carga_trabajo = int((carga_actual / carga_maxima) * 100) if carga_maxima > 0 else 0
        
        enfermeros_data.append({
            'enfermero': distribucion.enfermero,
            'pacientes': pacientes_con_gravedad,
            'total_pacientes': len(pacientes_asignados),
            'carga_trabajo': carga_trabajo
        })
    
    # Calcular porcentajes para la barra visual
    total_ponderado = (pacientes_gravedad_1 * 1) + (pacientes_gravedad_2 * 2) + (pacientes_gravedad_3 * 3)
    if total_ponderado > 0:
        porcentaje_gravedad_1 = (pacientes_gravedad_1 * 1 * 100) / total_ponderado
        porcentaje_gravedad_2 = (pacientes_gravedad_2 * 2 * 100) / total_ponderado
        porcentaje_gravedad_3 = (pacientes_gravedad_3 * 3 * 100) / total_ponderado
    else:
        porcentaje_gravedad_1 = porcentaje_gravedad_2 = porcentaje_gravedad_3 = 0
    
    # Verificar si el área está en sobrecarga
    area_sobrecarga = AreaSobrecarga.objects.filter(area=area, activo=True).exists()
    
    # Obtener nivel de prioridad
    try:
        nivel_prioridad = NivelPrioridadArea.objects.get(area=area).nivel_prioridad
    except NivelPrioridadArea.DoesNotExist:
        nivel_prioridad = 1
    
    context = {
        'area': area,
        'enfermeros_data': enfermeros_data,
        'total_pacientes': total_pacientes,
        'pacientes_gravedad_1': pacientes_gravedad_1,
        'pacientes_gravedad_2': pacientes_gravedad_2,
        'pacientes_gravedad_3': pacientes_gravedad_3,
        'porcentaje_gravedad_1': porcentaje_gravedad_1,
        'porcentaje_gravedad_2': porcentaje_gravedad_2,
        'porcentaje_gravedad_3': porcentaje_gravedad_3,
        'area_en_sobrecarga': area_sobrecarga,
        'nivel_prioridad': nivel_prioridad,
        'ratio_pacientes_enfermero': total_pacientes / len(enfermeros_data) if enfermeros_data else 0,
        'distribucion_fecha': distribuciones.first().fecha_asignacion if distribuciones.exists() else None,
    }
    
    return render(request, 'usuarioJefa/ver_distribucion.html', context)


#////////////////////////////////////////////////////
# SIMULADOR DE EVENTOS
#///////////////////////////////////////////////////////////

@login_required
def simulador_inicio(request):
    """
    Paso 1: Selección de áreas para la simulación
    """
    if request.user.tipoUsuario != 'JP':
        messages.error(request, 'No tienes permisos para acceder al simulador')
        return redirect('jefa:menu_jefa')
    
    areas_disponibles = AreaEspecialidad.objects.all().order_by('nombre')
    
    if request.method == 'POST':
        nombre_simulacion = request.POST.get('nombre_simulacion', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        areas_seleccionadas = request.POST.getlist('areas_seleccionadas')
        
        # Validaciones
        if not nombre_simulacion:
            messages.error(request, 'El nombre de la simulación es obligatorio')
            return render(request, 'usuarioJefa/simulador_inicio.html', {
                'areas_disponibles': areas_disponibles
            })
        
        if not areas_seleccionadas:
            messages.error(request, 'Debes seleccionar al menos un área')
            return render(request, 'usuarioJefa/simulador_inicio.html', {
                'areas_disponibles': areas_disponibles
            })
        
        try:
            with transaction.atomic():
                # Crear simulación
                simulacion = SimulacionEvento.objects.create(
                    nombre=nombre_simulacion,
                    descripcion=descripcion,
                    creada_por=request.user,
                    total_areas=len(areas_seleccionadas)
                )
                
                # Crear áreas simuladas
                for area_id in areas_seleccionadas:
                    area = get_object_or_404(AreaEspecialidad, id=area_id)
                    AreaSimulada.objects.create(
                        simulacion=simulacion,
                        area_real=area
                    )
                
                messages.success(request, f'Simulación "{nombre_simulacion}" creada. Ahora asigna enfermeros por área.')
                return redirect('jefa:simulador_enfermeros', simulacion_id=simulacion.id)
                
        except Exception as e:
            messages.error(request, f'Error al crear simulación: {str(e)}')
    
    return render(request, 'usuarioJefa/simulador_inicio.html', {
        'areas_disponibles': areas_disponibles
    })

@login_required
def simulador_enfermeros(request, simulacion_id):
    """
    Paso 2: Asignación de enfermeros por área con validación de duplicados
    """
    if request.user.tipoUsuario != 'JP':
        messages.error(request, 'No tienes permisos para acceder al simulador')
        return redirect('jefa:menu_jefa')
    
    simulacion = get_object_or_404(SimulacionEvento, id=simulacion_id, creada_por=request.user)
    areas_simuladas = AreaSimulada.objects.filter(simulacion=simulacion).select_related('area_real')
    enfermeros_disponibles = Usuarios.objects.filter(tipoUsuario='EN', estaActivo=True).order_by('username')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # NUEVO: Validación de enfermeros duplicados
                enfermeros_seleccionados_total = []
                errores_validacion = []
                
                # Recopilar todos los enfermeros seleccionados primero
                for area_simulada in areas_simuladas:
                    enfermeros_key = f'enfermeros_{area_simulada.id}'
                    enfermeros_seleccionados = request.POST.getlist(enfermeros_key)
                    
                    for enfermero_id in enfermeros_seleccionados:
                        if enfermero_id in enfermeros_seleccionados_total:
                            # Encontrar el enfermero duplicado para el mensaje
                            enfermero_duplicado = get_object_or_404(Usuarios, id=enfermero_id)
                            errores_validacion.append(
                                f'❌ El enfermero {enfermero_duplicado.first_name} {enfermero_duplicado.apellidos} '
                                f'está seleccionado en múltiples áreas. Cada enfermero solo puede estar en un área.'
                            )
                        else:
                            enfermeros_seleccionados_total.append(enfermero_id)
                
                # Si hay errores de validación, mostrarlos y no procesar
                if errores_validacion:
                    for error in errores_validacion:
                        messages.error(request, error)
                    
                    # Preparar context con datos para mostrar errores
                    context = {
                        'simulacion': simulacion,
                        'areas_simuladas': areas_simuladas,
                        'enfermeros_disponibles': enfermeros_disponibles,
                        'enfermeros_seleccionados_por_area': obtener_enfermeros_seleccionados_del_post(request, areas_simuladas),
                        'mostrar_errores': True
                    }
                    return render(request, 'usuarioJefa/simulador_enfermeros.html', context)
                
                # VALIDACIÓN ORIGINAL: Limpiar enfermeros simulados existentes
                for area_simulada in areas_simuladas:
                    EnfermeroSimulado.objects.filter(area_simulada=area_simulada).delete()
        
                total_enfermeros = 0
                
                # Procesar cada área sin duplicados
                for area_simulada in areas_simuladas:
                    # Obtener cantidad y enfermeros seleccionados para esta área
                    cantidad_key = f'cantidad_enfermeros_{area_simulada.id}'
                    enfermeros_key = f'enfermeros_{area_simulada.id}'
                    
                    cantidad_enfermeros = int(request.POST.get(cantidad_key, 0))
                    enfermeros_seleccionados = request.POST.getlist(enfermeros_key)
                    
                    # Validar que la cantidad coincida con los seleccionados
                    if cantidad_enfermeros != len(enfermeros_seleccionados):
                        messages.error(request, f'En {area_simulada.area_real.nombre}: selecciona exactamente {cantidad_enfermeros} enfermeros')
                        
                        context = {
                            'simulacion': simulacion,
                            'areas_simuladas': areas_simuladas,
                            'enfermeros_disponibles': enfermeros_disponibles,
                            'enfermeros_seleccionados_por_area': obtener_enfermeros_seleccionados_del_post(request, areas_simuladas)
                        }
                        return render(request, 'usuarioJefa/simulador_enfermeros.html', context)
                    
                    # Actualizar área simulada
                    area_simulada.cantidad_enfermeros = cantidad_enfermeros
                    area_simulada.save()
                    
                    # Crear enfermeros simulados
                    for enfermero_id in enfermeros_seleccionados:
                        enfermero = get_object_or_404(Usuarios, id=enfermero_id, tipoUsuario='EN')
                        EnfermeroSimulado.objects.create(
                            area_simulada=area_simulada,
                            enfermero_real=enfermero
                        )
                    
                    total_enfermeros += cantidad_enfermeros
                
                # Actualizar total en simulación
                simulacion.total_enfermeros = total_enfermeros
                simulacion.save()
                
                messages.success(request, f'✅ {total_enfermeros} enfermeros asignados correctamente sin duplicados. Ahora define la cantidad de pacientes.')
                return redirect('jefa:simulador_pacientes', simulacion_id=simulacion.id)
                
        except Exception as e:
            messages.error(request, f'Error al asignar enfermeros: {str(e)}')
    
    # Para GET request o errores
    context = {
        'simulacion': simulacion,
        'areas_simuladas': areas_simuladas,
        'enfermeros_disponibles': enfermeros_disponibles,
        'enfermeros_seleccionados_por_area': {}  # Vacío para GET request
    }
    
    return render(request, 'usuarioJefa/simulador_enfermeros.html', context)

def obtener_enfermeros_seleccionados_del_post(request, areas_simuladas):
    """
    Función auxiliar para recuperar los enfermeros seleccionados del POST
    para mostrarlos en caso de error
    """
    seleccionados = {}
    for area_simulada in areas_simuladas:
        enfermeros_key = f'enfermeros_{area_simulada.id}'
        cantidad_key = f'cantidad_enfermeros_{area_simulada.id}'
        
        seleccionados[area_simulada.id] = {
            'enfermeros': request.POST.getlist(enfermeros_key),
            'cantidad': request.POST.get(cantidad_key, 0)
        }
    
    return seleccionados

@login_required
def simulador_pacientes(request, simulacion_id):
    """
    Paso 3: Definir cantidad de pacientes por área y generar pacientes simulados
    """
    if request.user.tipoUsuario != 'JP':
        messages.error(request, 'No tienes permisos para acceder al simulador')
        return redirect('jefa:menu_jefa')
    
    simulacion = get_object_or_404(SimulacionEvento, id=simulacion_id, creada_por=request.user)
    areas_simuladas = AreaSimulada.objects.filter(simulacion=simulacion).select_related('area_real')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                total_pacientes = 0
                
                for area_simulada in areas_simuladas:
                    cantidad_key = f'cantidad_pacientes_{area_simulada.id}'
                    cantidad_pacientes = int(request.POST.get(cantidad_key, 0))
                    
                    if cantidad_pacientes < 0:
                        messages.error(request, f'La cantidad de pacientes no puede ser negativa en {area_simulada.area_real.nombre}')
                        return render(request, 'usuarioJefa/simulador_pacientes.html', {
                            'simulacion': simulacion,
                            'areas_simuladas': areas_simuladas
                        })
                    
                    # Actualizar área simulada
                    area_simulada.cantidad_pacientes = cantidad_pacientes
                    area_simulada.ratio_pacientes_enfermero = (
                        cantidad_pacientes / area_simulada.cantidad_enfermeros 
                        if area_simulada.cantidad_enfermeros > 0 else 0
                    )
                    area_simulada.save()
                    
                    # Generar pacientes simulados
                    for i in range(1, cantidad_pacientes + 1):
                        PacienteSimulado.objects.create(
                            area_simulada=area_simulada,
                            nombre_simulado=f"Paciente {i}"
                        )
                    
                    total_pacientes += cantidad_pacientes
                
                # Actualizar total en simulación
                simulacion.total_pacientes = total_pacientes
                simulacion.save()
                
                if total_pacientes > 0:
                    messages.success(request, f'{total_pacientes} pacientes generados. Ahora asigna padecimientos.')
                    return redirect('jefa:simulador_padecimientos', simulacion_id=simulacion.id)
                else:
                    messages.warning(request, 'Simulación creada sin pacientes. Puedes ver los resultados.')
                    return redirect('jefa:simulador_resultados', simulacion_id=simulacion.id)
                
        except Exception as e:
            messages.error(request, f'Error al generar pacientes: {str(e)}')
    
    return render(request, 'usuarioJefa/simulador_pacientes.html', {
        'simulacion': simulacion,
        'areas_simuladas': areas_simuladas
    })

@login_required
def simulador_padecimientos(request, simulacion_id):
    """
    Paso 4: Asignar padecimientos a pacientes simulados
    """
    if request.user.tipoUsuario != 'JP':
        messages.error(request, 'No tienes permisos para acceder al simulador')
        return redirect('jefa:menu_jefa')
    
    simulacion = get_object_or_404(SimulacionEvento, id=simulacion_id, creada_por=request.user)
    
    # Obtener pacientes agrupados por área
    areas_con_pacientes = []
    for area_simulada in AreaSimulada.objects.filter(simulacion=simulacion).select_related('area_real'):
        pacientes = PacienteSimulado.objects.filter(area_simulada=area_simulada)
        if pacientes.exists():
            areas_con_pacientes.append({
                'area': area_simulada,
                'pacientes': pacientes
            })
    
    padecimientos_disponibles = Padecimiento.objects.filter(activo=True).order_by('nombre')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Procesar padecimientos para cada paciente
                for area_info in areas_con_pacientes:
                    for paciente in area_info['pacientes']:
                        # Obtener padecimientos seleccionados para este paciente
                        padecimientos_key = f'padecimientos_{paciente.id}'
                        gravedad_key = f'gravedad_{paciente.id}'
                        
                        padecimientos_ids = request.POST.getlist(padecimientos_key)
                        nivel_gravedad = int(request.POST.get(gravedad_key, 1))
                        
                        # Actualizar nivel de gravedad
                        paciente.nivel_gravedad = nivel_gravedad
                        paciente.save()
                        
                        # Crear padecimientos simulados
                        for padecimiento_id in padecimientos_ids:
                            padecimiento = get_object_or_404(Padecimiento, id=padecimiento_id)
                            PadecimientoSimulado.objects.create(
                                paciente_simulado=paciente,
                                padecimiento=padecimiento
                            )
                
                messages.success(request, 'Padecimientos asignados correctamente. Generando resultados...')
                return redirect('jefa:simulador_resultados', simulacion_id=simulacion.id)
                
        except Exception as e:
            messages.error(request, f'Error al asignar padecimientos: {str(e)}')
    
    return render(request, 'usuarioJefa/simulador_padecimientos.html', {
        'simulacion': simulacion,
        'areas_con_pacientes': areas_con_pacientes,
        'padecimientos_disponibles': padecimientos_disponibles
    })

@login_required
def simulador_resultados(request, simulacion_id):
    """
    Paso 5: Mostrar resultados de la simulación en tablas con distribución automática
    MEJORADO con compatibilidades para el template
    """
    if request.user.tipoUsuario != 'JP':
        messages.error(request, 'No tienes permisos para acceder al simulador')
        return redirect('jefa:menu_jefa')
    
    simulacion = get_object_or_404(SimulacionEvento, id=simulacion_id, creada_por=request.user)
    
    # Obtener datos de la simulación
    areas_simuladas = AreaSimulada.objects.filter(simulacion=simulacion).select_related('area_real')
    
    # Distribuir pacientes automáticamente antes de mostrar resultados
    distribuir_pacientes_automaticamente(simulacion)
    
    # NUEVO: Calcular compatibilidades
    compatibilidades = calcular_compatibilidades_simulador(simulacion)
    
    # Preparar datos para las tablas
    resumen_areas = []
    detalle_enfermeros = []
    detalle_pacientes = []
    
    total_carga = 0
    areas_con_datos = 0
    
    for area_simulada in areas_simuladas:
        # Enfermeros del área
        enfermeros = EnfermeroSimulado.objects.filter(area_simulada=area_simulada).select_related('enfermero_real')
        
        # Pacientes del área
        pacientes = PacienteSimulado.objects.filter(area_simulada=area_simulada).prefetch_related('padecimientos__padecimiento')
        
        # Calcular métricas del área
        if area_simulada.cantidad_enfermeros > 0:
            carga_area = (area_simulada.cantidad_pacientes / area_simulada.cantidad_enfermeros) * 10
            total_carga += carga_area
            areas_con_datos += 1
        else:
            carga_area = 0
        
        area_simulada.carga_trabajo_area = carga_area
        area_simulada.save()
        
        # Agregar al resumen
        resumen_areas.append({
            'area': area_simulada,
            'enfermeros_count': enfermeros.count(),
            'pacientes_count': pacientes.count(),
            'carga_trabajo': carga_area
        })
        
        # Agregar enfermeros al detalle con pacientes asignados
        for enfermero in enfermeros:
            # Contar pacientes asignados a este enfermero
            pacientes_asignados = PacienteSimulado.objects.filter(enfermero_asignado=enfermero).count()
            
            # Calcular carga individual
            carga_individual = (pacientes_asignados / 6) * 100 if pacientes_asignados > 0 else 0
            
            # Actualizar enfermero simulado
            enfermero.pacientes_asignados = pacientes_asignados
            enfermero.carga_trabajo_individual = carga_individual
            enfermero.save()
            
            detalle_enfermeros.append(enfermero)
        
        # MODIFICADO: Agregar pacientes al detalle con información de compatibilidad
        for paciente in pacientes:
            # Obtener compatibilidad específica para este paciente
            compatibilidad_paciente = None
            if area_simulada.area_real.nombre in compatibilidades:
                for comp in compatibilidades[area_simulada.area_real.nombre]:
                    if comp['paciente'].id == paciente.id:
                        compatibilidad_paciente = comp
                        break
            
            detalle_pacientes.append({
                'paciente': paciente,
                'padecimientos': [p.padecimiento.nombre for p in paciente.padecimientos.all()],
                'area': area_simulada.area_real.nombre,
                'compatibilidad': compatibilidad_paciente  # NUEVO
            })
    
    # Calcular carga promedio general
    carga_promedio = total_carga / areas_con_datos if areas_con_datos > 0 else 0
    simulacion.carga_trabajo_promedio = carga_promedio
    simulacion.save()
    
    # NUEVO: Serializar compatibilidades para JavaScript
    import json
    compatibilidades_json = json.dumps(compatibilidades, default=str)
    
    context = {
        'simulacion': simulacion,
        'resumen_areas': resumen_areas,
        'detalle_enfermeros': detalle_enfermeros,
        'detalle_pacientes': detalle_pacientes,
        'compatibilidades': compatibilidades,  # Para el template
        'compatibilidades_json': compatibilidades_json,  # Para JavaScript
        'carga_promedio': carga_promedio
    }
    
    return render(request, 'usuarioJefa/simulador_resultados.html', context)

def distribuir_pacientes_automaticamente(simulacion):
    """
    Distribuye automáticamente los pacientes simulados entre los enfermeros disponibles
    implementando TODOS los criterios de los requerimientos RQNF55-64 con manejo correcto de coincidencias
    """
    areas_simuladas = AreaSimulada.objects.filter(simulacion=simulacion)
    
    for area_simulada in areas_simuladas:
        # Obtener enfermeros y pacientes del área
        enfermeros = list(EnfermeroSimulado.objects.filter(area_simulada=area_simulada).select_related('enfermero_real'))
        pacientes = list(PacienteSimulado.objects.filter(area_simulada=area_simulada).prefetch_related('padecimientos__padecimiento'))
        
        if not enfermeros or not pacientes:
            continue
        
        # Limpiar asignaciones anteriores
        PacienteSimulado.objects.filter(area_simulada=area_simulada).update(enfermero_asignado=None)
        
        print(f"🏥 SIMULADOR - Distribuyendo {len(pacientes)} pacientes entre {len(enfermeros)} enfermeros en {area_simulada.area_real.nombre}")
        
        # Inicializar estructura de carga para cada enfermero
        enfermeros_carga = {}
        for enfermero in enfermeros:
            enfermeros_carga[enfermero.id] = {
                'enfermero': enfermero,
                'enfermero_real': enfermero.enfermero_real,
                'gravedad_1': 0,  # Máximo 3
                'gravedad_2': 0,  # Máximo 2  
                'gravedad_3': 0,  # Máximo 1
                'total_pacientes': 0,
                'carga_trabajo_actual': 0
            }
        
        # Ordenar pacientes por gravedad (graves primero)
        pacientes_ordenados = sorted(pacientes, key=lambda p: p.nivel_gravedad, reverse=True)
        
        # ALGORITMO PRINCIPAL con manejo correcto de coincidencias
        for paciente in pacientes_ordenados:
            print(f"\n👤 Asignando paciente {paciente.nombre_simulado} (Gravedad: {paciente.nivel_gravedad})")
            
            # Obtener padecimientos del paciente
            padecimientos_paciente = [p.padecimiento for p in paciente.padecimientos.all()]
            
            # Filtrar enfermeros que pueden tomar el paciente (límites de gravedad)
            enfermeros_disponibles = [
                (enfermero_id, carga_info) 
                for enfermero_id, carga_info in enfermeros_carga.items()
                if verificar_limites_gravedad(paciente, carga_info)
            ]
            
            if not enfermeros_disponibles:
                print(f"❌ No se pudo asignar {paciente.nombre_simulado} - Sin enfermeros disponibles")
                continue
            
            # APLICAR ALGORITMO DE COINCIDENCIAS SEGÚN MÓDULOS
            mejor_enfermero_id = aplicar_algoritmo_coincidencias(
                enfermeros_disponibles, 
                area_simulada.area_real, 
                padecimientos_paciente
            )
            
            if mejor_enfermero_id:
                mejor_enfermero = enfermeros_carga[mejor_enfermero_id]['enfermero']
                
                # Realizar asignación
                paciente.enfermero_asignado = mejor_enfermero
                paciente.save()
                
                # Actualizar contadores
                enfermeros_carga[mejor_enfermero_id][f'gravedad_{paciente.nivel_gravedad}'] += 1
                enfermeros_carga[mejor_enfermero_id]['total_pacientes'] += 1
                enfermeros_carga[mejor_enfermero_id]['carga_trabajo_actual'] = calcular_carga_trabajo_actual(enfermeros_carga[mejor_enfermero_id])
                
                enfermero_real = enfermeros_carga[mejor_enfermero_id]['enfermero_real']
                print(f"✅ Asignado a {enfermero_real.username}")
            else:
                print(f"❌ Error en algoritmo de coincidencias para {paciente.nombre_simulado}")

def aplicar_algoritmo_coincidencias(enfermeros_disponibles, area, padecimientos_paciente):
    """
    Aplica el algoritmo de coincidencias exacto según se especifica en "Módulos"
    """
    print("🔍 Aplicando algoritmo de coincidencias...")
    
    # PASO 1: Buscar coincidencias en PARÁMETRO 1 (Área de especialidad)
    coincidencias_param1 = []
    for enfermero_id, carga_info in enfermeros_disponibles:
        enfermero_real = carga_info['enfermero_real']
        if enfermero_real.areaEspecialidad and enfermero_real.areaEspecialidad.id == area.id:
            coincidencias_param1.append((enfermero_id, carga_info))
            print(f"   🎯 {enfermero_real.username}: Especialista en {area.nombre}")
    
    # Si hay 1 coincidencia en parámetro 1 → SELECCIONAR
    if len(coincidencias_param1) == 1:
        enfermero_seleccionado = coincidencias_param1[0][0]
        enfermero_real = coincidencias_param1[0][1]['enfermero_real']
        print(f"✅ SELECCIONADO por especialidad única: {enfermero_real.username}")
        return enfermero_seleccionado
    
    # Si hay 2+ coincidencias en parámetro 1 → usar parámetro 2 para desempatar
    elif len(coincidencias_param1) > 1:
        print(f"🔄 {len(coincidencias_param1)} especialistas encontrados, desempatando con fortalezas...")
        candidatos = coincidencias_param1
    
    # Si NO hay coincidencias en parámetro 1 → usar solo parámetro 2
    else:
        print("➡️ Sin especialistas, evaluando por fortalezas...")
        candidatos = enfermeros_disponibles
    
    # PASO 2: Evaluar PARÁMETRO 2 (Fortalezas vs Padecimientos)
    mejores_param2 = evaluar_fortalezas_vs_padecimientos(candidatos, padecimientos_paciente)
    
    # Si hay 1 ganador en parámetro 2 → SELECCIONAR
    if len(mejores_param2) == 1:
        enfermero_seleccionado = mejores_param2[0]['enfermero_id']
        enfermero_real = mejores_param2[0]['enfermero_real']
        print(f"✅ SELECCIONADO por fortalezas: {enfermero_real.username} ({mejores_param2[0]['coincidencias']} coincidencias)")
        return enfermero_seleccionado
    
    # Si hay empate → usar parámetro 3
    elif len(mejores_param2) > 1:
        print(f"🔄 {len(mejores_param2)} candidatos empatados en fortalezas, desempatando con carga...")
        candidatos_param3 = [(m['enfermero_id'], m['carga_info']) for m in mejores_param2]
    
    # Si no hay coincidencias en parámetro 2 → usar todos para parámetro 3
    else:
        print("➡️ Sin coincidencias en fortalezas, evaluando por carga...")
        candidatos_param3 = candidatos
    
    # PASO 3: Evaluar PARÁMETRO 3 (Carga de trabajo)
    mejor_param3 = evaluar_carga_trabajo(candidatos_param3)
    
    # Si hay 1 ganador → SELECCIONAR
    if len(mejor_param3) == 1:
        enfermero_seleccionado = mejor_param3[0]['enfermero_id']
        enfermero_real = mejor_param3[0]['enfermero_real']
        print(f"✅ SELECCIONADO por menor carga: {enfermero_real.username} ({mejor_param3[0]['carga']}% carga)")
        return enfermero_seleccionado
    
    # Si hay empate → usar parámetro 4 (desempate final)
    elif len(mejor_param3) > 1:
        print(f"🔄 {len(mejor_param3)} candidatos empatados en carga, desempate final con prioridad de área...")
        candidatos_param4 = [(m['enfermero_id'], m['carga_info']) for m in mejor_param3]
        
        # PASO 4: PARÁMETRO 4 (Nivel de prioridad del área) - DESEMPATE FINAL
        mejor_param4 = evaluar_prioridad_area(candidatos_param4, area)
        
        if mejor_param4:
            enfermero_seleccionado = mejor_param4['enfermero_id']
            enfermero_real = mejor_param4['enfermero_real']
            print(f"✅ SELECCIONADO por desempate final: {enfermero_real.username}")
            return enfermero_seleccionado
    
    # Si todo falla → seleccionar el primero disponible
    if enfermeros_disponibles:
        enfermero_seleccionado = enfermeros_disponibles[0][0]
        enfermero_real = enfermeros_disponibles[0][1]['enfermero_real']
        print(f"⚠️ SELECCIONADO por defecto: {enfermero_real.username}")
        return enfermero_seleccionado
    
    return None

def evaluar_fortalezas_vs_padecimientos(candidatos, padecimientos_paciente):
    """
    Evalúa coincidencias de fortalezas vs padecimientos y retorna los mejores
    """
    if not padecimientos_paciente:
        return []
    
    # Obtener fortalezas requeridas por los padecimientos
    fortalezas_requeridas = set()
    for padecimiento in padecimientos_paciente:
        fortalezas_requeridas.update(padecimiento.fortalezas.all())
    
    if not fortalezas_requeridas:
        return []
    
    evaluaciones = []
    max_coincidencias = 0
    
    for enfermero_id, carga_info in candidatos:
        enfermero_real = carga_info['enfermero_real']
        fortalezas_enfermero = set(enfermero_real.fortalezas.all())
        
        # Calcular coincidencias
        coincidencias = len(fortalezas_enfermero.intersection(fortalezas_requeridas))
        
        evaluaciones.append({
            'enfermero_id': enfermero_id,
            'enfermero_real': enfermero_real,
            'carga_info': carga_info,
            'coincidencias': coincidencias
        })
        
        if coincidencias > max_coincidencias:
            max_coincidencias = coincidencias
    
    # Retornar solo los que tienen el máximo de coincidencias
    mejores = [e for e in evaluaciones if e['coincidencias'] == max_coincidencias and max_coincidencias > 0]
    return mejores

def evaluar_carga_trabajo(candidatos):
    """
    Evalúa carga de trabajo y retorna los que tienen menor carga
    """
    evaluaciones = []
    min_carga = float('inf')
    
    for enfermero_id, carga_info in candidatos:
        carga_actual = carga_info['carga_trabajo_actual']
        
        evaluaciones.append({
            'enfermero_id': enfermero_id,
            'enfermero_real': carga_info['enfermero_real'],
            'carga_info': carga_info,
            'carga': carga_actual
        })
        
        if carga_actual < min_carga:
            min_carga = carga_actual
    
    # Retornar los que tienen la menor carga
    mejores = [e for e in evaluaciones if e['carga'] == min_carga]
    return mejores

def evaluar_prioridad_area(candidatos, area):
    """
    Desempate final usando nivel de prioridad del área
    """
    try:
        nivel_area = NivelPrioridadArea.objects.get(area=area)
        # En caso de empate total, seleccionar el primero
        if candidatos:
            return {
                'enfermero_id': candidatos[0][0],
                'enfermero_real': candidatos[0][1]['enfermero_real']
            }
    except NivelPrioridadArea.DoesNotExist:
        pass
    
    # Si no tiene nivel o error, seleccionar el primero
    if candidatos:
        return {
            'enfermero_id': candidatos[0][0],
            'enfermero_real': candidatos[0][1]['enfermero_real']
        }
    
    return None

# Mantener las funciones auxiliares anteriores
def verificar_limites_gravedad(paciente, carga_info):
    """
    Verifica si un enfermero puede tomar un paciente según los límites de gravedad (RQNF80)
    """
    gravedad = paciente.nivel_gravedad
    
    if gravedad == 3 and carga_info['gravedad_3'] >= 1:
        return False  # Ya tiene 1 paciente grave (máximo)
    elif gravedad == 2 and carga_info['gravedad_2'] >= 2:
        return False  # Ya tiene 2 pacientes medios (máximo)
    elif gravedad == 1 and carga_info['gravedad_1'] >= 3:
        return False  # Ya tiene 3 pacientes leves (máximo)
    
    return True

def calcular_carga_trabajo_actual(carga_info):
    """
    Calcula el porcentaje de carga de trabajo actual según RQNF79-80
    """
    # Peso por gravedad: grave=3, medio=2, leve=1
    carga_ponderada = (
        carga_info['gravedad_3'] * 3 +
        carga_info['gravedad_2'] * 2 +
        carga_info['gravedad_1'] * 1
    )
    
    # Máxima carga posible: 1 grave + 2 medios + 3 leves = 10 puntos
    carga_maxima = 10
    
    porcentaje = (carga_ponderada / carga_maxima) * 100
    return min(porcentaje, 100)  # Máximo 100%

    
@login_required
def lista_simulaciones(request):
    """
    Lista todas las simulaciones creadas
    """
    if request.user.tipoUsuario != 'JP':
        messages.error(request, 'No tienes permisos para acceder al simulador')
        return redirect('jefa:menu_jefa')
    
    simulaciones = SimulacionEvento.objects.all().order_by('-fecha_creacion')
    
    return render(request, 'usuarioJefa/lista_simulaciones.html', {
        'simulaciones': simulaciones
    })

def calcular_compatibilidades_simulador(simulacion):
    """
    Calcula las compatibilidades entre enfermeros y pacientes en la simulación
    similar a como se muestra en areas_fortalezas.html
    """
    compatibilidades_por_area = {}
    
    areas_simuladas = AreaSimulada.objects.filter(simulacion=simulacion).select_related('area_real')
    
    for area_simulada in areas_simuladas:
        # Obtener enfermeros del área
        enfermeros = EnfermeroSimulado.objects.filter(
            area_simulada=area_simulada
        ).select_related('enfermero_real')
        
        # Obtener pacientes asignados del área
        pacientes = PacienteSimulado.objects.filter(
            area_simulada=area_simulada,
            enfermero_asignado__isnull=False
        ).prefetch_related('padecimientos__padecimiento')
        
        compatibilidades_area = []
        
        for enfermero in enfermeros:
            # Obtener pacientes asignados a este enfermero
            pacientes_enfermero = pacientes.filter(enfermero_asignado=enfermero)
            
            for paciente in pacientes_enfermero:
                # Obtener fortalezas del enfermero
                fortalezas_enfermero = set(enfermero.enfermero_real.fortalezas.all())
                
                # Obtener padecimientos del paciente
                padecimientos_paciente = [p.padecimiento for p in paciente.padecimientos.all()]
                
                # Calcular compatibilidades específicas
                compatibilidades_paciente = []
                
                for padecimiento in padecimientos_paciente:
                    fortalezas_requeridas = set(padecimiento.fortalezas.all())
                    
                    # Encontrar coincidencias
                    coincidencias = fortalezas_enfermero.intersection(fortalezas_requeridas)
                    
                    if coincidencias:
                        for fortaleza in coincidencias:
                            compatibilidades_paciente.append({
                                'fortaleza': fortaleza.nombre,
                                'padecimiento': padecimiento.nombre,
                                'tipo': 'coincidencia'
                            })
                    else:
                        # Si no hay coincidencias, mostrar que no hay compatibilidad específica
                        compatibilidades_paciente.append({
                            'fortaleza': 'Sin coincidencia específica',
                            'padecimiento': padecimiento.nombre,
                            'tipo': 'sin_coincidencia'
                        })
                
                # Agregar información de por qué se asignó
                motivo_asignacion = determinar_motivo_asignacion(
                    enfermero.enfermero_real, 
                    area_simulada.area_real, 
                    padecimientos_paciente
                )
                
                compatibilidades_area.append({
                    'enfermero': enfermero.enfermero_real,
                    'paciente': paciente,
                    'compatibilidades': compatibilidades_paciente,
                    'motivo_principal': motivo_asignacion,
                    'total_coincidencias': len([c for c in compatibilidades_paciente if c['tipo'] == 'coincidencia'])
                })
        
        compatibilidades_por_area[area_simulada.area_real.nombre] = compatibilidades_area
    
    return compatibilidades_por_area

def determinar_motivo_asignacion(enfermero_real, area, padecimientos_paciente):
    """
    Determina el motivo principal por el cual se asignó el paciente al enfermero
    """
    motivos = []
    
    # 1. Verificar si es especialista del área
    if enfermero_real.areaEspecialidad and enfermero_real.areaEspecialidad.id == area.id:
        motivos.append("Especialista del área")
    
    # 2. Verificar coincidencias de fortalezas
    if padecimientos_paciente:
        fortalezas_enfermero = set(enfermero_real.fortalezas.all())
        total_coincidencias = 0
        
        for padecimiento in padecimientos_paciente:
            fortalezas_requeridas = set(padecimiento.fortalezas.all())
            coincidencias = len(fortalezas_enfermero.intersection(fortalezas_requeridas))
            total_coincidencias += coincidencias
        
        if total_coincidencias > 0:
            motivos.append(f"{total_coincidencias} fortaleza(s) coincidente(s)")
    
    # 3. Si no hay motivos específicos
    if not motivos:
        motivos.append("Distribución por carga de trabajo")
    
    return " | ".join(motivos)