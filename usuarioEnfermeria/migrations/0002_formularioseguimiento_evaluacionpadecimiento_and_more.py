# Generated by Django 5.1.3 on 2025-01-19 02:27

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarioDoctor', '0005_alter_padecimiento_options_padecimiento_activo'),
        ('usuarioEnfermeria', '0001_initial'),
        ('usuarioJefa', '0003_alter_medicamento_gramaje'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FormularioSeguimiento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_registro', models.DateTimeField(auto_now_add=True)),
                ('notas_generales', models.TextField(blank=True)),
                ('enfermero', models.ForeignKey(limit_choices_to={'tipoUsuario__in': ['EN', 'JP']}, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('paciente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='usuarioJefa.paciente')),
            ],
            options={
                'ordering': ['-fecha_registro'],
            },
        ),
        migrations.CreateModel(
            name='EvaluacionPadecimiento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado', models.CharField(choices=[('M', 'Mejoró'), ('E', 'Empeoró'), ('S', 'Sin cambios')], max_length=1)),
                ('notas', models.TextField(blank=True)),
                ('padecimiento', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='usuarioDoctor.recetapadecimiento')),
                ('formulario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='usuarioEnfermeria.formularioseguimiento')),
            ],
        ),
        migrations.CreateModel(
            name='CuidadoFaltante',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('motivo', models.TextField()),
                ('fecha_reportado', models.DateTimeField(auto_now_add=True)),
                ('cuidado', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='usuarioDoctor.recetacuidado')),
                ('formulario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='usuarioEnfermeria.formularioseguimiento')),
            ],
        ),
    ]
