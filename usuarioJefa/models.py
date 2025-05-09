from django.db import models
from django.utils import timezone
from django.db.models import Q
from login.models import Usuarios, AreaEspecialidad
from django.apps import apps

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

    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField()
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES)
    num_seguridad_social = models.CharField(max_length=20, unique=True)
    fecha_ingreso = models.DateTimeField(default=timezone.now)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='ACTIVO')
    area = models.ForeignKey('login.AreaEspecialidad', on_delete=models.PROTECT)  # Referenciamos a login.AreaEspecialidad
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
    hospital_origen = models.CharField(max_length=200, blank=True, null=True)
    esta_activo = models.BooleanField(default=True)
    fecha_alta = models.DateTimeField(null=True, blank=True)
    numero_ingresos = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"

    def dar_alta(self):
        self.esta_activo = False
        self.estado = 'INACTIVO'
        self.fecha_alta = timezone.now()
        self.save()

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

class HistorialCompletoPaciente(models.Model):

    paciente = models.OneToOneField(Paciente, on_delete=models.CASCADE, related_name='historial_completo')
    
    def get_recetas(self):
        Receta = apps.get_model('usuarioDoctor', 'Receta')
        return Receta.objects.filter(paciente=self.paciente).order_by('-fecha_creacion')
    
    def get_diagnosticos(self):
        Diagnostico = apps.get_model('usuarioDoctor', 'Diagnostico')
        return Diagnostico.objects.filter(paciente=self.paciente).order_by('-fecha_creacion')
    
    def get_seguimientos(self):
        SeguimientoCuidados = apps.get_model('usuarioEnfermeria', 'SeguimientoCuidados')
        return SeguimientoCuidados.objects.filter(paciente=self.paciente).order_by('-fecha_registro')
    
    def get_formularios(self):
        FormularioSeguimiento = apps.get_model('usuarioEnfermeria', 'FormularioSeguimiento')
        return FormularioSeguimiento.objects.filter(paciente=self.paciente).order_by('-fecha_registro')
    
# models.py
# models.py
# models.py
# models.py
# models.py

class AsignacionCalendario(models.Model):
    enfermero = models.ForeignKey('login.Usuarios', on_delete=models.PROTECT)
    area = models.ForeignKey('login.AreaEspecialidad', on_delete=models.PROTECT)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    bimestre = models.IntegerField()
    year = models.IntegerField()
    activo = models.BooleanField(default=True)

    class Meta:
        unique_together = ['enfermero', 'fecha_inicio', 'fecha_fin']

class HistorialCambios(models.Model):
    asignacion = models.ForeignKey(AsignacionCalendario, on_delete=models.CASCADE)
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    area_anterior = models.ForeignKey('login.AreaEspecialidad', on_delete=models.PROTECT, related_name='cambios_anteriores')
    area_nueva = models.ForeignKey('login.AreaEspecialidad', on_delete=models.PROTECT, related_name='cambios_nuevos')
    fecha_inicio_anterior = models.DateField()
    fecha_fin_anterior = models.DateField()
    fecha_inicio_nueva = models.DateField()
    fecha_fin_nueva = models.DateField()

    class Meta:
        ordering = ['-fecha_cambio']

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class AreaSobrecarga(models.Model):
    area = models.ForeignKey('login.AreaEspecialidad', on_delete=models.CASCADE)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.area.nombre} - Sobrecarga {'Activa' if self.activo else 'Inactiva'}"

    class Meta:
        verbose_name = "Área en Sobrecarga"
        verbose_name_plural = "Áreas en Sobrecarga"

class NivelPrioridadArea(models.Model):
    area = models.OneToOneField('login.AreaEspecialidad', on_delete=models.CASCADE)
    nivel_prioridad = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Nivel de prioridad del área (1-5)"
    )

    def __str__(self):
        return f"{self.area.nombre} - Prioridad: {self.nivel_prioridad}"

    class Meta:
        verbose_name = "Nivel de Prioridad de Área"
        verbose_name_plural = "Niveles de Prioridad de Áreas"

class GravedadPaciente(models.Model):
    NIVELES_GRAVEDAD = [
        (1, 'Baja'),
        (2, 'Media'),
        (3, 'Alta')
    ]
    
    paciente = models.ForeignKey('usuarioJefa.Paciente', on_delete=models.CASCADE)
    nivel_gravedad = models.IntegerField(
        choices=NIVELES_GRAVEDAD,
        validators=[MinValueValidator(1), MaxValueValidator(3)]
    )
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.paciente.nombre} - Gravedad: {self.get_nivel_gravedad_display()}"

    class Meta:
        verbose_name = "Gravedad de Paciente"
        verbose_name_plural = "Gravedades de Pacientes"



class DistribucionPacientes(models.Model):
    enfermero = models.ForeignKey('login.Usuarios', on_delete=models.CASCADE)
    area = models.ForeignKey('login.AreaEspecialidad', on_delete=models.CASCADE)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    
    pacientes_gravedad_1 = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(3)],
        help_text="Pacientes de gravedad baja (máx. 3)"
    )
    pacientes_gravedad_2 = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(2)],
        help_text="Pacientes de gravedad media (máx. 2)"
    )
    pacientes_gravedad_3 = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Pacientes de gravedad alta (máx. 1)"
    )

    def clean(self):
        if self.pacientes_gravedad_1 > 3:
            raise ValidationError('Un enfermero no puede atender más de 3 pacientes de gravedad baja')
        if self.pacientes_gravedad_2 > 2:
            raise ValidationError('Un enfermero no puede atender más de 2 pacientes de gravedad media')
        if self.pacientes_gravedad_3 > 1:
            raise ValidationError('Un enfermero no puede atender más de 1 paciente de gravedad alta')

    def total_pacientes(self):
        return self.pacientes_gravedad_1 + self.pacientes_gravedad_2 + self.pacientes_gravedad_3

    class Meta:
        verbose_name = "Distribución de Pacientes"
        verbose_name_plural = "Distribuciones de Pacientes"
        unique_together = ['enfermero', 'area']