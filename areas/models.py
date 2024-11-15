
from django.db import models

# Create your models here.

class area(models.Model):
    nombre = models.CharField(max_length=200)
    def __str__(self):
        return self.nombre

class actividad(models.Model):
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    area = models.ForeignKey(area, on_delete=models.CASCADE)
    def __str__(self):
        return self.titulo
    
