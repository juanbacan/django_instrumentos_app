"""
Vistas de administración para el módulo de Instrumentos/Evaluaciones.
Estas vistas extienden de ModelCRUDView para proporcionar interfaces
de administración completas con listado, creación, edición y eliminación.
"""
import json
from django.shortcuts import render
from django.db import transaction
from django.db.models import Count, Q
from django.contrib import messages

from core.views import ViewAdministracionBase, ModelCRUDView
from core.utils import success_json, error_json, get_redirect_url

from .models import Instrumento, Dimension, Item, EscalaOpcion, Intento, Respuesta, NivelRetroalimentacion
from .forms import InstrumentoForm, DimensionForm, ItemForm, EscalaOpcionForm, ImportarTestForm, NivelRetroalimentacionForm


# ==========================================
# Vista Principal de Administración
# ==========================================
class InstrumentosAdminView(ViewAdministracionBase):
    """Vista principal del módulo de administración de instrumentos"""
    
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        
        # Estadísticas generales
        context['total_instrumentos'] = Instrumento.objects.count()
        context['instrumentos_activos'] = Instrumento.objects.filter(activo=True).count()
        context['total_dimensiones'] = Dimension.objects.count()
        context['total_items'] = Item.objects.count()
        context['total_intentos'] = Intento.objects.count()
        context['intentos_completados'] = Intento.objects.filter(completado=True).count()
        
        # Instrumentos recientes
        context['instrumentos_recientes'] = Instrumento.objects.all().order_by('-created_at')[:5]
        
        # Intentos recientes
        context['intentos_recientes'] = Intento.objects.select_related(
            'usuario', 'instrumento'
        ).order_by('-inicio')[:10]
        
        return render(request, 'instrumentos/admin/dashboard.html', context)


# ==========================================
# CRUD de Instrumentos
# ==========================================
class InstrumentoAdminView(ModelCRUDView):
    """Vista CRUD para gestionar Instrumentos/Evaluaciones"""
    model = Instrumento
    form_class = InstrumentoForm
    template_list = 'instrumentos/admin/instrumento_list.html'
    template_form = 'core/forms/formAdmin.html'
    
    list_display = ['nombre', 'slug', 'activo', 'num_dimensiones', 'num_items', 'premium', 'created_at']
    search_fields = ['nombre', 'slug', 'descripcion']
    list_filter = ['activo', 'premium', 'created_at']
    ordering = ['-created_at']
    paginate_by = 20
    
    # Configuración de exportación
    export_filename = 'instrumentos.xlsx'
    export_headers = ['ID', 'Nombre', 'Slug', 'Activo', 'Dimensiones', 'Ítems', 'Creado']
    export_fields = ['id', 'nombre', 'slug', 'activo', 'num_dimensiones', 'num_items', 'created_at']
    
    def get_queryset(self):
        """Agregar anotaciones para mejorar el rendimiento"""
        qs = super().get_queryset()
        qs = qs.annotate(
            num_dimensiones=Count('dimensiones', distinct=True)
        )
        return qs
    
    def num_dimensiones(self, obj):
        """Mostrar número de dimensiones"""
        return obj.dimensiones.count()
    num_dimensiones.short_description = 'Dimensiones'
    
    def num_items(self, obj):
        """Mostrar número total de ítems"""
        return Item.objects.filter(dimension__instrumento=obj).count()
    num_items.short_description = 'Ítems'
    
    def get_importar(self, request, context, *args, **kwargs):
        """Mostrar formulario para importar test desde JSON"""
        context['title'] = 'Importar Test desde JSON'
        context['form'] = ImportarTestForm()
        context['action'] = 'importar'
        context['message'] ='''
            <div class="alert alert-info mt-2">
                <strong><i class="fa-solid fa-circle-info me-2"></i>Formato JSON:</strong>
                Puedes subir un archivo o pegar el JSON en texto. Debe contener las claves <code>instrumento</code>, <code>escalas</code> y <code>dimensiones</code>.
                <br><small class="text-muted">También puedes incluir campos opcionales como <code>instrumento.premium</code> y <code>dimensiones[].niveles_retroalimentacion</code>.</small>
                <details class="mt-2">
                    <summary style="cursor: pointer;">Ver ejemplo</summary>
                    <pre class="mt-2 bg-light p-2 rounded small" style="max-height: 300px; overflow-y: auto;"><code>
{
    "instrumento": {
        "nombre": "Test de Ejemplo",
        "slug": "test-ejemplo",
        "descripcion": "Descripción del test",
        "activo": true,
        "premium": false
    },
    "escalas": [
        {"etiqueta": "Nunca", "valor": 1, "orden": 1},
        {"etiqueta": "A veces", "valor": 2, "orden": 2}
    ],
    "dimensiones": [
        {
            "nombre": "Dimensión 1",
            "orden": 1,
            "items": [
                {"texto": "Pregunta 1", "es_inverso": false, "orden": 1},
                {"texto": "Pregunta 2", "es_inverso": true, "orden": 2}
            ],
            "niveles_retroalimentacion": [
                {
                    "nombre_nivel": "Bajo",
                    "porcentaje_min": 0,
                    "porcentaje_max": 49.99,
                    "mensaje_feedback": "Necesitas reforzar esta dimensión.",
                    "clase_visual": "warning"
                },
                {
                    "nombre_nivel": "Alto",
                    "porcentaje_min": 50,
                    "porcentaje_max": 100,
                    "mensaje_feedback": "Buen desempeño en esta dimensión.",
                    "clase_visual": "success"
                }
            ]
        }
    ]
}</code></pre>
                    </details>
                </div>
            '''
        return render(request, 'core/modals/formModal.html', context)
    
    def post_importar(self, request, context, *args, **kwargs):
        """Procesar importación de test desde JSON"""
        form = ImportarTestForm(request.POST, request.FILES)
        
        if not form.is_valid():
            return error_json('Formulario no válido. Por favor, revisa los campos e intenta de nuevo.', forms=[form])
        
        try:
            json_file = form.cleaned_data.get('json_file')
            json_text = form.cleaned_data.get('json_text', '')
            
            # Leer y validar JSON
            try:
                if json_text:
                    data = json.loads(json_text)
                elif json_file:
                    json_content = json_file.read().decode('utf-8')
                    data = json.loads(json_content)
                else:
                    return error_json('Debes subir un archivo JSON o pegar el contenido JSON en la caja de texto.')
            except json.JSONDecodeError as e:
                return error_json(f'Error al leer el JSON: {str(e)}')
            except UnicodeDecodeError:
                return error_json('No se pudo decodificar el archivo. Asegúrate de usar UTF-8.')
            except Exception as e:
                return error_json(f'Error al procesar el JSON: {str(e)}')
            
            # Validar estructura JSON
            if 'instrumento' not in data:
                return error_json('El JSON debe contener la clave "instrumento"')
            if 'escalas' not in data:
                return error_json('El JSON debe contener la clave "escalas"')
            if 'dimensiones' not in data:
                return error_json('El JSON debe contener la clave "dimensiones"')
            
            # Procesar importación en transacción atómica
            with transaction.atomic():
                instrumento_data = data['instrumento']
                
                # Crear o actualizar instrumento
                instrumento, created = Instrumento.objects.update_or_create(
                    slug=instrumento_data['slug'],
                    defaults={
                        'nombre': instrumento_data['nombre'],
                        'descripcion': instrumento_data.get('descripcion', ''),
                        'activo': instrumento_data.get('activo', True),
                        'premium': instrumento_data.get('premium', False)
                    }
                )
                
                # Crear opciones de escala
                for escala_data in data['escalas']:
                    EscalaOpcion.objects.update_or_create(
                        instrumento=instrumento,
                        valor_nominal=escala_data['valor'],
                        defaults={
                            'etiqueta': escala_data['etiqueta'],
                            'orden': escala_data.get('orden', escala_data['valor'])
                        }
                    )
                
                # Crear dimensiones, ítems y retroalimentación
                total_niveles = 0  # Contador para niveles de retroalimentación
                
                for dimension_data in data['dimensiones']:
                    dimension, dim_created = Dimension.objects.update_or_create(
                        instrumento=instrumento,
                        nombre=dimension_data['nombre'],
                        defaults={
                            'orden': dimension_data.get('orden', 1)
                        }
                    )
                    
                    # Crear ítems de la dimensión
                    for item_data in dimension_data.get('items', []):
                        Item.objects.update_or_create(
                            dimension=dimension,
                            texto=item_data['texto'],
                            defaults={
                                'es_inverso': item_data.get('es_inverso', False),
                                'orden': item_data.get('orden', 1)
                            }
                        )
                    
                    # ==========================================
                    # NUEVO: Crear Niveles de Retroalimentación
                    # ==========================================
                    for nivel_data in dimension_data.get('niveles_retroalimentacion', []):
                        NivelRetroalimentacion.objects.update_or_create(
                            dimension=dimension,
                            nombre_nivel=nivel_data['nombre_nivel'],
                            defaults={
                                'porcentaje_min': nivel_data['porcentaje_min'],
                                'porcentaje_max': nivel_data['porcentaje_max'],
                                'mensaje_feedback': nivel_data['mensaje_feedback'],
                                'clase_visual': nivel_data.get('clase_visual', 'secondary')
                            }
                        )
                        total_niveles += 1
                
                # Mensaje de éxito actualizado
                action = 'creado' if created else 'actualizado'
                total_dimensiones = len(data['dimensiones'])
                total_items = sum(len(d.get('items', [])) for d in data['dimensiones'])
                
                messages.success(
                    request,
                    f'✅ Test "{instrumento.nombre}" {action} exitosamente con '
                    f'{total_dimensiones} dimensiones, {total_items} ítems y {total_niveles} diagnósticos.'
                )
                
                return success_json({
                    'mensaje': f'Test {action} exitosamente',
                    'url': request.path
                })
                
        except Exception as e:
            return error_json(f'Error al importar: {str(e)}')


# ==========================================
# CRUD de Dimensiones
# ==========================================
class DimensionAdminView(ModelCRUDView):
    """Vista CRUD para gestionar Dimensiones"""
    model = Dimension
    form_class = DimensionForm
    template_list = 'instrumentos/admin/dimension_list.html'
    template_form = 'core/forms/formAdmin.html'
    
    list_display = ['nombre', 'instrumento', 'orden', 'num_items', 'created_at']
    search_fields = ['nombre', 'instrumento__nombre']
    list_filter = ['instrumento', 'created_at']
    ordering = ['instrumento', 'orden']
    paginate_by = 30
    auto_complete_fields = ['instrumento']
    
    # Configuración de exportación
    export_filename = 'dimensiones.xlsx'
    export_headers = ['ID', 'Nombre', 'Instrumento', 'Orden', 'Ítems', 'Creado']
    export_fields = ['id', 'nombre', 'instrumento__nombre', 'orden', 'num_items', 'created_at']
    
    def get_queryset(self):
        """Optimizar consultas"""
        qs = super().get_queryset()
        qs = qs.select_related('instrumento').annotate(
            num_items=Count('items')
        )
        return qs
    
    def num_items(self, obj):
        """Mostrar número de ítems"""
        return obj.items.count()
    num_items.short_description = 'Ítems'


# ==========================================
# CRUD de Ítems
# ==========================================
class ItemAdminView(ModelCRUDView):
    """Vista CRUD para gestionar Ítems/Preguntas"""
    model = Item
    form_class = ItemForm
    template_list = 'instrumentos/admin/item_list.html'
    template_form = 'core/forms/formAdmin.html'
    
    list_display = ['texto_corto', 'dimension', 'instrumento', 'es_inverso', 'orden', 'created_at']
    search_fields = ['texto', 'dimension__nombre', 'dimension__instrumento__nombre']
    list_filter = ['dimension__instrumento', 'dimension', 'es_inverso', 'created_at']
    ordering = ['dimension__instrumento', 'dimension__orden', 'orden']
    paginate_by = 50
    auto_complete_fields = ['dimension']
    
    # Configuración de exportación
    export_filename = 'items.xlsx'
    export_headers = ['ID', 'Texto', 'Dimensión', 'Instrumento', 'Inverso', 'Orden', 'Creado']
    export_fields = ['id', 'texto', 'dimension__nombre', 'instrumento', 'es_inverso', 'orden', 'created_at']
    
    def get_queryset(self):
        """Optimizar consultas"""
        qs = super().get_queryset()
        qs = qs.select_related('dimension', 'dimension__instrumento')
        return qs
    
    def texto_corto(self, obj):
        """Mostrar versión corta del texto"""
        return obj.texto[:80] + '...' if len(obj.texto) > 80 else obj.texto
    texto_corto.short_description = 'Texto'
    
    def instrumento(self, obj):
        """Mostrar instrumento al que pertenece"""
        return obj.dimension.instrumento.nombre
    instrumento.short_description = 'Instrumento'


# ==========================================
# CRUD de Niveles de Retroalimentación
# ==========================================
class NivelRetroalimentacionAdminView(ModelCRUDView):
    """Vista CRUD para gestionar Niveles de Retroalimentación"""
    model = NivelRetroalimentacion
    form_class = NivelRetroalimentacionForm
    template_list = 'instrumentos/admin/nivel_retroalimentacion_list.html'
    template_form = 'core/forms/formAdmin.html'
    
    list_display = ['nombre_nivel', 'dimension', 'instrumento', 'rango_porcentaje', 'clase_visual_badge', 'created_at']
    search_fields = ['nombre_nivel', 'dimension__nombre', 'dimension__instrumento__nombre', 'mensaje_feedback']
    list_filter = ['dimension__instrumento', 'dimension', 'clase_visual', 'created_at']
    ordering = ['dimension__instrumento', 'dimension__orden', 'porcentaje_min']
    paginate_by = 30
    auto_complete_fields = ['dimension']
    
    # Configuración de exportación
    export_filename = 'niveles_retroalimentacion.xlsx'
    export_headers = ['ID', 'Nivel', 'Dimensión', 'Instrumento', 'Min%', 'Max%', 'Clase Visual', 'Creado']
    export_fields = ['id', 'nombre_nivel', 'dimension__nombre', 'instrumento', 'porcentaje_min', 'porcentaje_max', 'clase_visual', 'created_at']
    
    def get_queryset(self):
        """Optimizar consultas"""
        qs = super().get_queryset()
        qs = qs.select_related('dimension', 'dimension__instrumento')
        return qs
    
    def instrumento(self, obj):
        """Mostrar instrumento al que pertenece"""
        return obj.dimension.instrumento.nombre
    instrumento.short_description = 'Instrumento'
    
    def rango_porcentaje(self, obj):
        """Mostrar rango de porcentaje"""
        return f"{obj.porcentaje_min}% - {obj.porcentaje_max}%"
    rango_porcentaje.short_description = 'Rango'
    
    def clase_visual_badge(self, obj):
        """Mostrar badge con la clase visual"""
        colores = {
            'danger': 'danger',
            'warning': 'warning',
            'success': 'success',
            'info': 'info',
            'primary': 'primary',
            'secondary': 'secondary',
        }
        color = colores.get(obj.clase_visual, 'secondary')
        return f'<span class="badge bg-{color}">{obj.get_clase_visual_display()}</span>'
    clase_visual_badge.short_description = 'Color'


# ==========================================
# CRUD de Opciones de Escala
# ==========================================
class EscalaOpcionAdminView(ModelCRUDView):
    """Vista CRUD para gestionar Opciones de Escala"""
    model = EscalaOpcion
    form_class = EscalaOpcionForm
    template_list = 'instrumentos/admin/escala_opcion_list.html'
    template_form = 'core/forms/formAdmin.html'
    
    list_display = ['etiqueta', 'valor_nominal', 'instrumento', 'orden', 'created_at']
    search_fields = ['etiqueta', 'instrumento__nombre']
    list_filter = ['instrumento', 'valor_nominal', 'created_at']
    ordering = ['instrumento', 'orden']
    paginate_by = 30
    auto_complete_fields = ['instrumento']
    
    # Configuración de exportación
    export_filename = 'escalas_opciones.xlsx'
    export_headers = ['ID', 'Etiqueta', 'Valor', 'Instrumento', 'Orden', 'Creado']
    export_fields = ['id', 'etiqueta', 'valor_nominal', 'instrumento__nombre', 'orden', 'created_at']
    
    def get_queryset(self):
        """Optimizar consultas"""
        qs = super().get_queryset()
        qs = qs.select_related('instrumento')
        return qs


# ==========================================
# Vista de Intentos (Solo Lectura)
# ==========================================
class IntentoAdminView(ModelCRUDView):
    """Vista para visualizar Intentos de Evaluación (solo lectura)"""
    model = Intento
    template_list = 'instrumentos/admin/intento_list.html'
    
    list_display = ['id', 'usuario', 'instrumento', 'completado', 'inicio', 'fin', 'num_respuestas']
    search_fields = ['usuario__username', 'usuario__email', 'instrumento__nombre']
    list_filter = ['completado', 'instrumento', 'inicio', 'fin']
    ordering = ['-inicio']
    paginate_by = 30
    
    # Configuración de exportación
    export_filename = 'intentos.xlsx'
    export_headers = ['ID', 'Usuario', 'Email', 'Instrumento', 'Completado', 'Inicio', 'Fin', 'Respuestas']
    export_fields = ['id', 'usuario__username', 'usuario__email', 'instrumento__nombre', 'completado', 'inicio', 'fin', 'num_respuestas']
    
    # Sobrescribir acciones para quitar edición y eliminación
    row_actions = [
        {
            "name": "view",
            "label": "Ver Detalles",
            "icon": "fa-eye",
            "url": lambda o: f"?action=view&id={o.id}",
            "modal": True,
            'attrs': {
                'data-bs-toggle': 'tooltip',
                'title': 'Ver Detalles',
            },
        },
    ]
    
    def get_queryset(self):
        """Optimizar consultas"""
        qs = super().get_queryset()
        qs = qs.select_related('usuario', 'instrumento').annotate(
            num_respuestas=Count('respuestas')
        )
        return qs
    
    def num_respuestas(self, obj):
        """Mostrar número de respuestas"""
        return obj.respuestas.count()
    num_respuestas.short_description = 'Respuestas'
    
    def get_view(self, request, context, *args, **kwargs):
        """Vista de detalle de un intento"""
        intento_id = request.GET.get('id')
        intento = Intento.objects.select_related(
            'usuario', 'instrumento'
        ).prefetch_related(
            'respuestas__item__dimension', 'respuestas__opcion'
        ).get(id=intento_id)
        
        context['title'] = f'Detalle del Intento #{intento.id}'
        context['intento'] = intento
        context['respuestas'] = intento.respuestas.all()
        
        return render(request, 'instrumentos/admin/intento_detail.html', context)


# ==========================================
# Vista de Respuestas (Solo Lectura)
# ==========================================
class RespuestaAdminView(ModelCRUDView):
    """Vista para visualizar Respuestas (solo lectura)"""
    model = Respuesta
    template_list = 'instrumentos/admin/respuesta_list.html'
    
    list_display = ['id', 'usuario', 'intento_id', 'item_texto', 'opcion', 'created_at']
    search_fields = ['intento__usuario__username', 'item__texto']
    list_filter = ['intento__instrumento', 'intento__completado', 'created_at']
    ordering = ['-created_at']
    paginate_by = 50
    
    # Sin acciones (solo lectura)
    row_actions = []
    
    # Configuración de exportación
    export_filename = 'respuestas.xlsx'
    export_headers = ['ID', 'Usuario', 'Intento', 'Ítem', 'Opción', 'Creado']
    export_fields = ['id', 'usuario', 'intento__id', 'item__texto', 'opcion__etiqueta', 'created_at']
    
    def get_queryset(self):
        """Optimizar consultas"""
        qs = super().get_queryset()
        qs = qs.select_related(
            'intento', 'intento__usuario', 'item', 'item__dimension', 'opcion'
        )
        return qs
    
    def usuario(self, obj):
        """Mostrar usuario del intento"""
        return obj.intento.usuario.username
    usuario.short_description = 'Usuario'
    
    def intento_id(self, obj):
        """Mostrar ID del intento"""
        return f"#{obj.intento.id}"
    intento_id.short_description = 'Intento'
    
    def item_texto(self, obj):
        """Mostrar versión corta del ítem"""
        return obj.item.texto[:60] + '...' if len(obj.item.texto) > 60 else obj.item.texto
    item_texto.short_description = 'Ítem'
