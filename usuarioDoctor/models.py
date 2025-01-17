from django.db import models
from django.utils import timezone
from usuarioJefa.models import Paciente
from login.models import Usuarios
from decimal import Decimal

class Padecimiento(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(null=True, blank=True)
    activo = models.BooleanField(default=True)  # Para poder desactivar padecimientos sin eliminarlos
    
    class Meta:
        ordering = ['nombre']  # Para que aparezcan ordenados alfabéticamente
    
    def __str__(self):
        return self.nombre

class Cuidado(models.Model):
    nombre = models.CharField(max_length=200)
    
    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Cuidado'
        verbose_name_plural = 'Cuidados'

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
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='recetas_doctor')
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

class RecetaPadecimiento(models.Model):
    receta = models.ForeignKey(Receta, on_delete=models.CASCADE, related_name='padecimientos')
    padecimiento = models.ForeignKey(Padecimiento, on_delete=models.PROTECT)
    nivel_gravedad = models.IntegerField(choices=Diagnostico.NIVELES_GRAVEDAD)
    
    def __str__(self):
        return f"{self.padecimiento} - {self.get_nivel_gravedad_display()}"

class RecetaCuidado(models.Model):
    receta = models.ForeignKey(Receta, on_delete=models.CASCADE, related_name='cuidados')
    cuidado = models.ForeignKey(Cuidado, on_delete=models.PROTECT)
    completado = models.BooleanField(default=False)
    fecha_completado = models.DateTimeField(null=True, blank=True)
    completado_por = models.ForeignKey(
        'login.Usuarios',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={'tipoUsuario': 'EN'}
    )


class DetalleReceta(models.Model):
    UNIDADES_MEDIDA = [
        ('TAB', 'Tabletas'),
        ('ML', 'Mililitros'),
        ('MG', 'Miligramos'),
        ('CAP', 'Cápsulas'),
        ('GOT', 'Gotas'),
        ('AMP', 'Ampolletas'),
    ]

    receta = models.ForeignKey(Receta, on_delete=models.CASCADE, related_name='detalles')
    medicamento = models.ForeignKey('usuarioJefa.Medicamento', on_delete=models.PROTECT)
    
    # Dosis
    cantidad_por_toma = models.DecimalField(max_digits=5, decimal_places=2)
    unidad_medida = models.CharField(max_length=3, choices=UNIDADES_MEDIDA)
    
    # Horario
    frecuencia_horas = models.PositiveIntegerField(help_text="Cada cuántas horas")
    dias_tratamiento = models.PositiveIntegerField()
    
    instrucciones = models.TextField()
    descripcion_opcional = models.TextField(blank=True)
    hay_existencia = models.BooleanField(default=True)

    
    def calcular_cantidad_total(self):
        tomas_por_dia = Decimal('24') / Decimal(str(self.frecuencia_horas))
        return self.cantidad_por_toma * tomas_por_dia * Decimal(str(self.dias_tratamiento))

    def save(self, *args, **kwargs):
        cantidad_necesaria = self.calcular_cantidad_total()
        if self.medicamento.cantidad_disponible < cantidad_necesaria:
            self.hay_existencia = False
        super().save(*args, **kwargs)
        
        # Actualizar stock del medicamento
        if self.hay_existencia:
            self.medicamento.cantidad_disponible -= cantidad_necesaria
            self.medicamento.save()

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

class PadecimientoDiagnostico(models.Model):
    diagnostico = models.ForeignKey(Diagnostico, on_delete=models.CASCADE, related_name='padecimientos')
    padecimiento = models.ForeignKey(Padecimiento, on_delete=models.PROTECT)
    nivel_gravedad = models.IntegerField(choices=Diagnostico.NIVELES_GRAVEDAD)
    cuidados = models.ManyToManyField(Cuidado, through='CuidadoPadecimiento')

class CuidadoPadecimiento(models.Model):
    padecimiento_diagnostico = models.ForeignKey(PadecimientoDiagnostico, on_delete=models.CASCADE)
    cuidado = models.ForeignKey(Cuidado, on_delete=models.PROTECT)
    completado = models.BooleanField(default=False)
    fecha_completado = models.DateTimeField(null=True, blank=True)
    completado_por = models.ForeignKey(
        Usuarios,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={'tipoUsuario': 'EN'}
    )