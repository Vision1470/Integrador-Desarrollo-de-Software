from django.db import models
from django.utils import timezone
from django.db.models import Q
from login.models import Usuarios, AreaEspecialidad
from usuarioEnfermeria.models import *

class Hospital(models.Model):
    nombre = models.CharField(max_length=200)
    direccion = models.TextField()

    def __str__(self):
        return self.nombre

class Paciente(models.Model):
    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
    ]
    
    ESTADO_CHOICES = [
        ('ACTIVO', 'Activo'),
        ('INACTIVO', 'Inactivo'),
    ]

    # Datos personales
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField()
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES)
    num_seguridad_social = models.CharField(max_length=20, unique=True)
    
    # Datos de ingreso
    fecha_ingreso = models.DateTimeField(default=timezone.now)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='ACTIVO')
    area = models.ForeignKey(AreaEspecialidad, on_delete=models.PROTECT)
    
    # Relaciones con el personal
    doctor_actual = models.ForeignKey(
        Usuarios, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='pacientes_doctor',
        limit_choices_to={'tipoUsuario': 'DR'}
    )
    enfermero_actual = models.ForeignKey(
        Usuarios,
        on_delete=models.SET_NULL,
        null=True,
        related_name='pacientes_enfermero',
        limit_choices_to={'tipoUsuario': 'EN'}
    )
    
    # Datos de traslado
    hospital_origen = models.CharField(max_length=200, blank=True, null=True)
    
    # Control de estado
    numero_ingresos = models.PositiveIntegerField(default=1)
    esta_activo = models.BooleanField(default=True)
    fecha_alta = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"

    def dar_alta(self):
        print(f"Ejecutando dar_alta para paciente {self.id}")  # Debug
        self.esta_activo = False
        self.estado = 'INACTIVO'
        self.fecha_alta = timezone.now()
        self.save()
        print(f"Alta completada: activo={self.esta_activo}, estado={self.estado}")  # Debug
        return True

class HistorialMedico(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='historial_medico')
    doctor = models.ForeignKey(
        Usuarios,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'tipoUsuario': 'DR'}
    )
    fecha = models.DateTimeField(auto_now_add=True)
    diagnostico = models.TextField()

    class Meta:
        ordering = ['-fecha']

class RecetaMedica(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='recetas_medicas')  # Cambiado de 'recetas' a 'recetas_medicas'
    doctor = models.ForeignKey(
        Usuarios,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'tipoUsuario': 'DR'}
    )
    fecha = models.DateTimeField(auto_now_add=True)
    prescripcion = models.TextField()
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ['-fecha']

class HistorialDoctores(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='historial_doctores')
    doctor = models.ForeignKey(
        Usuarios,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'tipoUsuario': 'DR'}
    )
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    motivo_cambio = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-fecha_asignacion']
        verbose_name = 'Historial de Doctores'
        verbose_name_plural = 'Historiales de Doctores'

class HistorialEnfermeros(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='historial_enfermeros')
    enfermero = models.ForeignKey(
        Usuarios,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'tipoUsuario': 'EN'}
    )
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    motivo_cambio = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-fecha_asignacion']
        verbose_name = 'Historial de Enfermeros'
        verbose_name_plural = 'Historiales de Enfermeros'

class Compuesto(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Compuesto'
        verbose_name_plural = 'Compuestos'

class Medicamento(models.Model):
    nombre = models.CharField(max_length=200)
    gramaje = models.CharField(max_length=50)
    compuestos = models.ManyToManyField(Compuesto)
    cantidad_disponible = models.IntegerField(default=0)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre} {self.gramaje}g"

    class Meta:
        verbose_name = 'Medicamento'
        verbose_name_plural = 'Medicamentos'

class Instrumento(models.Model):
    nombre = models.CharField(max_length=200)
    cantidad = models.IntegerField(default=0)
    especificaciones = models.TextField()
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Instrumento'
        verbose_name_plural = 'Instrumentos'

