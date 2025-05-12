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

@login_required
def areas_fortalezas(request):
    areas = AreaEspecialidad.objects.all()
    fortalezas = Fortaleza.objects.all()
    return render(request, 'usuarioJefa/areas_fortalezas.html', {
        'areas': areas,
        'fortalezas': fortalezas
    })

@login_required
def crear_area(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        fortalezas_ids = request.POST.getlist('fortalezas')
        
        try:
            area = AreaEspecialidad.objects.create(
                nombre=nombre,
                descripcion=descripcion
            )
            if len(fortalezas_ids) <= 4:
                area.fortalezas.set(fortalezas_ids)
                messages.success(request, 'Área creada exitosamente.')
                return redirect('areas_fortalezas')
            else:
                area.delete()
                messages.error(request, 'No se pueden asignar más de 4 fortalezas a un área.')
        except Exception as e:
            messages.error(request, f'Error al crear el área: {str(e)}')
    
    fortalezas = Fortaleza.objects.all()
    return render(request, 'usuarioJefa/crear_area.html', {'fortalezas': fortalezas})

@login_required
def crear_fortaleza(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        
        try:
            Fortaleza.objects.create(
                nombre=nombre,
                descripcion=descripcion
            )
            messages.success(request, 'Fortaleza creada exitosamente.')
            return redirect('areas_fortalezas')
        except Exception as e:
            messages.error(request, f'Error al crear la fortaleza: {str(e)}')
    
    return render(request, 'usuarioJefa/crear_fortaleza.html')

@login_required
def editar_area(request, area_id):
    area = get_object_or_404(AreaEspecialidad, id=area_id)
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        fortalezas_ids = request.POST.getlist('fortalezas')
        
        try:
            if len(fortalezas_ids) <= 4:
                area.nombre = nombre
                area.descripcion = descripcion
                area.save()
                area.fortalezas.set(fortalezas_ids)
                messages.success(request, 'Área actualizada exitosamente.')
                return redirect('areas_fortalezas')
            else:
                messages.error(request, 'No se pueden asignar más de 4 fortalezas a un área.')
        except Exception as e:
            messages.error(request, f'Error al actualizar el área: {str(e)}')
    
    fortalezas = Fortaleza.objects.all()
    return render(request, 'usuarioJefa/editar_area.html', {
        'area': area,
        'fortalezas': fortalezas
    })

@login_required
def editar_fortaleza(request, fortaleza_id):
    fortaleza = get_object_or_404(Fortaleza, id=fortaleza_id)
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        
        try:
            fortaleza.nombre = nombre
            fortaleza.descripcion = descripcion
            fortaleza.save()
            messages.success(request, 'Fortaleza actualizada exitosamente.')
            return redirect('areas_fortalezas')
        except Exception as e:
            messages.error(request, f'Error al actualizar la fortaleza: {str(e)}')
    
    return render(request, 'usuarioJefa/editar_fortaleza.html', {'fortaleza': fortaleza})
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
        area=area, activo=True
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
            distribucion_actual = cargar_distribucion_previa(distribucion_previa_id, enfermeros_activos)
            distribucion_id = distribucion_previa_id
            messages.success(request, "Se ha cargado la distribución previa correctamente.")
        else:
            # Generar nueva distribución según el método seleccionado
            if metodo_distribucion == 'equitativa':
                distribucion_actual, distribucion_id = generar_distribucion_equitativa(
                    request, area, enfermeros_activos, pacientes_en_area, considerar_desempeno, descripcion
                )
                messages.success(request, "Se ha generado una distribución equitativa.")
            elif metodo_distribucion == 'gravedad':
                distribucion_actual, distribucion_id = generar_distribucion_por_gravedad(
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
            
            # Crear asignación de paciente
            AsignacionPaciente.objects.create(
                paciente=paciente.paciente,
                distribucion=distribucion,
                activo=True
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
                    
                    # Crear asignación de paciente
                    AsignacionPaciente.objects.create(
                        paciente=paciente.paciente,
                        distribucion=distribucion,
                        activo=True
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
                
                # Crear asignación de paciente
                AsignacionPaciente.objects.create(
                    paciente=paciente.paciente,
                    distribucion=distribucion,
                    activo=True
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
                
                # Crear asignación de paciente
                AsignacionPaciente.objects.create(
                    paciente=paciente.paciente,
                    distribucion=distribucion,
                    activo=True
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

def cargar_distribucion_previa(distribucion_id, enfermeros_activos):
    """
    Carga una distribución previa desde la base de datos.
    """
    distribucion = get_object_or_404(DistribucionPacientes, id=distribucion_id)
    
    # Obtener IDs de enfermeros actualmente activos
    enfermeros_activos_ids = [e.enfermero.id for e in enfermeros_activos]
    
    # Obtener todas las distribuciones asociadas
    distribuciones = DistribucionPacientes.objects.filter(
        area=distribucion.area,
        fecha_asignacion__date=distribucion.fecha_asignacion.date()
    )
    
    # Cargar asignaciones existentes
    asignaciones = []
    for dist in distribuciones:
        if dist.enfermero.id in enfermeros_activos_ids:
            # Obtener pacientes asignados a este enfermero
            pacientes_asignados = Paciente.objects.filter(
                area=dist.area,
                enfermero_actual=dist.enfermero,
                esta_activo=True
            )
            
            # Calcular carga de trabajo
            carga_maxima = 1*3 + 2*2 + 3*1  # 1 grave + 2 medios + 3 leves = 10
            carga_actual = (dist.pacientes_gravedad_3 * 3) + (dist.pacientes_gravedad_2 * 2) + (dist.pacientes_gravedad_1 * 1)
            carga_trabajo = int((carga_actual / carga_maxima) * 100) if carga_maxima > 0 else 0
            
            asignaciones.append({
                'enfermero': dist.enfermero,
                'distribucion': dist,
                'pacientes': list(pacientes_asignados),
                'gravedad_1': dist.pacientes_gravedad_1,
                'gravedad_2': dist.pacientes_gravedad_2,
                'gravedad_3': dist.pacientes_gravedad_3,
                'total_pacientes': len(pacientes_asignados),
                'carga_trabajo': carga_trabajo
            })
    
    return asignaciones

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
                
                # Crear asignación de paciente
                AsignacionPaciente.objects.create(
                    paciente=paciente.paciente,
                    distribucion=distribucion,
                    activo=True
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
                
                # Crear asignación de paciente
                AsignacionPaciente.objects.create(
                    paciente=paciente.paciente,
                    distribucion=distribucion,
                    activo=True
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
                
                # Crear asignación de paciente
                AsignacionPaciente.objects.create(
                    paciente=paciente.paciente,
                    distribucion=distribucion,
                    activo=True
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