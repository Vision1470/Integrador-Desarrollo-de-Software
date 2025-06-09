from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import datetime, timedelta
import random

from login.models import Usuarios, AreaEspecialidad, Fortaleza
from usuarioJefa.models import (
    Paciente, Compuesto, Medicamento, Instrumento, 
    AsignacionCalendario, GravedadPaciente, NivelPrioridadArea
)


class Command(BaseCommand):
    help = 'Poblar la base de datos con datos de prueba para testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--full',
            action='store_true',
            help='Crear dataset completo (más datos)',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Iniciando población de base de datos...')
        )
        
        try:
            with transaction.atomic():
                # Limpiar datos existentes (opcional)
                if options['full']:
                    self.limpiar_datos_existentes()
                
                # Crear datos básicos
                fortalezas = self.crear_fortalezas()
                areas = self.crear_areas(fortalezas)
                jefa_piso = self.crear_jefa_piso()
                enfermeros = self.crear_enfermeros(areas, fortalezas)
                doctores = self.crear_doctores(areas, fortalezas)
                
                # Crear medicamentos e instrumentos
                self.crear_medicamentos_instrumentos()
                
                # Crear pacientes con gravedad
                pacientes = self.crear_pacientes(areas, doctores, enfermeros)
                
                # Crear asignaciones de calendario
                self.crear_asignaciones_calendario(enfermeros, areas)
                
                # Asignar niveles de prioridad a áreas
                self.asignar_prioridades_areas(areas)
                
                self.stdout.write(
                    self.style.SUCCESS('✅ Base de datos poblada exitosamente!')
                )
                self.mostrar_resumen(areas, enfermeros, doctores, pacientes)
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error al poblar base de datos: {str(e)}')
            )

    def limpiar_datos_existentes(self):
        """Limpia datos existentes (opcional)"""
        self.stdout.write('🧹 Limpiando datos existentes...')
        
        # Eliminar usuarios (excepto superuser)
        Usuarios.objects.filter(is_superuser=False).delete()
        
        # Limpiar otros datos
        Paciente.objects.all().delete()
        AsignacionCalendario.objects.all().delete()
        GravedadPaciente.objects.all().delete()

    def crear_fortalezas(self):
        """Crear fortalezas médicas"""
        self.stdout.write('📋 Creando fortalezas...')
        
        fortalezas_data = [
            ('Cuidados Intensivos', 'Atención especializada en UCI'),
            ('Pediatría', 'Atención médica a niños'),
            ('Geriatría', 'Atención a pacientes de la tercera edad'),
            ('Cardiología', 'Cuidados cardiovasculares'),
            ('Neurología', 'Atención neurológica'),
            ('Traumatología', 'Cuidados de fracturas y traumas'),
            ('Medicamentos IV', 'Administración intravenosa'),
            ('Curaciones', 'Cuidado de heridas'),
            ('Vendajes', 'Aplicación de vendajes'),
            ('Inyecciones', 'Administración de inyecciones'),
            ('Sueros', 'Aplicación de sueros'),
            ('Terapia Respiratoria', 'Cuidados respiratorios'),
        ]
        
        fortalezas = []
        for nombre, descripcion in fortalezas_data:
            fortaleza, created = Fortaleza.objects.get_or_create(
                nombre=nombre,
                defaults={'descripcion': descripcion}
            )
            fortalezas.append(fortaleza)
            if created:
                self.stdout.write(f'  ✓ Fortaleza creada: {nombre}')
        
        return fortalezas

    def crear_areas(self, fortalezas):
        """Crear áreas de especialidad"""
        self.stdout.write('🏥 Creando áreas de especialidad...')
        
        areas_data = [
            ('Urgencias', 'Atención de emergencias médicas', [0, 6, 7, 9]),
            ('Medicina Interna', 'Atención médica general', [3, 6, 10]),
            ('Cirugía', 'Sala de cirugía y post-operatorio', [0, 5, 7, 8]),
            ('Pediatría', 'Atención pediátrica', [1, 7, 8, 9]),
            ('Cuidados Intensivos', 'UCI para pacientes críticos', [0, 3, 6, 11]),
            ('Cardiología', 'Unidad cardiovascular', [3, 6, 10, 11]),
            ('Neurología', 'Unidad neurológica', [4, 6, 7]),
            ('Traumatología', 'Atención de traumas y fracturas', [5, 7, 8, 9]),
        ]
        
        areas = []
        for nombre, descripcion, fortalezas_indices in areas_data:
            area, created = AreaEspecialidad.objects.get_or_create(
                nombre=nombre,
                defaults={'descripcion': descripcion}
            )
            
            # Asignar fortalezas al área
            fortalezas_area = [fortalezas[i] for i in fortalezas_indices]
            area.fortalezas.set(fortalezas_area)
            
            areas.append(area)
            if created:
                self.stdout.write(f'  ✓ Área creada: {nombre}')
        
        return areas

    def crear_jefa_piso(self):
        """Crear usuario jefa de piso"""
        self.stdout.write('👩‍⚕️ Creando jefa de piso...')
        
        jefa, created = Usuarios.objects.get_or_create(
            username='jefa_piso',
            defaults={
                'first_name': 'María',
                'apellidos': 'González Rodríguez',
                'tipoUsuario': 'JP',
                'edad': 45,
                'fechaNacimiento': '1978-03-15',
                'estaActivo': True,
                'primerIngreso': False,
                'email': 'jefa@hospital.com'
            }
        )
        
        if created:
            jefa.set_password('jefa123')
            jefa.save()
            self.stdout.write('  ✓ Jefa de piso creada: jefa_piso / jefa123')
        
        return jefa

    def crear_enfermeros(self, areas, fortalezas):
        """Crear enfermeros"""
        self.stdout.write('👨‍⚕️ Creando enfermeros...')
        
        nombres_enfermeros = [
            ('Ana', 'Martínez López'),
            ('Carlos', 'Fernández García'),
            ('Lucía', 'Rodríguez Pérez'),
            ('Miguel', 'López Hernández'),
            ('Elena', 'García Martín'),
            ('David', 'Hernández Ruiz'),
            ('Carmen', 'Pérez González'),
            ('Alejandro', 'Martín Díaz'),
            ('Isabel', 'Díaz Moreno'),
            ('Roberto', 'Moreno Jiménez'),
            ('Patricia', 'Jiménez Álvarez'),
            ('Francisco', 'Álvarez Romero'),
            ('Beatriz', 'Romero Torres'),
            ('Javier', 'Torres Vargas'),
            ('Cristina', 'Vargas Castillo'),
            ('Sergio', 'Castillo Ortega'),
        ]
        
        enfermeros = []
        for i, (nombre, apellidos) in enumerate(nombres_enfermeros):
            username = f'enf_{nombre.lower()}{i+1:02d}'
            
            # Asignar área aleatoria
            area_especialidad = random.choice(areas)
            
            enfermero, created = Usuarios.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': nombre,
                    'apellidos': apellidos,
                    'tipoUsuario': 'EN',
                    'edad': random.randint(23, 55),
                    'fechaNacimiento': f'{random.randint(1970, 2000)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}',
                    'areaEspecialidad': area_especialidad,
                    'estaActivo': True,
                    'primerIngreso': False,
                    'email': f'{username}@hospital.com'
                }
            )
            
            if created:
                enfermero.set_password('enf123')
                # Asignar 2-4 fortalezas aleatorias
                fortalezas_enfermero = random.sample(fortalezas, random.randint(2, 4))
                enfermero.fortalezas.set(fortalezas_enfermero)
                enfermero.save()
                
                self.stdout.write(f'  ✓ Enfermero: {username} / enf123 ({area_especialidad.nombre})')
            
            enfermeros.append(enfermero)
        
        return enfermeros

    def crear_doctores(self, areas, fortalezas):
        """Crear doctores"""
        self.stdout.write('👨‍⚕️ Creando doctores...')
        
        nombres_doctores = [
            ('Dr. Juan', 'Méndez Salinas'),
            ('Dra. Laura', 'Vásquez Cruz'),
            ('Dr. Pedro', 'Guerrero Luna'),
            ('Dra. Sofía', 'Campos Herrera'),
            ('Dr. Ricardo', 'Morales Vega'),
            ('Dra. Andrea', 'Silva Contreras'),
            ('Dr. Fernando', 'Reyes Aguilar'),
            ('Dra. Mónica', 'Gutiérrez Soto'),
        ]
        
        doctores = []
        for i, (nombre, apellidos) in enumerate(nombres_doctores):
            username = f'doc_{nombre.split(".")[1].lower()}{i+1:02d}'
            
            # Asignar área aleatoria
            area_especialidad = random.choice(areas)
            
            doctor, created = Usuarios.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': nombre,
                    'apellidos': apellidos,
                    'tipoUsuario': 'DR',
                    'edad': random.randint(28, 65),
                    'fechaNacimiento': f'{random.randint(1960, 1995)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}',
                    'areaEspecialidad': area_especialidad,
                    'estaActivo': True,
                    'primerIngreso': False,
                    'email': f'{username}@hospital.com'
                }
            )
            
            if created:
                doctor.set_password('doc123')
                # Asignar 1-3 fortalezas aleatorias relacionadas con su área
                fortalezas_doctor = random.sample(fortalezas, random.randint(1, 3))
                doctor.fortalezas.set(fortalezas_doctor)
                doctor.save()
                
                self.stdout.write(f'  ✓ Doctor: {username} / doc123 ({area_especialidad.nombre})')
            
            doctores.append(doctor)
        
        return doctores

    def crear_medicamentos_instrumentos(self):
        """Crear medicamentos e instrumentos"""
        self.stdout.write('💊 Creando medicamentos e instrumentos...')
        
        # Crear compuestos
        compuestos_data = [
            'Paracetamol', 'Ibuprofeno', 'Aspirina', 'Amoxicilina',
            'Diclofenaco', 'Omeprazol', 'Losartán', 'Metformina'
        ]
        
        compuestos = []
        for nombre in compuestos_data:
            compuesto, created = Compuesto.objects.get_or_create(
                nombre=nombre,
                defaults={'descripcion': f'Compuesto activo {nombre}'}
            )
            compuestos.append(compuesto)
        
        # Crear medicamentos
        medicamentos_data = [
            ('Paracetamol', '500', [0], 500),
            ('Ibuprofeno', '400', [1], 300),
            ('Aspirina', '100', [2], 200),
            ('Amoxicilina', '500', [3], 150),
            ('Diclofenaco', '50', [4], 100),
            ('Omeprazol', '20', [5], 250),
            ('Losartán', '50', [6], 180),
            ('Metformina', '850', [7], 300),
        ]
        
        for nombre, gramaje, compuestos_indices, cantidad in medicamentos_data:
            medicamento, created = Medicamento.objects.get_or_create(
                nombre=nombre,
                gramaje=gramaje,
                defaults={'cantidad_disponible': cantidad}
            )
            if created:
                medicamento.compuestos.set([compuestos[i] for i in compuestos_indices])
        
        # Crear instrumentos
        instrumentos_data = [
            ('Tensiómetro Digital', 15, 'Monitor de presión arterial automático'),
            ('Termómetro Infrarrojo', 25, 'Termómetro sin contacto'),
            ('Oxímetro de Pulso', 30, 'Medidor de saturación de oxígeno'),
            ('Estetoscopio', 20, 'Estetoscopio clínico profesional'),
            ('Jeringas 5ml', 500, 'Jeringas desechables de 5ml'),
            ('Gasas Estériles', 200, 'Gasas estériles 10x10cm'),
            ('Vendas Elásticas', 100, 'Vendas elásticas de diferentes tamaños'),
        ]
        
        for nombre, cantidad, especificaciones in instrumentos_data:
            Instrumento.objects.get_or_create(
                nombre=nombre,
                defaults={
                    'cantidad': cantidad,
                    'especificaciones': especificaciones
                }
            )

    def crear_pacientes(self, areas, doctores, enfermeros):
        """Crear pacientes con diferentes niveles de gravedad"""
        self.stdout.write('🏥 Creando pacientes...')
        
        # Validaciones previas
        if not areas:
            self.stdout.write(self.style.ERROR('❌ No hay áreas disponibles'))
            return []
        if not doctores:
            self.stdout.write(self.style.ERROR('❌ No hay doctores disponibles'))
            return []
        if not enfermeros:
            self.stdout.write(self.style.ERROR('❌ No hay enfermeros disponibles'))
            return []
        
        nombres_pacientes = [
            ('José', 'Ramírez', 'M'), ('María', 'López', 'F'),
            ('Antonio', 'García', 'M'), ('Carmen', 'Hernández', 'F'),
            ('Manuel', 'Martín', 'M'), ('Pilar', 'Sánchez', 'F'),
            ('Francisco', 'González', 'M'), ('Dolores', 'Díaz', 'F'),
            ('Juan', 'Rodríguez', 'M'), ('Mercedes', 'Pérez', 'F'),
            ('Luis', 'Fernández', 'M'), ('Antonia', 'Gómez', 'F'),
            ('Miguel', 'Ruiz', 'M'), ('Francisca', 'Moreno', 'F'),
            ('Jesús', 'Muñoz', 'M'), ('Isabel', 'Álvarez', 'F'),
            ('Rafael', 'Jiménez', 'M'), ('Ana', 'Romero', 'F'),
            ('Carlos', 'Navarro', 'M'), ('Rosario', 'Torres', 'F'),
            ('Andrés', 'Domínguez', 'M'), ('Teresa', 'Vázquez', 'F'),
            ('Ricardo', 'Morales', 'M'), ('Concepción', 'Ramos', 'F'),
            ('Fernando', 'Gil', 'M'), ('Esperanza', 'Serrano', 'F'),
            ('Eduardo', 'Blanco', 'M'), ('Purificación', 'Molina', 'F'),
            ('Ramón', 'Castro', 'M'), ('Amparo', 'Ortega', 'F'),
            ('Alberto', 'Vargas', 'M'), ('Gloria', 'Medina', 'F'),
            ('Enrique', 'Herrera', 'M'), ('Remedios', 'Garrido', 'F'),
            ('Vicente', 'Ibáñez', 'M'), ('Cristina', 'Guerrero', 'F'),
            ('Ángel', 'Mendoza', 'M'), ('Silvia', 'Cortes', 'F'),
            ('Pablo', 'Castillo', 'M'), ('Beatriz', 'León', 'F'),
        ]
        
        pacientes = []
        for i, (nombre, apellido, sexo) in enumerate(nombres_pacientes):
            # Asignar área aleatoria
            area = random.choice(areas)
            
            # Buscar doctores en esa área, si no hay, usar cualquier doctor
            doctores_area = [d for d in doctores if d.areaEspecialidad == area]
            if not doctores_area:
                doctores_area = doctores  # Usar cualquier doctor si no hay en el área
            doctor = random.choice(doctores_area)
            
            # Buscar enfermeros en esa área, si no hay, usar cualquier enfermero
            enfermeros_area = [e for e in enfermeros if e.areaEspecialidad == area]
            if not enfermeros_area:
                enfermeros_area = enfermeros  # Usar cualquier enfermero si no hay en el área
            enfermero = random.choice(enfermeros_area)
            
            # Generar fecha de nacimiento realista
            edad = random.randint(18, 85)
            fecha_nacimiento = datetime.now().date() - timedelta(days=edad*365 + random.randint(0, 365))
            
            paciente, created = Paciente.objects.get_or_create(
                num_seguridad_social=f'SS{i+1:04d}2024',
                defaults={
                    'nombres': nombre,
                    'apellidos': apellido,
                    'fecha_nacimiento': fecha_nacimiento,
                    'sexo': sexo,
                    'area': area,
                    'doctor_actual': doctor,
                    'enfermero_actual': enfermero,
                    'hospital_origen': 'Hospital General',
                    'esta_activo': True,
                    'numero_ingresos': 1
                }
            )
            
            if created:
                # Asignar nivel de gravedad basado en el área
                if area.nombre in ['Cuidados Intensivos', 'Urgencias']:
                    # Más probabilidad de pacientes graves en UCI y Urgencias
                    nivel_gravedad = random.choices([1, 2, 3], weights=[30, 40, 30])[0]
                elif area.nombre in ['Cardiología', 'Neurología']:
                    # Distribución media en especialidades críticas
                    nivel_gravedad = random.choices([1, 2, 3], weights=[40, 45, 15])[0]
                else:
                    # Mayoría pacientes leves en otras áreas
                    nivel_gravedad = random.choices([1, 2, 3], weights=[60, 30, 10])[0]
                
                GravedadPaciente.objects.create(
                    paciente=paciente,
                    nivel_gravedad=nivel_gravedad
                )
                
                self.stdout.write(f'  ✓ Paciente: {nombre} {apellido} - {area.nombre} (Gravedad: {nivel_gravedad})')
            
            pacientes.append(paciente)
        
        return pacientes

    def crear_asignaciones_calendario(self, enfermeros, areas):
        """Crear asignaciones de calendario para enfermeros"""
        self.stdout.write('📅 Creando asignaciones de calendario...')
        
        if not enfermeros:
            self.stdout.write(self.style.WARNING('⚠️ No hay enfermeros para asignar'))
            return
        
        if not areas:
            self.stdout.write(self.style.WARNING('⚠️ No hay áreas disponibles'))
            return
        
        año_actual = datetime.now().year
        
        # Crear asignaciones para cada enfermero en diferentes bimestres
        for enfermero in enfermeros:
            # Asignar 2-3 bimestres aleatorios para cada enfermero
            bimestres_asignados = random.sample(range(1, 7), random.randint(2, 3))
            
            for bimestre in bimestres_asignados:
                # Calcular fechas del bimestre
                mes_inicio = ((bimestre - 1) * 2) + 1
                fecha_inicio = datetime(año_actual, mes_inicio, 1)
                
                if mes_inicio + 1 <= 12:
                    import calendar
                    ultimo_dia_mes2 = calendar.monthrange(año_actual, mes_inicio + 1)[1]
                    fecha_fin = datetime(año_actual, mes_inicio + 1, ultimo_dia_mes2)
                else:
                    fecha_fin = datetime(año_actual, 12, 31)
                
                # Asignar área (preferencia por su especialidad, pero puede ser otra)
                if enfermero.areaEspecialidad and random.random() < 0.7:  # 70% probabilidad
                    area = enfermero.areaEspecialidad
                else:
                    area = random.choice(areas)
                
                AsignacionCalendario.objects.get_or_create(
                    enfermero=enfermero,
                    bimestre=bimestre,
                    year=año_actual,
                    defaults={
                        'area': area,
                        'fecha_inicio': fecha_inicio.date(),
                        'fecha_fin': fecha_fin.date(),
                        'activo': True
                    }
                )
        
        total_asignaciones = AsignacionCalendario.objects.filter(activo=True).count()
        self.stdout.write(f'  ✓ {total_asignaciones} asignaciones de calendario creadas')

    def asignar_prioridades_areas(self, areas):
        """Asignar niveles de prioridad a las áreas"""
        self.stdout.write('⭐ Asignando prioridades a áreas...')
        
        # Asignar prioridades específicas según el tipo de área
        prioridades = {
            'Cuidados Intensivos': 5,
            'Urgencias': 5,
            'Cardiología': 4,
            'Neurología': 4,
            'Cirugía': 4,
            'Pediatría': 3,
            'Medicina Interna': 2,
            'Traumatología': 3,
        }
        
        for area in areas:
            prioridad = prioridades.get(area.nombre, 2)  # Default: prioridad 2
            
            NivelPrioridadArea.objects.get_or_create(
                area=area,
                defaults={'nivel_prioridad': prioridad}
            )
            
            self.stdout.write(f'  ✓ {area.nombre}: Prioridad {prioridad}')

    def mostrar_resumen(self, areas, enfermeros, doctores, pacientes):
        """Mostrar resumen de datos creados"""
        self.stdout.write('\n📊 RESUMEN DE DATOS CREADOS:')
        self.stdout.write(f'  • {len(areas)} áreas de especialidad')
        self.stdout.write(f'  • {len(enfermeros)} enfermeros')
        self.stdout.write(f'  • {len(doctores)} doctores')
        self.stdout.write(f'  • {len(pacientes)} pacientes')
        
        # Resumen por área
        self.stdout.write('\n🏥 DISTRIBUCIÓN POR ÁREA:')
        for area in areas:
            pacientes_area = len([p for p in pacientes if p.area == area])
            enfermeros_area = len([e for e in enfermeros if e.areaEspecialidad == area])
            self.stdout.write(f'  • {area.nombre}: {pacientes_area} pacientes, {enfermeros_area} enfermeros')
        
        # Información de acceso
        self.stdout.write('\n🔑 CREDENCIALES DE ACCESO:')
        self.stdout.write('  • Jefa de Piso: jefa_piso / jefa123')
        self.stdout.write('  • Enfermeros: enf_ana01, enf_carlos02, etc. / enf123')
        self.stdout.write('  • Doctores: doc_juan01, doc_laura02, etc. / doc123')
        
        self.stdout.write('\n✅ ¡Listo para probar el sistema de sobrecarga!')