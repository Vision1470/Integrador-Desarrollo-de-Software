# Generated by Django 5.1.3 on 2025-01-16 23:23

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarioDoctor', '0002_remove_detallereceta_dosis_and_more'),
        ('usuarioJefa', '0003_alter_medicamento_gramaje'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='padecimientodiagnostico',
            options={},
        ),
        migrations.RemoveField(
            model_name='padecimientodiagnostico',
            name='comentarios',
        ),
        migrations.CreateModel(
            name='Cuidado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200)),
                ('descripcion', models.TextField()),
                ('requiere_material', models.BooleanField(default=False)),
                ('cantidad_material', models.PositiveIntegerField(blank=True, null=True)),
                ('material_requerido', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='usuarioJefa.instrumento')),
            ],
            options={
                'verbose_name': 'Cuidado',
                'verbose_name_plural': 'Cuidados',
            },
        ),
        migrations.CreateModel(
            name='CuidadoPadecimiento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('completado', models.BooleanField(default=False)),
                ('fecha_completado', models.DateTimeField(blank=True, null=True)),
                ('completado_por', models.ForeignKey(blank=True, limit_choices_to={'tipoUsuario': 'EN'}, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('cuidado', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='usuarioDoctor.cuidado')),
                ('padecimiento_diagnostico', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='usuarioDoctor.padecimientodiagnostico')),
            ],
        ),
        migrations.AddField(
            model_name='padecimientodiagnostico',
            name='cuidados',
            field=models.ManyToManyField(through='usuarioDoctor.CuidadoPadecimiento', to='usuarioDoctor.cuidado'),
        ),
    ]
