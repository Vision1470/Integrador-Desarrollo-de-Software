from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from login.models import *
from usuarioJefa.models import Paciente
from django.utils import timezone
from usuarioJefa.forms import PacienteForm

def menu_jefa(request):
    return render(request, 'usuarioJefa/menu_jefa.html')

def pacientes_jefa(request):
    # Obtener todos los pacientes
    print("Número de pacientes:", Paciente.objects.count())  # Para debug
    pacientes = Paciente.objects.select_related(
        'area', 
        'doctor_actual', 
        'enfermero_actual'
    ).all()
    
    context = {
        'pacientes': pacientes,
    }
    
    print("Contexto:", context)  # Para debug
    return render(request, 'usuarioJefa/pacientes_jefa.html', context)

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
    return render(request, 'usuarioJefa/historiales.html')  

# views.py
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
    return render(request, 'usuarioJefa/usuarios_.html')

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
            
            messages.success(request, 'Usuario creado exitosamente')
            return render(request, 'usuarioJefa/crear_usuarios.html')
            
        except Exception as e:
            messages.error(request, f'Error al crear el usuario: {str(e)}')
            return render(request, 'usuarioJefa/crear_usuarios.html')
    
    # GET: mostrar formulario
    context = {
        'areas': AreaEspecialidad.objects.all(),
        'fortalezas': Fortaleza.objects.all(),
    }
    return render(request, 'usuarioJefa/crear_usuarios.html', context)

def gestionar_usuarios(request):
    # Filtrar solo usuarios activos
    usuarios = Usuarios.objects.filter(estaActivo=True).order_by('tipoUsuario', 'first_name')
    return render(request, 'usuarioJefa/gestionar_usuarios.html', {'usuarios': usuarios})

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
            return redirect('jefa:gestionar_usuarios')
            
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
            return redirect('jefa:historial_empleados')
        # Si no, redirigir a gestionar usuarios
        return redirect('jefa:gestionar_usuarios')
    
    return redirect('jefa:gestionar_usuarios')