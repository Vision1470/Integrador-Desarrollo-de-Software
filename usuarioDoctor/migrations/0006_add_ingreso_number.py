from django.db import migrations, models

def set_ingreso_number_doctor(apps, schema_editor):
    # Obtenemos los modelos históricos
    Diagnostico = apps.get_model('usuarioDoctor', 'Diagnostico')
    Receta = apps.get_model('usuarioDoctor', 'Receta')
    
    # Actualizar diagnósticos
    for diagnostico in Diagnostico.objects.all():
        diagnostico.numero_ingreso = diagnostico.paciente.numero_ingresos
        diagnostico.save()
    
    # Actualizar recetas
    for receta in Receta.objects.all():
        receta.numero_ingreso = receta.paciente.numero_ingresos
        receta.save()

class Migration(migrations.Migration):
    dependencies = [
        ('usuarioDoctor', '0005_alter_padecimiento_options_padecimiento_activo'),  # Necesitarás poner el nombre correcto
    ]

    operations = [
        # Añadir campo a Diagnostico
        migrations.AddField(
            model_name='diagnostico',
            name='numero_ingreso',
            field=models.PositiveIntegerField(default=1),
        ),
        # Añadir campo a Receta
        migrations.AddField(
            model_name='receta',
            name='numero_ingreso',
            field=models.PositiveIntegerField(default=1),
        ),
        # Ejecutar función para llenar los campos
        migrations.RunPython(set_ingreso_number_doctor),
    ]