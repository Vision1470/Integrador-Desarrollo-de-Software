from django.db import models
from django.utils import timezone
from login.models import Usuarios
from usuarioJefa.models import Paciente
from usuarioDoctor.models import RecetaPadecimiento, RecetaCuidado, DetalleReceta

class SeguimientoCuidados(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    registrado_por = models.ForeignKey(
        Usuarios,
        on_delete=models.PROTECT,
        limit_choices_to={'tipoUsuario__in': ['EN', 'JP']}
    )

    class Meta:
        verbose_name = "Seguimiento de Cuidados"
        verbose_name_plural = "Seguimientos de Cuidados"

class RegistroCuidado(models.Model):
    seguimiento = models.ForeignKey(SeguimientoCuidados, on_delete=models.CASCADE)
    cuidado = models.ForeignKey(RecetaCuidado, on_delete=models.CASCADE)
    completado = models.BooleanField(default=False)
    fecha_completado = models.DateTimeField(null=True, blank=True)
    notas = models.TextField(blank=True)

class RegistroMedicamento(models.Model):
    seguimiento = models.ForeignKey(SeguimientoCuidados, on_delete=models.CASCADE)
    medicamento = models.ForeignKey(DetalleReceta, on_delete=models.CASCADE)
    administrado = models.BooleanField(default=False)
    fecha_administracion = models.DateTimeField(null=True, blank=True)
    notas = models.TextField(blank=True)

class FormularioSeguimiento(models.Model):
    ESTADO_PADECIMIENTO = [
        ('M', 'Mejoró'),
        ('E', 'Empeoró'),
        ('S', 'Sin cambios')
    ]

    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    enfermero = models.ForeignKey(
        Usuarios,
        on_delete=models.PROTECT,
        limit_choices_to={'tipoUsuario__in': ['EN', 'JP']}
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)
    notas_generales = models.TextField(blank=True)

    class Meta:
        ordering = ['-fecha_registro']

class EvaluacionPadecimiento(models.Model):
    formulario = models.ForeignKey(FormularioSeguimiento, on_delete=models.CASCADE)
    padecimiento = models.ForeignKey(RecetaPadecimiento, on_delete=models.CASCADE)
    estado = models.CharField(max_length=1, choices=FormularioSeguimiento.ESTADO_PADECIMIENTO)
    notas = models.TextField(blank=True)

class CuidadoFaltante(models.Model):
    formulario = models.ForeignKey(FormularioSeguimiento, on_delete=models.CASCADE)
    cuidado = models.ForeignKey('usuarioDoctor.RecetaCuidado', on_delete=models.CASCADE)
    motivo = models.TextField()
    fecha_reportado = models.DateTimeField(auto_now_add=True)

class MedicamentoFaltante(models.Model):
    formulario = models.ForeignKey(FormularioSeguimiento, on_delete=models.CASCADE)
    medicamento = models.ForeignKey('usuarioDoctor.DetalleReceta', on_delete=models.CASCADE)
    motivo = models.TextField()
    fecha_reportado = models.DateTimeField(auto_now_add=True)