from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuarios(AbstractUser):
    # Constantes para los tipos de usuario
    jefaPiso = 'JP'
    enfermeria = 'EN'
    doctor = 'DR'
    cocina = 'CO'
    
    rolesUsuario = [
        (jefaPiso, 'Jefa de Piso'),
        (enfermeria, 'Enfermería'),
        (doctor, 'Doctor'),
        (cocina, 'Cocina'),
    ]

    tipoUsuario = models.CharField(
        max_length=2,
        choices=rolesUsuario,
        default=enfermeria,
    )

    nombreTemporal = models.CharField(max_length=20, blank=True, null=True, help_text="Nombre temporal para el primer ingreso")
    cedula = models.CharField(max_length=20, blank=True, null=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    primerIngreso = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f"{self.first_name} ({self.get_tipoUsuario_display()})"