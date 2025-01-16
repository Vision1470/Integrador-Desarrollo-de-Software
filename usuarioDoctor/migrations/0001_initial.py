# Generated by Django 5.1.3 on 2025-01-16 05:26

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('usuarioJefa', '0002_compuesto_instrumento_alter_recetamedica_paciente_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Padecimiento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200)),
                ('descripcion', models.TextField()),
            ],
            options={
                'verbose_name': 'Padecimiento',
                'verbose_name_plural': 'Padecimientos',
            },
        ),
        migrations.CreateModel(
            name='Diagnostico',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descripcion', models.TextField()),
                ('cuidados_especificos', models.TextField()),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_modificacion', models.DateTimeField(auto_now=True)),
                ('aprobado_por_jefa', models.BooleanField(default=False)),
                ('activo', models.BooleanField(default=True)),
                ('doctor', models.ForeignKey(limit_choices_to={'tipoUsuario': 'DR'}, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('paciente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='diagnosticos', to='usuarioJefa.paciente')),
            ],
            options={
                'ordering': ['-fecha_creacion'],
            },
        ),
        migrations.CreateModel(
            name='HistorialDiagnostico',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_modificacion', models.DateTimeField(auto_now_add=True)),
                ('cambios_realizados', models.TextField()),
                ('motivo_cambio', models.TextField()),
                ('diagnostico', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='usuarioDoctor.diagnostico')),
                ('doctor_modificador', models.ForeignKey(limit_choices_to={'tipoUsuario': 'DR'}, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PadecimientoDiagnostico',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nivel_gravedad', models.IntegerField(choices=[(1, 'Leve'), (2, 'Moderado'), (3, 'Grave')])),
                ('comentarios', models.TextField(blank=True)),
                ('diagnostico', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='padecimientos', to='usuarioDoctor.diagnostico')),
                ('padecimiento', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='usuarioDoctor.padecimiento')),
            ],
            options={
                'verbose_name': 'Padecimiento en Diagnóstico',
                'verbose_name_plural': 'Padecimientos en Diagnósticos',
            },
        ),
        migrations.CreateModel(
            name='Receta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_modificacion', models.DateTimeField(auto_now=True)),
                ('aprobado_por_jefa', models.BooleanField(default=False)),
                ('activa', models.BooleanField(default=True)),
                ('diagnostico', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='usuarioDoctor.diagnostico')),
                ('doctor', models.ForeignKey(limit_choices_to={'tipoUsuario': 'DR'}, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('paciente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recetas_doctor', to='usuarioJefa.paciente')),
            ],
        ),
        migrations.CreateModel(
            name='HistorialReceta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_modificacion', models.DateTimeField(auto_now_add=True)),
                ('cambios_realizados', models.TextField()),
                ('motivo_cambio', models.TextField()),
                ('medicamento_no_efectivo', models.BooleanField(default=False)),
                ('doctor_modificador', models.ForeignKey(limit_choices_to={'tipoUsuario': 'DR'}, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('receta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='usuarioDoctor.receta')),
            ],
        ),
        migrations.CreateModel(
            name='DetalleReceta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dosis', models.CharField(max_length=100)),
                ('horario', models.CharField(max_length=200)),
                ('instrucciones', models.TextField()),
                ('descripcion_opcional', models.TextField(blank=True)),
                ('hay_existencia', models.BooleanField(default=True)),
                ('medicamento', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='usuarioJefa.medicamento')),
                ('receta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='detalles', to='usuarioDoctor.receta')),
            ],
        ),
    ]
