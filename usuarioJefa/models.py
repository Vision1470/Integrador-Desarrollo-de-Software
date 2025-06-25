from django.db import models
from django.utils import timezone
from django.db.models import Q
from login.models import Usuarios, AreaEspecialidad
from django.apps import apps
from django.core.exceptions import ValidationError

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
        constraints = [
            models.UniqueConstraint(
                fields=['enfermero', 'fecha_inicio', 'fecha_fin'],
                condition=models.Q(activo=True),
                name='unique_active_assignment'
            )
        ]

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



# Modificación al modelo DistribucionPacientes en usuarioJefa/models.py
class DistribucionPacientes(models.Model):
    enfermero = models.ForeignKey('login.Usuarios', on_delete=models.CASCADE)
    area = models.ForeignKey('login.AreaEspecialidad', on_delete=models.CASCADE)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    descripcion = models.CharField(max_length=255, blank=True)
    activo = models.BooleanField(default=True)
    
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
    
    def get_pacientes_asignados(self):
        """Retorna los pacientes asignados a este enfermero en esta distribución"""
        return Paciente.objects.filter(asignacionpaciente__distribucion=self)

    class Meta:
        verbose_name = "Distribución de Pacientes"
        verbose_name_plural = "Distribuciones de Pacientes"

class AsignacionPaciente(models.Model):
    paciente = models.ForeignKey('usuarioJefa.Paciente', on_delete=models.CASCADE, related_name='asignacionpaciente')
    distribucion = models.ForeignKey('DistribucionPacientes', on_delete=models.CASCADE, related_name='asignaciones')
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Asignación de Paciente"
        verbose_name_plural = "Asignaciones de Pacientes"
        unique_together = ['paciente', 'distribucion']  # Un paciente solo puede estar asignado a una distribución a la vez
        
    def __str__(self):
        return f"Paciente {self.paciente.nombres} asignado a {self.distribucion.enfermero.username}"
    
class AsignacionEmergencia(models.Model):
    """
    Modelo para manejar asignaciones temporales de emergencia.
    Estas asignaciones son espontáneas y temporales, sobrescribiendo
    las asignaciones normales del calendario por períodos específicos.
    """
    enfermero = models.ForeignKey(
        'login.Usuarios', 
        on_delete=models.CASCADE,
        limit_choices_to={'tipoUsuario': 'EN'}
    )
    area_origen = models.ForeignKey(
        'login.AreaEspecialidad', 
        on_delete=models.CASCADE,
        related_name='emergencias_origen',
        help_text="Área de donde viene el enfermero"
    )
    area_destino = models.ForeignKey(
        'login.AreaEspecialidad', 
        on_delete=models.CASCADE,
        related_name='emergencias_destino',
        help_text="Área a donde va temporalmente"
    )
    fecha_inicio = models.DateTimeField(
        help_text="Inicio de la asignación temporal"
    )
    fecha_fin = models.DateTimeField(
        help_text="Fin de la asignación temporal"
    )
    motivo = models.TextField(
        help_text="Razón de la asignación de emergencia"
    )
    activa = models.BooleanField(
        default=True,
        help_text="Si la asignación de emergencia está activa"
    )
    creada_por = models.ForeignKey(
        'login.Usuarios',
        on_delete=models.CASCADE,
        related_name='emergencias_creadas',
        limit_choices_to={'tipoUsuario': 'JP'}
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_finalizacion = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Asignación de Emergencia"
        verbose_name_plural = "Asignaciones de Emergencia"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        estado = "Activa" if self.activa else "Finalizada"
        return f"Emergencia: {self.enfermero.username} - {self.area_destino.nombre} ({estado})"
    
    def clean(self):
        """Validaciones del modelo"""
        if self.fecha_fin <= self.fecha_inicio:
            raise ValidationError('La fecha de fin debe ser posterior a la fecha de inicio')
        
        if self.area_origen == self.area_destino:
            raise ValidationError('El área de origen y destino no pueden ser la misma')
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def finalizar(self):
        """Finaliza la asignación de emergencia"""
        self.activa = False
        self.fecha_finalizacion = timezone.now()
        self.save()
    
    def esta_vigente(self, fecha=None):
        """Verifica si la asignación está vigente en una fecha específica"""
        if fecha is None:
            fecha = timezone.now()
        
        return (
            self.activa and 
            self.fecha_inicio <= fecha <= self.fecha_fin
        )

    @classmethod
    def obtener_asignaciones_vigentes(cls, enfermero=None, area=None, fecha=None):
        """Obtiene asignaciones de emergencia vigentes"""
        if fecha is None:
            fecha = timezone.now()
        
        filtros = {
            'activa': True,
            'fecha_inicio__lte': fecha,
            'fecha_fin__gte': fecha
        }
        
        if enfermero:
            filtros['enfermero'] = enfermero
        
        if area:
            filtros['area_destino'] = area
            
        return cls.objects.filter(**filtros)
    
# Modelos para el Simulador de Eventos
class SimulacionEvento(models.Model):
    nombre = models.CharField(max_length=200, help_text="Nombre/etiqueta para identificar la simulación")
    descripcion = models.TextField(blank=True, help_text="Descripción opcional de la simulación")
    creada_por = models.ForeignKey(
        'login.Usuarios',
        on_delete=models.CASCADE,
        limit_choices_to={'tipoUsuario': 'JP'}
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activa = models.BooleanField(default=True, help_text="Si la simulación está activa para comparaciones")
    
    # Resultados calculados
    total_areas = models.IntegerField(default=0)
    total_enfermeros = models.IntegerField(default=0)
    total_pacientes = models.IntegerField(default=0)
    carga_trabajo_promedio = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    class Meta:
        verbose_name = "Simulación de Evento"
        verbose_name_plural = "Simulaciones de Eventos"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.nombre} - {self.fecha_creacion.strftime('%d/%m/%Y')}"

class AreaSimulada(models.Model):
    simulacion = models.ForeignKey(SimulacionEvento, on_delete=models.CASCADE, related_name='areas_simuladas')
    area_real = models.ForeignKey('login.AreaEspecialidad', on_delete=models.CASCADE)
    cantidad_enfermeros = models.IntegerField(default=0, help_text="Cantidad de enfermeros asignados en la simulación")
    cantidad_pacientes = models.IntegerField(default=0, help_text="Cantidad de pacientes en esta área")
    en_sobrecarga = models.BooleanField(default=False, help_text="Si el área está marcada como sobrecargada")
    
    # Métricas calculadas
    carga_trabajo_area = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    ratio_pacientes_enfermero = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    class Meta:
        verbose_name = "Área Simulada"
        verbose_name_plural = "Áreas Simuladas"
        unique_together = ['simulacion', 'area_real']
    
    def __str__(self):
        return f"{self.area_real.nombre} - {self.simulacion.nombre}"

class EnfermeroSimulado(models.Model):
    area_simulada = models.ForeignKey(AreaSimulada, on_delete=models.CASCADE, related_name='enfermeros_asignados')
    enfermero_real = models.ForeignKey(
        'login.Usuarios', 
        on_delete=models.CASCADE,
        limit_choices_to={'tipoUsuario': 'EN'}
    )
    pacientes_asignados = models.IntegerField(default=0, help_text="Cantidad de pacientes asignados a este enfermero")
    carga_trabajo_individual = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    class Meta:
        verbose_name = "Enfermero Simulado"
        verbose_name_plural = "Enfermeros Simulados"
        unique_together = ['area_simulada', 'enfermero_real']
    
    def __str__(self):
        return f"{self.enfermero_real.username} - {self.area_simulada.area_real.nombre}"

class PacienteSimulado(models.Model):
    NIVELES_GRAVEDAD = [
        (1, 'Leve'),
        (2, 'Moderado'),
        (3, 'Grave')
    ]
    
    area_simulada = models.ForeignKey(AreaSimulada, on_delete=models.CASCADE, related_name='pacientes_simulados')
    enfermero_asignado = models.ForeignKey(
        EnfermeroSimulado, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='pacientes_a_cargo'
    )
    nombre_simulado = models.CharField(max_length=100, help_text="Nombre generado: Paciente 1, Paciente 2, etc.")
    nivel_gravedad = models.IntegerField(choices=NIVELES_GRAVEDAD, default=1)
    
    class Meta:
        verbose_name = "Paciente Simulado"
        verbose_name_plural = "Pacientes Simulados"
    
    def __str__(self):
        return f"{self.nombre_simulado} - {self.area_simulada.area_real.nombre}"

class PadecimientoSimulado(models.Model):
    paciente_simulado = models.ForeignKey(PacienteSimulado, on_delete=models.CASCADE, related_name='padecimientos')
    padecimiento = models.ForeignKey('usuarioDoctor.Padecimiento', on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = "Padecimiento Simulado"
        verbose_name_plural = "Padecimientos Simulados"
        unique_together = ['paciente_simulado', 'padecimiento']
    
    def __str__(self):
        return f"{self.padecimiento.nombre} - {self.paciente_simulado.nombre_simulado}"
    

class PersonalTemporal(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre completo")
    area = models.ForeignKey(AreaEspecialidad, on_delete=models.CASCADE, verbose_name="Área asignada")
    
    # Fechas y tiempo
    fecha_inicio = models.DateTimeField(verbose_name="Fecha de inicio")
    fecha_fin = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de fin (opcional)")
    tiempo_indefinido = models.BooleanField(default=False, verbose_name="Tiempo indefinido")
    
    # Estado y control
    activo = models.BooleanField(default=True)
    desactivado_automaticamente = models.BooleanField(default=False)
    fecha_desactivacion = models.DateTimeField(null=True, blank=True)
    motivo_desactivacion = models.TextField(blank=True)
    
    # Metadatos
    motivo_asignacion = models.TextField(verbose_name="Motivo de la asignación")
    creado_por = models.ForeignKey(Usuarios, on_delete=models.CASCADE, related_name='personal_temporal_creado')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    # Historial y reactivación
    fue_reactivado = models.BooleanField(default=False)
    reactivado_desde = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, 
                                       related_name='reactivaciones')
    
    class Meta:
        verbose_name = "Personal Temporal"
        verbose_name_plural = "Personal Temporal"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        estado = "Activo" if self.activo else "Inactivo"
        return f"{self.nombre} - {self.area.nombre} ({estado})"
    
    def debe_desactivarse_automaticamente(self):
        """Verifica si debe desactivarse automáticamente por fecha"""
        if not self.tiempo_indefinido and self.fecha_fin and self.activo:
            return timezone.now() >= self.fecha_fin
        return False
    
    def esta_activo_en_fecha(self, fecha):
        """Verifica si está activo en una fecha específica"""
        if not self.activo:
            return False
        
        if fecha < self.fecha_inicio:
            return False
            
        if not self.tiempo_indefinido and self.fecha_fin:
            return fecha <= self.fecha_fin
            
        return True
    
    def desactivar(self, motivo="", automatico=False):
        """Desactiva el personal temporal y registra en historial"""
        self.activo = False
        self.fecha_desactivacion = timezone.now()
        self.motivo_desactivacion = motivo
        self.desactivado_automaticamente = automatico
        self.save()
        
        # Crear entrada en historial
        HistorialPersonalTemporal.objects.create(
            personal_temporal=self,
            accion='desactivacion',
            motivo=motivo,
            automatico=automatico,
            usuario_accion=None if automatico else getattr(self, '_usuario_accion', None)
        )


class HistorialPersonalTemporal(models.Model):
    ACCIONES = [
        ('creacion', 'Creación'),
        ('reactivacion', 'Reactivación'),
        ('desactivacion', 'Desactivación'),
    ]
    
    personal_temporal = models.ForeignKey(PersonalTemporal, on_delete=models.CASCADE, 
                                        related_name='historial')
    accion = models.CharField(max_length=20, choices=ACCIONES)
    fecha = models.DateTimeField(auto_now_add=True)
    motivo = models.TextField(blank=True)
    automatico = models.BooleanField(default=False)
    usuario_accion = models.ForeignKey(Usuarios, null=True, blank=True, on_delete=models.SET_NULL)
    
    class Meta:
        verbose_name = "Historial Personal Temporal"
        ordering = ['-fecha']