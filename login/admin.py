from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuarios

class CustomUserAdmin(UserAdmin):
    model = Usuarios
    list_display = ['username', 'first_name', 'email', 'tipoUsuario', 'primerIngreso']
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Información Personal', {'fields': ('first_name', 'email', 'telefono', 'direccion')}),
        ('Información Profesional', {'fields': ('tipoUsuario', 'cedula')}),
        ('Estado', {'fields': ('primerIngreso', 'is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'tipoUsuario', 'is_staff', 'is_superuser'),
        }),
    )

admin.site.register(Usuarios, CustomUserAdmin)