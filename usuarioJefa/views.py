from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from login.models import Usuarios, AreaEspecialidad, Fortaleza, HistorialPersonal

def menu_jefa(request):
    return render(request, 'usuarioJefa/menu_jefa.html')

def pacientes_jefa(request):
    return render(request, 'usuarioJefa/pacientes_jefa.html')

def historiales_(request):
    return render(request, 'usuarioJefa/historiales.html')  

def historial_empleados(request):
    return render(request, 'usuarioJefa/historial_empleados.html')

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
    usuarios = Usuarios.objects.all().order_by('tipoUsuario', 'first_name')
    return render(request, 'usuarioJefa/gestionar_usuarios.html', {'usuarios': usuarios})

def editar_usuario(request, usuario_id):
    usuario = get_object_or_404(Usuarios, id=usuario_id)
    
    if request.method == 'POST':
        nombre_real = request.POST.get('nombre_real')
        cedula = request.POST.get('cedula')
        
        try:
            usuario.first_name = nombre_real
            usuario.cedula = cedula
            usuario.save()
            messages.success(request, 'Usuario actualizado correctamente')
            return redirect('jefa:gestionar_usuarios')
        except Exception as e:
            messages.error(request, 'Error al actualizar el usuario')
    
    return render(request, 'usuarioJefa/editar_usuario.html', {'usuario': usuario})

def toggle_usuario(request, usuario_id):
    if request.method == 'POST':
        usuario = get_object_or_404(Usuarios, id=usuario_id)
        action = request.POST.get('action')
        
        try:
            if action == 'desactivar':
                usuario.estaActivo = False
                usuario.save()
                
                # Crear registro en historial
                HistorialPersonal.objects.create(
                    usuario=usuario,
                    fechaRegistro=usuario.fechaRegistro,
                    motivoEliminacion='Desactivación por jefa de piso'
                )
                messages.success(request, 'Usuario desactivado correctamente')
            
            elif action == 'activar':
                usuario.estaActivo = True
                usuario.fechaEliminacion = None
                usuario.save()
                messages.success(request, 'Usuario activado correctamente')
                
        except Exception as e:
            messages.error(request, f'Error al modificar el estado del usuario: {str(e)}')
    
    return redirect('jefa:gestionar_usuarios')

