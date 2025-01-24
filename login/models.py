from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class AreaEspecialidad(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    fortalezas = models.ManyToManyField('Fortaleza', blank=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Área de Especialidad'
        verbose_name_plural = 'Áreas de Especialidad'

    def clean(self):
        # Validar máximo 4 fortalezas
        if self.fortalezas.count() > 4:
            raise ValidationError('Un área no puede tener más de 4 fortalezas asociadas.')

class Fortaleza(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Fortaleza'
        verbose_name_plural = 'Fortalezas'

class Usuarios(AbstractUser):
    # Tipos de usuario
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

    # Datos personales
    tipoUsuario = models.CharField(max_length=2, choices=rolesUsuario, default=enfermeria)
    apellidos = models.CharField(max_length=150)
    edad = models.IntegerField(default=18)
    fechaNacimiento = models.DateField(null=True, blank=True)
    areaEspecialidad = models.ForeignKey(AreaEspecialidad, on_delete=models.SET_NULL, null=True)
    fortalezas = models.ManyToManyField(Fortaleza)
    
    # Estado del usuario
    estaActivo = models.BooleanField(default=True)
    fechaRegistro = models.DateTimeField(default=timezone.now)
    fechaEliminacion = models.DateTimeField(null=True, blank=True)

    # Otros campos
    cedula = models.CharField(max_length=20, blank=True, null=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    primerIngreso = models.BooleanField(default=True)

class HistorialPersonal(models.Model):
    usuario = models.ForeignKey(Usuarios, on_delete=models.CASCADE)
    fechaRegistro = models.DateTimeField(default=timezone.now)
    fechaEliminacion = models.DateTimeField(null=True, blank=True)
    tiempoActivo = models.DurationField(null=True, blank=True)  # Calculado automáticamente
    motivoEliminacion = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        # Calcular tiempo activo
        if self.fechaRegistro and self.fechaEliminacion:
            self.tiempoActivo = self.fechaEliminacion - self.fechaRegistro
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Historial de Personal'
        verbose_name_plural = 'Historiales de Personal'