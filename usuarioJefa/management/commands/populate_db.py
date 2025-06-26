from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import datetime, timedelta
import random

from login.models import Usuarios, AreaEspecialidad, Fortaleza
from usuarioJefa.models import (
    Paciente, Compuesto, Medicamento, Instrumento, 
    GravedadPaciente
)


class Command(BaseCommand):
    help = 'Poblar la base de datos con enfermeros, pacientes, medicamentos e instrumentos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--enfermeros',
            type=int,
            default=30,
            help='Número de enfermeros a crear (default: 30)',
        )
        parser.add_argument(
            '--pacientes',
            type=int,
            default=60,
            help='Número de pacientes a crear (default: 60)',
        )
        parser.add_argument(
            '--limpiar',
            action='store_true',
            help='Limpiar datos existentes antes de crear',
        )

    def handle(self, *args, **options):
        num_enfermeros = options['enfermeros']
        num_pacientes = options['pacientes']
        limpiar = options['limpiar']
        
        self.stdout.write(
            self.style.SUCCESS(f'🚀 Creando {num_enfermeros} enfermeros y {num_pacientes} pacientes...')
        )
        
        try:
            with transaction.atomic():
                # Limpiar datos existentes si se solicita
                if limpiar:
                    self.limpiar_datos_existentes()
                
                # Validar que existen áreas y fortalezas
                areas = list(AreaEspecialidad.objects.all())
                fortalezas = list(Fortaleza.objects.all())
                
                if not areas:
                    self.stdout.write(
                        self.style.ERROR('❌ No hay áreas creadas. Crea áreas primero.')
                    )
                    return
                
                if not fortalezas:
                    self.stdout.write(
                        self.style.WARNING('⚠️ No hay fortalezas creadas. Continuando sin asignar fortalezas.')
                    )
                
                # Crear solo lo solicitado
                enfermeros = self.crear_enfermeros(areas, fortalezas, num_enfermeros)
                self.crear_medicamentos_instrumentos()
                pacientes = self.crear_pacientes(areas, num_pacientes)
                
                self.stdout.write(
                    self.style.SUCCESS('✅ Población completada exitosamente!')
                )
                self.mostrar_resumen(areas, enfermeros, pacientes)
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error al poblar base de datos: {str(e)}')
            )
            import traceback
            traceback.print_exc()

    def limpiar_datos_existentes(self):
        """Limpia solo enfermeros y pacientes de prueba"""
        self.stdout.write('🧹 Limpiando datos existentes...')
        
        # Eliminar enfermeros de prueba (que empiecen con 'enf_test_' o 'enf_')
        enfermeros_eliminados = Usuarios.objects.filter(
            tipoUsuario='EN',
            username__startswith='enf_'
        ).delete()[0]
        
        # Eliminar pacientes de prueba
        pacientes_eliminados = Paciente.objects.filter(
            nombres__startswith='Paciente_'
        ).delete()[0]
        
        self.stdout.write(f'  ✓ {enfermeros_eliminados} enfermeros eliminados')
        self.stdout.write(f'  ✓ {pacientes_eliminados} pacientes eliminados')

    def crear_enfermeros(self, areas, fortalezas, cantidad):
        """Crear enfermeros"""
        self.stdout.write(f'👨‍⚕️ Creando {cantidad} enfermeros...')
        
        nombres = [
            'Ana', 'Carlos', 'Lucía', 'Miguel', 'Elena', 'David',
            'Carmen', 'Alejandro', 'Isabel', 'Roberto', 'Patricia',
            'Francisco', 'Beatriz', 'Javier', 'Cristina', 'Sergio',
            'María', 'José', 'Laura', 'Antonio', 'Sofía', 'Manuel',
            'Andrea', 'Fernando', 'Mónica', 'Ricardo', 'Diana',
            'Raúl', 'Natalia', 'Esteban', 'Claudia', 'Óscar',
            'Valeria', 'Iván', 'Paola', 'Jorge', 'Camila', 'Andrés',
            'Lorena', 'Gabriel', 'Marcela', 'Felipe', 'Adriana'
        ]
        
        apellidos = [
            'García', 'Rodríguez', 'González', 'Fernández', 'López',
            'Martínez', 'Sánchez', 'Pérez', 'Gómez', 'Martín',
            'Jiménez', 'Ruiz', 'Hernández', 'Díaz', 'Moreno',
            'Álvarez', 'Romero', 'Torres', 'Vargas', 'Castillo',
            'Ortega', 'Ramos', 'Delgado', 'Castro', 'Herrera'
        ]
        
        enfermeros = []
        contador_exitosos = 0
        
        for i in range(cantidad):
            # Generar datos aleatorios
            nombre = random.choice(nombres)
            apellido = random.choice(apellidos)
            username = f'enf_test_{i+1:03d}'
            
            # Verificar que no existe
            if Usuarios.objects.filter(username=username).exists():
                self.stdout.write(f'  ⚠️ Usuario {username} ya existe, saltando...')
                continue
            
            try:
                # Asignar área aleatoria (70% probabilidad de tener especialidad)
                area_especialidad = random.choice(areas) if random.random() < 0.7 else None
                
                # Crear enfermero
                enfermero = Usuarios.objects.create(
                    username=username,
                    first_name=nombre,
                    apellidos=apellido,
                    tipoUsuario='EN',
                    edad=random.randint(23, 55),
                    fechaNacimiento=f'{random.randint(1970, 2000)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}',
                    areaEspecialidad=area_especialidad,
                    estaActivo=True,
                    primerIngreso=False,
                    email=f'{username}@hospital.com'
                )
                
                # Establecer contraseña
                enfermero.set_password('123456')
                
                # Asignar fortalezas aleatorias (1-4 fortalezas)
                if fortalezas:
                    num_fortalezas = random.randint(1, min(4, len(fortalezas)))
                    fortalezas_asignadas = random.sample(fortalezas, num_fortalezas)
                    enfermero.fortalezas.set(fortalezas_asignadas)
                
                enfermero.save()
                enfermeros.append(enfermero)
                contador_exitosos += 1
                
                especialidad_txt = area_especialidad.nombre if area_especialidad else "Sin especialidad"
                self.stdout.write(f'  ✓ {username}: {nombre} {apellido} ({especialidad_txt})')
                
            except Exception as e:
                self.stdout.write(f'  ❌ Error creando {username}: {str(e)}')
                continue
        
        self.stdout.write(f'  ✅ {contador_exitosos} enfermeros creados exitosamente')
        return enfermeros

    def crear_medicamentos_instrumentos(self):
        """Crear medicamentos e instrumentos"""
        self.stdout.write('💊 Creando medicamentos e instrumentos...')
        
        # Crear compuestos si no existen
        compuestos_data = [
            'Paracetamol', 'Ibuprofeno', 'Aspirina', 'Amoxicilina',
            'Diclofenaco', 'Omeprazol', 'Losartán', 'Metformina',
            'Captopril', 'Atorvastatina', 'Ranitidina', 'Loratadina'
        ]
        
        compuestos = []
        for nombre in compuestos_data:
            compuesto, created = Compuesto.objects.get_or_create(
                nombre=nombre,
                defaults={'descripcion': f'Compuesto activo {nombre}'}
            )
            compuestos.append(compuesto)
            if created:
                self.stdout.write(f'  ✓ Compuesto: {nombre}')
        
        # Crear medicamentos
        medicamentos_data = [
            ('Paracetamol 500mg', '500', [0], random.randint(100, 500)),
            ('Ibuprofeno 400mg', '400', [1], random.randint(80, 300)),
            ('Aspirina 100mg', '100', [2], random.randint(200, 400)),
            ('Amoxicilina 500mg', '500', [3], random.randint(50, 150)),
            ('Diclofenaco 50mg', '50', [4], random.randint(60, 200)),
            ('Omeprazol 20mg', '20', [5], random.randint(100, 250)),
            ('Losartán 50mg', '50', [6], random.randint(80, 180)),
            ('Metformina 850mg', '850', [7], random.randint(150, 300)),
            ('Captopril 25mg', '25', [8], random.randint(90, 200)),
            ('Atorvastatina 20mg', '20', [9], random.randint(70, 150)),
        ]
        
        contador_medicamentos = 0
        for nombre, gramaje, compuestos_indices, cantidad in medicamentos_data:
            try:
                medicamento, created = Medicamento.objects.get_or_create(
                    nombre=nombre,
                    gramaje=gramaje,
                    defaults={'cantidad_disponible': cantidad}
                )
                if created:
                    medicamento.compuestos.set([compuestos[i] for i in compuestos_indices])
                    contador_medicamentos += 1
                    self.stdout.write(f'  ✓ Medicamento: {nombre} ({cantidad} unidades)')
            except Exception as e:
                self.stdout.write(f'  ❌ Error creando medicamento {nombre}: {str(e)}')
        
        # Crear instrumentos
        instrumentos_data = [
            ('Tensiómetro Digital', random.randint(10, 20), 'Monitor de presión arterial automático'),
            ('Termómetro Infrarrojo', random.randint(20, 35), 'Termómetro sin contacto'),
            ('Oxímetro de Pulso', random.randint(25, 40), 'Medidor de saturación de oxígeno'),
            ('Estetoscopio', random.randint(15, 25), 'Estetoscopio clínico profesional'),
            ('Jeringas 5ml', random.randint(400, 600), 'Jeringas desechables de 5ml'),
            ('Gasas Estériles', random.randint(150, 250), 'Gasas estériles 10x10cm'),
            ('Vendas Elásticas', random.randint(80, 120), 'Vendas elásticas de diferentes tamaños'),
            ('Catéteres IV', random.randint(50, 100), 'Catéteres intravenosos calibre 18-22'),
            ('Guantes Latex', random.randint(500, 800), 'Guantes de látex estériles'),
            ('Mascarillas N95', random.randint(100, 200), 'Mascarillas de protección respiratoria'),
        ]
        
        contador_instrumentos = 0
        for nombre, cantidad, especificaciones in instrumentos_data:
            try:
                instrumento, created = Instrumento.objects.get_or_create(
                    nombre=nombre,
                    defaults={
                        'cantidad': cantidad,
                        'especificaciones': especificaciones
                    }
                )
                if created:
                    contador_instrumentos += 1
                    self.stdout.write(f'  ✓ Instrumento: {nombre} ({cantidad} unidades)')
            except Exception as e:
                self.stdout.write(f'  ❌ Error creando instrumento {nombre}: {str(e)}')
        
        self.stdout.write(f'  ✅ {contador_medicamentos} medicamentos y {contador_instrumentos} instrumentos creados')

    def crear_pacientes(self, areas, cantidad):
        """Crear pacientes con diferentes niveles de gravedad"""
        self.stdout.write(f'🏥 Creando {cantidad} pacientes...')
        
        # Validar que hay doctores disponibles
        doctores = list(Usuarios.objects.filter(tipoUsuario='DR', estaActivo=True))
        if not doctores:
            self.stdout.write(self.style.ERROR('❌ No hay doctores disponibles. Los pacientes se crearán sin doctor asignado.'))
        
        nombres_masculinos = [
            'José', 'Antonio', 'Manuel', 'Francisco', 'Juan', 'Luis',
            'Miguel', 'Jesús', 'Rafael', 'Carlos', 'Andrés', 'Ricardo',
            'Fernando', 'Eduardo', 'Ramón', 'Alberto', 'Enrique', 'Vicente',
            'Ángel', 'Pablo', 'Álvaro', 'Diego', 'Sergio', 'Mario'
        ]
        
        nombres_femeninos = [
            'María', 'Carmen', 'Pilar', 'Dolores', 'Mercedes', 'Antonia',
            'Francisca', 'Isabel', 'Ana', 'Rosario', 'Teresa', 'Concepción',
            'Esperanza', 'Purificación', 'Amparo', 'Gloria', 'Remedios',
            'Cristina', 'Silvia', 'Beatriz', 'Lucía', 'Elena', 'Patricia'
        ]
        
        apellidos = [
            'García', 'Rodríguez', 'González', 'Fernández', 'López',
            'Martínez', 'Sánchez', 'Pérez', 'Gómez', 'Martín',
            'Jiménez', 'Ruiz', 'Hernández', 'Díaz', 'Moreno',
            'Álvarez', 'Romero', 'Torres', 'Vargas', 'Castillo',
            'Navarro', 'Ramos', 'Gil', 'Serrano', 'Blanco'
        ]
        
        pacientes = []
        contador_exitosos = 0
        
        for i in range(cantidad):
            try:
                # Generar datos básicos
                sexo = random.choice(['M', 'F'])
                if sexo == 'M':
                    nombre = random.choice(nombres_masculinos)
                else:
                    nombre = random.choice(nombres_femeninos)
                
                apellido = random.choice(apellidos)
                segundo_apellido = random.choice(apellidos)
                
                # Generar NSS único
                nss = f'SS{i+1:04d}{random.randint(1000, 9999)}'
                
                # Verificar que no existe
                if Paciente.objects.filter(num_seguridad_social=nss).exists():
                    nss = f'SS{i+1:04d}{random.randint(10000, 99999)}'
                
                # Generar edad y fecha de nacimiento
                edad = random.randint(18, 85)
                fecha_nacimiento = datetime.now().date() - timedelta(days=edad*365 + random.randint(0, 365))
                
                # Asignar área aleatoria
                area = random.choice(areas)
                
                # Asignar doctor si hay disponibles
                doctor = None
                if doctores:
                    # Preferir doctores del área
                    doctores_area = [d for d in doctores if d.areaEspecialidad == area]
                    if doctores_area:
                        doctor = random.choice(doctores_area)
                    else:
                        doctor = random.choice(doctores)
                
                paciente = Paciente.objects.create(
                    num_seguridad_social=nss,
                    nombres=nombre,
                    apellidos=f'{apellido} {segundo_apellido}',
                    fecha_nacimiento=fecha_nacimiento,
                    sexo=sexo,
                    area=area,
                    doctor_actual=doctor,
                    hospital_origen=random.choice([
                        'Hospital General', 'Clínica Santa María', 
                        'Centro Médico Nacional', 'Hospital Regional'
                    ]),
                    esta_activo=True,
                    numero_ingresos=random.randint(1, 3)
                )
                
                # Asignar nivel de gravedad basado en el área
                if area.nombre in ['Cuidados Intensivos', 'Urgencias']:
                    # Más probabilidad de pacientes graves
                    nivel_gravedad = random.choices([1, 2, 3], weights=[20, 40, 40])[0]
                elif area.nombre in ['Cardiología', 'Neurología', 'Cirugía']:
                    # Distribución media
                    nivel_gravedad = random.choices([1, 2, 3], weights=[40, 40, 20])[0]
                else:
                    # Mayoría pacientes leves
                    nivel_gravedad = random.choices([1, 2, 3], weights=[70, 25, 5])[0]
                
                GravedadPaciente.objects.create(
                    paciente=paciente,
                    nivel_gravedad=nivel_gravedad
                )
                
                pacientes.append(paciente)
                contador_exitosos += 1
                
                gravedad_txt = {1: 'Leve', 2: 'Moderada', 3: 'Grave'}[nivel_gravedad]
                self.stdout.write(f'  ✓ {nombre} {apellido}: {area.nombre} (Gravedad: {gravedad_txt})')
                
            except Exception as e:
                self.stdout.write(f'  ❌ Error creando paciente {i+1}: {str(e)}')
                continue
        
        self.stdout.write(f'  ✅ {contador_exitosos} pacientes creados exitosamente')
        return pacientes

    def mostrar_resumen(self, areas, enfermeros, pacientes):
        """Mostrar resumen de datos creados"""
        self.stdout.write('\n📊 RESUMEN DE DATOS CREADOS:')
        self.stdout.write(f'  • {len(enfermeros)} enfermeros')
        self.stdout.write(f'  • {len(pacientes)} pacientes')
        
        # Resumen por área
        self.stdout.write('\n🏥 DISTRIBUCIÓN POR ÁREA:')
        for area in areas:
            pacientes_area = len([p for p in pacientes if p.area == area])
            enfermeros_area = len([e for e in enfermeros if e.areaEspecialidad == area])
            self.stdout.write(f'  • {area.nombre}: {pacientes_area} pacientes, {enfermeros_area} enfermeros')
        
        # Distribución por gravedad
        self.stdout.write('\n⚡ DISTRIBUCIÓN POR GRAVEDAD:')
        gravedad_1 = len([p for p in pacientes if hasattr(p, 'gravedadpaciente_set') and p.gravedadpaciente_set.first() and p.gravedadpaciente_set.first().nivel_gravedad == 1])
        gravedad_2 = len([p for p in pacientes if hasattr(p, 'gravedadpaciente_set') and p.gravedadpaciente_set.first() and p.gravedadpaciente_set.first().nivel_gravedad == 2])
        gravedad_3 = len([p for p in pacientes if hasattr(p, 'gravedadpaciente_set') and p.gravedadpaciente_set.first() and p.gravedadpaciente_set.first().nivel_gravedad == 3])
        
        self.stdout.write(f'  • Leves: {gravedad_1}')
        self.stdout.write(f'  • Moderados: {gravedad_2}')
        self.stdout.write(f'  • Graves: {gravedad_3}')
        
        # Información de acceso
        self.stdout.write('\n🔑 CREDENCIALES DE PRUEBA:')
        self.stdout.write('  • Enfermeros: enf_test_001, enf_test_002, etc.')
        self.stdout.write('  • Contraseña: 123456')
        
        self.stdout.write('\n✅ ¡Listo para probar las sugerencias con más datos!')