from django.db import migrations, models

def set_ingreso_number_enfermeria(apps, schema_editor):
    # Obtenemos los modelos históricos
    SeguimientoCuidados = apps.get_model('usuarioEnfermeria', 'SeguimientoCuidados')
    FormularioSeguimiento = apps.get_model('usuarioEnfermeria', 'FormularioSeguimiento')
    
    # Actualizar seguimientos
    for seguimiento in SeguimientoCuidados.objects.all():
        seguimiento.numero_ingreso = seguimiento.paciente.numero_ingresos
        seguimiento.save()
    
    # Actualizar formularios
    for formulario in FormularioSeguimiento.objects.all():
        formulario.numero_ingreso = formulario.paciente.numero_ingresos
        formulario.save()

class Migration(migrations.Migration):
    dependencies = [
        ('usuarioEnfermeria', '0003_medicamentofaltante'),  # Necesitarás poner el nombre correcto
    ]

    operations = [
        # Añadir campo a SeguimientoCuidados
        migrations.AddField(
            model_name='seguimientocuidados',
            name='numero_ingreso',
            field=models.PositiveIntegerField(default=1),
        ),
        # Añadir campo a FormularioSeguimiento
        migrations.AddField(
            model_name='formularioseguimiento',
            name='numero_ingreso',
            field=models.PositiveIntegerField(default=1),
        ),
        # Ejecutar función para llenar los campos
        migrations.RunPython(set_ingreso_number_enfermeria),
    ]