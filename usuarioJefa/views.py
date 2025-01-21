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
from datetime import datetime

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
    # Obtener todos los usuarios
    usuarios = Usuarios.objects.all().select_related('areaEspecialidad').prefetch_related('fortalezas')
    
    # Ordenar por fecha de registro
    usuarios = usuarios.order_by('-fechaRegistro')

    return render(request, 'usuarioJefa/historiales.html', {
        'usuarios': usuarios
    }) 

def historial_empleados(request):
    # Obtener todos los usuarios
    usuarios = Usuarios.objects.all().select_related('areaEspecialidad').prefetch_related('fortalezas')
    
    # Ordenar por fecha de registro
    usuarios = usuarios.order_by('-fechaRegistro')

    return render(request, 'usuarioJefa/historial_empleados.html', {
        'usuarios': usuarios
    })

def historial_pacientes(request):

    return render(request, 'usuarioJefa/historial_pacientes.html') 

def calendario_(request):
    return render(request, 'usuarioJefa/calendario.html')  

def usuarios_(request):
    usuarios_activos = Usuarios.objects.filter(estaActivo=True)
    areas = AreaEspecialidad.objects.all()
    fortalezas = Fortaleza.objects.all()

    return render(request, 'usuarioJefa/usuarios_.html', {
        'usuarios': usuarios_activos,
        'areas': areas,
        'fortalezas': fortalezas
    })

def gestionar_usuarios(request):
    # Filtrar solo usuarios activos
    usuarios = Usuarios.objects.filter(estaActivo=True).order_by('tipoUsuario', 'first_name')
    return render(request, 'usuarioJefa/gestionar_usuarios.html', {'usuarios': usuarios})

def crear_usuarios(request):
    if request.method == 'POST':
        try:
            # Datos básicos
            nombre = request.POST.get('nombre')
            apellidos = request.POST.get('apellidos')
            edad = request.POST.get('edad')
            fecha_nacimiento = request.POST.get('fecha_nacimiento')

            # Área de especialidad
            area_especialidad_id = request.POST.get('area_especialidad')
            area_especialidad = AreaEspecialidad.objects.get(id=area_especialidad_id)
            
            # Crear usuario
            usuario = Usuarios.objects.create_user(
                username=request.POST.get('nombre_temporal'),
                password=request.POST.get('contraseña'),
                first_name=nombre,
                apellidos=apellidos,
                edad=edad,
                fechaNacimiento=fecha_nacimiento,
                areaEspecialidad=area_especialidad,
                estaActivo=True,
                primerIngreso=True
            )
            
            # Agregar fortalezas
            fortalezas_ids = request.POST.getlist('fortalezas')
            if len(fortalezas_ids) > 4:
                raise ValueError("No se pueden seleccionar más de 4 fortalezas")
            usuario.fortalezas.set(fortalezas_ids)
            
            usuario.tipoUsuario = request.POST.get('tipo_usuario')
            usuario.cedula = request.POST.get('cedula')

            messages.success(request, 'Usuario creado exitosamente')
            return redirect(request, 'usuarioJefa/usuarios_.html')
            
        except Exception as e:
            messages.error(request, f'Error al crear el usuario: {str(e)}')
            return redirect(request, 'usuarioJefa/usuarios_.html')
    
    # GET: mostrar formulario
    context = {
        'areas': AreaEspecialidad.objects.all(),
        'fortalezas': Fortaleza.objects.all(),
    }
    return redirect(request, 'usuarioJefa/crear_usuarios.html', context)

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