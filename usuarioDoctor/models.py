from django.db import models
from django.utils import timezone
from usuarioJefa.models import Paciente
from login.models import Usuarios

class Diagnostico(models.Model):
    NIVELES_GRAVEDAD = [
        (1, 'Leve'),
        (2, 'Moderado'),
        (3, 'Grave')
    ]

    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='diagnosticos')
    doctor = models.ForeignKey(
        Usuarios, 
        on_delete=models.PROTECT, 
        limit_choices_to={'tipoUsuario': 'DR'}
    )
    descripcion = models.TextField()
    cuidados_especificos = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    aprobado_por_jefa = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['-fecha_creacion']

class HistorialDiagnostico(models.Model):
    diagnostico = models.ForeignKey(Diagnostico, on_delete=models.CASCADE)
    doctor_modificador = models.ForeignKey(
        Usuarios, 
        on_delete=models.PROTECT,
        limit_choices_to={'tipoUsuario': 'DR'}
    )
    fecha_modificacion = models.DateTimeField(auto_now_add=True)
    cambios_realizados = models.TextField()
    motivo_cambio = models.TextField()

class Receta(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='recetas_doctor')  # Cambiado de 'recetas' a 'recetas_doctor'
    doctor = models.ForeignKey(
        Usuarios, 
        on_delete=models.PROTECT,
        limit_choices_to={'tipoUsuario': 'DR'}
    )
    diagnostico = models.ForeignKey(Diagnostico, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    aprobado_por_jefa = models.BooleanField(default=False)
    activa = models.BooleanField(default=True)

class DetalleReceta(models.Model):
    receta = models.ForeignKey(Receta, on_delete=models.CASCADE, related_name='detalles')
    medicamento = models.ForeignKey('usuarioJefa.Medicamento', on_delete=models.PROTECT)  # Asumiendo que existirá este modelo
    dosis = models.CharField(max_length=100)
    horario = models.CharField(max_length=200)
    instrucciones = models.TextField()
    descripcion_opcional = models.TextField(blank=True)
    hay_existencia = models.BooleanField(default=True)

class HistorialReceta(models.Model):
    receta = models.ForeignKey(Receta, on_delete=models.CASCADE)
    doctor_modificador = models.ForeignKey(
        Usuarios, 
        on_delete=models.PROTECT,
        limit_choices_to={'tipoUsuario': 'DR'}
    )
    fecha_modificacion = models.DateTimeField(auto_now_add=True)
    cambios_realizados = models.TextField()
    motivo_cambio = models.TextField()
    medicamento_no_efectivo = models.BooleanField(default=False)

class Padecimiento(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    
    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Padecimiento'
        verbose_name_plural = 'Padecimientos'

class PadecimientoDiagnostico(models.Model):
    NIVELES_GRAVEDAD = [
        (1, 'Leve'),
        (2, 'Moderado'),
        (3, 'Grave')
    ]

    diagnostico = models.ForeignKey(Diagnostico, on_delete=models.CASCADE, related_name='padecimientos')
    padecimiento = models.ForeignKey(Padecimiento, on_delete=models.PROTECT)
    nivel_gravedad = models.IntegerField(choices=NIVELES_GRAVEDAD)
    comentarios = models.TextField(blank=True)

    def __str__(self):
        return f"{self.padecimiento.nombre} - Nivel {self.nivel_gravedad}"

    class Meta:
        verbose_name = 'Padecimiento en Diagnóstico'
        verbose_name_plural = 'Padecimientos en Diagnósticos'