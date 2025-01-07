from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from login.models import Usuarios 

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
        nombre_temporal = request.POST.get('nombre_temporal')
        contraseña = request.POST.get('contraseña')
        nombre_real = request.POST.get('nombre_real')
        cedula = request.POST.get('cedula')
        tipo_usuario = request.POST.get('tipo_usuario')

        # Validaciones
        if Usuarios.objects.filter(username=nombre_temporal).exists():
            messages.error(request, 'Este nombre de usuario temporal ya existe')
            return render(request, 'usuarioJefa/crear_usuarios.html')

        try:
            # Crear el nuevo usuario
            nuevo_usuario = Usuarios.objects.create_user(
                username=nombre_temporal,
                password=contraseña,
                first_name=nombre_real,
                cedula=cedula,
                tipoUsuario=tipo_usuario,
                primerIngreso=True,
                is_active=True
            )

            messages.success(request, 'Usuario creado exitosamente')
            return redirect('jefa:crear_usuarios.html') 

        except Exception as e:
            messages.error(request, 'Error al crear el usuario')
            return render(request, 'usuarioJefa/crear_usuarios.html')

    return render(request, 'usuarioJefa/crear_usuarios.html')

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
        usuario.is_active = not usuario.is_active
        usuario.save()
        
        estado = "activado" if usuario.is_active else "desactivado"
        messages.success(request, f'Usuario {estado} correctamente')
        
    return redirect('jefa:gestionar_usuarios')

def eliminar_usuario(request, usuario_id):
    if request.method == 'POST':
        usuario = get_object_or_404(Usuarios, id=usuario_id)
        try:
            usuario.delete()
            messages.success(request, 'Usuario eliminado correctamente')
        except Exception as e:
            messages.error(request, 'Error al eliminar el usuario')
    
    return redirect('jefa:gestionar_usuarios')