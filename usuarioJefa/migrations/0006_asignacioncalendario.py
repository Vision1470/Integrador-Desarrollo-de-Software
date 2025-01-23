# Generated by Django 5.1.3 on 2025-01-23 23:07

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('login', '0001_initial'),
        ('usuarioJefa', '0005_historialcompletopaciente'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AsignacionCalendario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_inicio', models.DateField()),
                ('fecha_fin', models.DateField()),
                ('bimestre', models.IntegerField()),
                ('year', models.IntegerField()),
                ('activo', models.BooleanField(default=True)),
                ('area', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='login.areaespecialidad')),
                ('enfermero', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('enfermero', 'fecha_inicio', 'fecha_fin')},
            },
        ),
    ]
