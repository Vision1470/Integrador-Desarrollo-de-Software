# Generated by Django 5.1.3 on 2025-06-15 10:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('login', '0005_alter_usuarios_areaespecialidad_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='fortaleza',
            options={'ordering': ['area__nombre', 'nombre'], 'verbose_name': 'Fortaleza', 'verbose_name_plural': 'Fortalezas'},
        ),
        migrations.AddField(
            model_name='fortaleza',
            name='area',
            field=models.ForeignKey(blank=True, help_text='Área hospitalaria donde se aplica principalmente esta fortaleza', null=True, on_delete=django.db.models.deletion.PROTECT, to='login.areaespecialidad'),
        ),
    ]
