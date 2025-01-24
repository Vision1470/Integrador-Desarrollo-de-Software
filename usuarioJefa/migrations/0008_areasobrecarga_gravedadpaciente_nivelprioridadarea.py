# Generated by Django 5.1.3 on 2025-01-24 10:34

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('login', '0004_alter_usuarios_tipousuario'),
        ('usuarioJefa', '0007_historialcambios'),
    ]

    operations = [
        migrations.CreateModel(
            name='AreaSobrecarga',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_inicio', models.DateTimeField(auto_now_add=True)),
                ('fecha_fin', models.DateTimeField(blank=True, null=True)),
                ('activo', models.BooleanField(default=True)),
                ('area', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='login.areaespecialidad')),
            ],
            options={
                'verbose_name': 'Área en Sobrecarga',
                'verbose_name_plural': 'Áreas en Sobrecarga',
            },
        ),
        migrations.CreateModel(
            name='GravedadPaciente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nivel_gravedad', models.IntegerField(choices=[(1, 'Baja'), (2, 'Media'), (3, 'Alta')], validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(3)])),
                ('fecha_asignacion', models.DateTimeField(auto_now_add=True)),
                ('paciente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='usuarioJefa.paciente')),
            ],
            options={
                'verbose_name': 'Gravedad de Paciente',
                'verbose_name_plural': 'Gravedades de Pacientes',
            },
        ),
        migrations.CreateModel(
            name='NivelPrioridadArea',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nivel_prioridad', models.IntegerField(help_text='Nivel de prioridad del área (1-5)', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('area', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='login.areaespecialidad')),
            ],
            options={
                'verbose_name': 'Nivel de Prioridad de Área',
                'verbose_name_plural': 'Niveles de Prioridad de Áreas',
            },
        ),
    ]
