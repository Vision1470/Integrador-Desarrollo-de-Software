# Generated by Django 5.1.3 on 2025-01-17 08:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarioDoctor', '0004_remove_cuidado_cantidad_material_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='padecimiento',
            options={'ordering': ['nombre']},
        ),
        migrations.AddField(
            model_name='padecimiento',
            name='activo',
            field=models.BooleanField(default=True),
        ),
    ]
