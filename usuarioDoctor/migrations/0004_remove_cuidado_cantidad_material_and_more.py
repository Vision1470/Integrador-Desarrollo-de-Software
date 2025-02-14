# Generated by Django 5.1.3 on 2025-01-17 02:15

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarioDoctor', '0003_alter_padecimientodiagnostico_options_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cuidado',
            name='cantidad_material',
        ),
        migrations.RemoveField(
            model_name='cuidado',
            name='descripcion',
        ),
        migrations.RemoveField(
            model_name='cuidado',
            name='material_requerido',
        ),
        migrations.RemoveField(
            model_name='cuidado',
            name='requiere_material',
        ),
        migrations.AlterField(
            model_name='padecimiento',
            name='descripcion',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='RecetaCuidado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('completado', models.BooleanField(default=False)),
                ('fecha_completado', models.DateTimeField(blank=True, null=True)),
                ('completado_por', models.ForeignKey(blank=True, limit_choices_to={'tipoUsuario': 'EN'}, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('cuidado', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='usuarioDoctor.cuidado')),
                ('receta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cuidados', to='usuarioDoctor.receta')),
            ],
        ),
        migrations.CreateModel(
            name='RecetaPadecimiento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nivel_gravedad', models.IntegerField(choices=[(1, 'Leve'), (2, 'Moderado'), (3, 'Grave')])),
                ('padecimiento', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='usuarioDoctor.padecimiento')),
                ('receta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='padecimientos', to='usuarioDoctor.receta')),
            ],
        ),
    ]
