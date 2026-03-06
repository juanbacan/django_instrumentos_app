"""
Management command para cargar tests de ejemplo en la base de datos.

Uso:
    python manage.py cargar_tests_ejemplo

Este comando crea:
- 2 tests de ejemplo (uno premium, uno gratis)
- Dimensiones, items, y opciones de escala
- Niveles de retroalimentación con diagnósticos
- Acceso premium de ejemplo
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from datetime import datetime, timedelta

from applications.instrumentos.models import (
    Instrumento, Dimension, Item, EscalaOpcion, 
    NivelRetroalimentacion, AccesoPremiumInstrumento
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Carga tests de ejemplo para pruebas del sistema'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Cargando tests de ejemplo...'))

        with transaction.atomic():
            # Crear tests
            test_gratuito = self._crear_test_gratuito()
            test_premium = self._crear_test_premium()

            # Crear acceso premium de ejemplo (si existe usuario admin)
            self._crear_acceso_premium_ejemplo(test_premium)

        self.stdout.write(self.style.SUCCESS('\n✅ Tests de ejemplo cargados exitosamente!'))
        self.stdout.write(self.style.WARNING('\n📌 Próximos pasos:'))
        self.stdout.write('   1. Ve a Admin → Instrumentos')
        self.stdout.write('   2. Verás dos tests de ejemplo')
        self.stdout.write('   3. Prueba accediendo como usuario no-admin')
        self.stdout.write('   4. El test "Autorregulación - Premium" requiere acceso premium')

    def _crear_test_gratuito(self):
        """Crea un test de ejemplo gratuito"""
        self.stdout.write('\n📚 Creando test GRATUITO: "Autorregulación Emocional"...')

        instrumento, created = Instrumento.objects.get_or_create(
            slug='autorregulacion-emocional',
            defaults={
                'nombre': 'Autorregulación Emocional',
                'descripcion': 'Evalúa tu capacidad para manejar emociones bajo presión. Este test es de acceso gratuito para todos.',
                'activo': True,
                'premium': False
            }
        )

        if not created:
            self.stdout.write('   (Ya existe, actualizado)')
            return instrumento

        # Crear opciones de escala
        escalas = [
            {'etiqueta': 'Nunca', 'valor': 1, 'orden': 1},
            {'etiqueta': 'Rara vez', 'valor': 2, 'orden': 2},
            {'etiqueta': 'A veces', 'valor': 3, 'orden': 3},
            {'etiqueta': 'Frecuentemente', 'valor': 4, 'orden': 4},
            {'etiqueta': 'Siempre', 'valor': 5, 'orden': 5}
        ]

        for escala in escalas:
            EscalaOpcion.objects.get_or_create(
                instrumento=instrumento,
                valor_nominal=escala['valor'],
                defaults={
                    'etiqueta': escala['etiqueta'],
                    'orden': escala['orden']
                }
            )

        # Crear dimensión
        dimension = Dimension.objects.create(
            instrumento=instrumento,
            nombre='Control Emocional',
            orden=1
        )

        # Crear ítems
        items_data = [
            {'texto': 'Mantengo la calma ante situaciones críticas en el aula', 'es_inverso': False, 'orden': 1},
            {'texto': 'Me resulta difícil controlar mis impulsos bajo presión', 'es_inverso': True, 'orden': 2},
            {'texto': 'Puedo manejar múltiples conflictos simultáneamente', 'es_inverso': False, 'orden': 3},
            {'texto': 'Pierdo la paciencia fácilmente con estudiantes disruptivos', 'es_inverso': True, 'orden': 4},
            {'texto': 'Tengo estrategias claras para calmar situaciones tensas', 'es_inverso': False, 'orden': 5}
        ]

        for item in items_data:
            Item.objects.create(
                dimension=dimension,
                **item
            )

        # Crear niveles de retroalimentación
        niveles = [
            {
                'nombre_nivel': 'Requiere Atención (Bajo)',
                'porcentaje_min': 0.00,
                'porcentaje_max': 33.99,
                'mensaje_feedback': '<p><strong>📊 Análisis:</strong> Tus resultados indican que situaciones de tensión pueden estar desbordando tu capacidad de respuesta. La autorregulación es fundamental para crear un ambiente aula positivo.</p><p><strong>💡 Recomendaciones:</strong></p><ul><li>Implementa <strong>pausas activas</strong> durante tu jornada</li><li>Practica técnicas de <strong>respiración diafragmática</strong> (4-7-8)</li><li>Busca espacios de descompresión antes de entrar al aula</li><li>Considera cursos de <strong>mindfulness para docentes</strong></li></ul>'
            },
            {
                'nombre_nivel': 'Adecuado (Medio)',
                'porcentaje_min': 34.00,
                'porcentaje_max': 66.99,
                'mensaje_feedback': '<p><strong>📊 Análisis:</strong> Posees herramientas adecuadas para manejar conflictos y situaciones de estrés típicas. Sin embargo, bajo presión sostenida podrías experimentar desgaste emocional.</p><p><strong>💡 Recomendaciones:</strong></p><ul><li>Mantén y refuerza tus estrategias actuales de manejo del estrés</li><li>Participa en <strong>grupos de apoyo</strong> con otros docentes</li><li>Desarrolla un <strong>plan personal de autocuidado</strong></li><li>Establece límites claros entre vida laboral y personal</li></ul>'
            },
            {
                'nombre_nivel': 'Óptimo (Alto)',
                'porcentaje_min': 67.00,
                'porcentaje_max': 100.00,
                'mensaje_feedback': '<p><strong>🎉 ¡Excelente!</strong> Muestras un <strong>alto grado de control emocional</strong> y eres capaz de separar los problemas personales de tu práctica docente.</p><p><strong>✓ Fortalezas identificadas:</strong></p><ul><li>✓ Mantienes la calma ante adversidades</li><li>✓ Gestionas eficazmente tu estrés</li><li>✓ Eres modelo de autorregulación para tus estudiantes</li></ul><p><strong>🚀 Próximos pasos:</strong> Comparte tus estrategias con otros docentes y considera ser mentor en bienestar emocional.</p>'
            }
        ]

        for nivel in niveles:
            NivelRetroalimentacion.objects.create(
                dimension=dimension,
                **nivel
            )

        self.stdout.write(self.style.SUCCESS('   ✅ Test gratuito creado con 5 ítems y 3 niveles de retroalimentación'))
        return instrumento

    def _crear_test_premium(self):
        """Crea un test de ejemplo premium"""
        self.stdout.write('\n💎 Creando test PREMIUM: "Empatía y Relaciones Interpersonales"...')

        instrumento, created = Instrumento.objects.get_or_create(
            slug='empatia-relaciones-premium',
            defaults={
                'nombre': 'Empatía y Relaciones Interpersonales - Premium',
                'descripcion': 'Evalúa tu capacidad empática y habilidades para construir relaciones positivas. Este es un test exclusivo para usuarios premium.',
                'activo': True,
                'premium': True
            }
        )

        if not created:
            self.stdout.write('   (Ya existe, actualizado como premium)')
            return instrumento

        # Crear opciones de escala
        escalas = [
            {'etiqueta': 'Totalmente en desacuerdo', 'valor': 1, 'orden': 1},
            {'etiqueta': 'En desacuerdo', 'valor': 2, 'orden': 2},
            {'etiqueta': 'Neutral', 'valor': 3, 'orden': 3},
            {'etiqueta': 'De acuerdo', 'valor': 4, 'orden': 4},
            {'etiqueta': 'Totalmente de acuerdo', 'valor': 5, 'orden': 5}
        ]

        for escala in escalas:
            EscalaOpcion.objects.get_or_create(
                instrumento=instrumento,
                valor_nominal=escala['valor'],
                defaults={
                    'etiqueta': escala['etiqueta'],
                    'orden': escala['orden']
                }
            )

        # Crear dimensión 1: Empatía
        dim_empatia = Dimension.objects.create(
            instrumento=instrumento,
            nombre='Capacidad Empática',
            orden=1
        )

        items_empatia = [
            {'texto': 'Identifico fácilmente las emociones de mis estudiantes', 'es_inverso': False, 'orden': 1},
            {'texto': 'Me cuesta entender el punto de vista ajeno cuando discrepo', 'es_inverso': True, 'orden': 2},
            {'texto': 'Adapto mi comunicación según el estado emocional de la otra persona', 'es_inverso': False, 'orden': 3},
            {'texto': 'Ignoro las preocupaciones personales de mis colegas', 'es_inverso': True, 'orden': 4}
        ]

        for item in items_empatia:
            Item.objects.create(dimension=dim_empatia, **item)

        # Crear dimensión 2: Habilidades Sociales
        dim_sociales = Dimension.objects.create(
            instrumento=instrumento,
            nombre='Habilidades Sociales',
            orden=2
        )

        items_sociales = [
            {'texto': 'Establezco relaciones positivas con mis colegas fácilmente', 'es_inverso': False, 'orden': 1},
            {'texto': 'Evito participar en trabajos colaborativos', 'es_inverso': True, 'orden': 2},
            {'texto': 'Medío efectivamente en conflictos entre compañeros', 'es_inverso': False, 'orden': 3},
            {'texto': 'Resuelvo desacuerdos de forma constructiva', 'es_inverso': False, 'orden': 4}
        ]

        for item in items_sociales:
            Item.objects.create(dimension=dim_sociales, **item)

        # Niveles para Empatía
        niveles_empatia = [
            {
                'nombre_nivel': 'Por Desarrollar (Bajo)',
                'porcentaje_min': 0.00,
                'porcentaje_max': 33.99,
                'mensaje_feedback': '<p><strong>📊 Análisis:</strong> Tu capacidad empática necesita desarrollarse. La empatía es clave para crear relaciones significativas y reducir conflictos en el aula.</p><p><strong>💡 Recomendaciones:</strong></p><ul><li>Participa en <strong>talleres de comunicación empática</strong></li><li>Practica la <strong>escucha activa</strong> sin juzgar</li><li>Realiza dinámicas de <strong>círculos de diálogo</strong> con estudiantes</li></ul>'
            },
            {
                'nombre_nivel': 'En Desarrollo (Medio)',
                'porcentaje_min': 34.00,
                'porcentaje_max': 66.99,
                'mensaje_feedback': '<p><strong>📊 Análisis:</strong> Tienes capacidad empática moderada. En ciertas situaciones conectas bien, pero puedes mejorar bajo estrés.</p><p><strong>💡 Recomendaciones:</strong></p><ul><li>Reflexiona sobre <strong>conflictos recientes</strong></li><li>Participa en <strong>observaciones de clase entre colegas</strong></li><li>Dedica tiempo consciente a <strong>conocer mejor a cada estudiante</strong></li></ul>'
            },
            {
                'nombre_nivel': 'Sobresaliente (Alto)',
                'porcentaje_min': 67.00,
                'porcentaje_max': 100.00,
                'mensaje_feedback': '<p><strong>🎉 ¡Enhorabuena!</strong> Demuestras una <strong>empatía excepcional</strong> hacia estudiantes y colegas.</p><p><strong>✓ Fortalezas:</strong></p><ul><li>✓ Escuchas activamente sin prejuzgar</li><li>✓ Adaptas tu comunicación según necesidades emocionales</li><li>✓ Creas un ambiente seguro para que otros se expresen</li></ul><p><strong>🚀 Próximos pasos:</strong> Comparte tu modelo empático en capacitaciones y mentoría.</p>'
            }
        ]

        for nivel in niveles_empatia:
            nivel['dimension'] = dim_empatia
            NivelRetroalimentacion.objects.create(**nivel)

        # Niveles para Habilidades Sociales (con mismo contenido como ejemplo)
        for nivel in niveles_empatia:
            nivel_social = nivel.copy()
            nivel_social['dimension'] = dim_sociales
            NivelRetroalimentacion.objects.create(**nivel_social)

        self.stdout.write(self.style.SUCCESS('   ✅ Test premium creado con 8 ítems, 2 dimensiones y 6 niveles de retroalimentación'))
        return instrumento

    def _crear_acceso_premium_ejemplo(self, test_premium):
        """Crea acceso premium de ejemplo"""
        self.stdout.write('\n🔑 Creando acceso premium de ejemplo...')

        # Buscar usuario admin
        try:
            admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                self.stdout.write(self.style.WARNING('   ⚠️  No hay usuario admin. Saltando creación de acceso premium.'))
                return

            # Crear acceso premium permanente para el admin
            acceso, created = AccesoPremiumInstrumento.objects.get_or_create(
                usuario=admin_user,
                instrumento=test_premium,
                defaults={
                    'activo': True,
                    'fecha_expiracion': None  # Permanente
                }
            )

            if created:
                self.stdout.write(f'   ✅ Acceso premium otorgado a {admin_user.username}')
            else:
                self.stdout.write(f'   ℹ️  {admin_user.username} ya tiene acceso premium')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Error al crear acceso premium: {e}'))
