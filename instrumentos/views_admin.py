"""
Vistas de administración para el módulo de Instrumentos/Evaluaciones.
Estas vistas extienden de ModelCRUDView para proporcionar interfaces
de administración completas con listado, creación, edición y eliminación.
"""
import json
from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Q
from django.contrib import messages
from django.http import HttpResponse

from core.views import ViewAdministracionBase, ModelCRUDView
from core.utils import success_json, error_json, get_redirect_url

from .models import Instrumento, Dimension, Item, EscalaOpcion, Intento, Respuesta, NivelRetroalimentacion
from .forms import InstrumentoForm, DimensionForm, ItemForm, EscalaOpcionForm, ImportarTestForm, NivelRetroalimentacionForm
from .export_json import build_test_json
from .import_json import ImportTestError, import_test_from_json, load_test_json_from_form


def _import_json_help_message(instrumento=None):
    intro = '''
        <div class="alert alert-info mt-2">
            <strong><i class="fa-solid fa-circle-info me-2"></i>Formato JSON:</strong>
            Debe contener <code>instrumento</code> y <code>dimensiones</code>.
            <br><small class="text-muted">
                <code>instrumento.tipo_instrumento</code>: <code>escala_likert</code> (default, requiere <code>escalas</code>)
                o <code>opciones_progresivas</code> (4 opciones por ítem, sin escalas globales).
                Opcional: <code>premium</code>, <code>tiempo_limite_*</code>, <code>niveles_retroalimentacion</code>.
            </small>
    '''
    if instrumento:
        intro += f'''
            <hr class="my-2">
            <p class="mb-1"><strong>Test a actualizar:</strong> {instrumento.nombre}</p>
            <p class="mb-0 small">Slug obligatorio: <code>{instrumento.slug}</code>. Se reemplazarán escalas, dimensiones, ítems y retroalimentación de este test.</p>
        '''
    intro += '</div>'
    return intro


def _success_import_message(result):
    instrumento = result['instrumento']
    if result['reemplazado']:
        verb = 'actualizado'
    else:
        verb = 'creado' if result['created'] else 'actualizado'
    return (
        f'✅ Test "{instrumento.nombre}" {verb} con '
        f'{result["total_dimensiones"]} dimensiones, {result["total_items"]} ítems '
        f'y {result["total_niveles"]} diagnósticos.'
    )


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
    
    list_display = ['nombre', 'slug', 'activo', 'tiempo_configurado', 'num_dimensiones', 'num_items', 'premium', 'created_at']
    search_fields = ['nombre', 'slug', 'descripcion']
    list_filter = ['activo', 'premium', 'tiempo_limite_activo', 'created_at']
    ordering = ['-created_at']
    paginate_by = 20

    row_actions = [
        {
            "name": "edit",
            "label": "Editar",
            "icon": "fa-pencil",
            "url": lambda o: f"?action=edit&id={o.id}",
            'attrs': {
                'data-bs-toggle': 'tooltip',
                'title': 'Editar',
            },
        },
        {
            "name": "ver_json",
            "label": "Ver JSON",
            "icon": "fa-code",
            "url": lambda o: f"?action=ver_json&id={o.id}",
            "modal": True,
            'attrs': {
                'data-bs-toggle': 'tooltip',
                'title': 'Ver test en JSON',
            },
        },
        {
            "name": "descargar_json",
            "label": "Descargar JSON",
            "icon": "fa-download",
            "url": lambda o: f"?action=descargar_json&id={o.id}",
            'attrs': {
                'data-bs-toggle': 'tooltip',
                'title': 'Descargar test en JSON',
            },
        },
        {
            "name": "importar_test",
            "label": "Importar JSON",
            "icon": "fa-file-import",
            "url": lambda o: f"?action=importar_test&id={o.id}",
            "modal": True,
            'attrs': {
                'data-bs-toggle': 'tooltip',
                'title': 'Actualizar este test desde JSON',
            },
        },
        {
            "name": "delete",
            "label": "Eliminar",
            "icon": "fa-trash",
            "url": lambda o: f"?action=delete&id={o.id}",
            "modal": True,
            'attrs': {
                'data-bs-toggle': 'tooltip',
                'title': 'Eliminar',
            },
        },
    ]
    
    # Configuración de exportación
    export_filename = 'instrumentos.xlsx'
    export_headers = ['ID', 'Nombre', 'Slug', 'Activo', 'Tiempo', 'Dimensiones', 'Ítems', 'Creado']
    export_fields = ['id', 'nombre', 'slug', 'activo', lambda o: o.tiempo_limite_texto(), 'num_dimensiones', 'num_items', 'created_at']
    
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

    def tiempo_configurado(self, obj):
        return obj.tiempo_limite_texto()
    tiempo_configurado.short_description = 'Tiempo'
    
    def num_items(self, obj):
        """Mostrar número total de ítems"""
        return Item.objects.filter(dimension__instrumento=obj).count()
    num_items.short_description = 'Ítems'

    def get_descargar_json(self, request, context, *args, **kwargs):
        """Descarga un instrumento completo en formato JSON (compatible con importar)."""
        instrumento_id = request.GET.get('id') or getattr(self, 'data', {}).get('id')
        instrumento = get_object_or_404(self.model, pk=instrumento_id)
        payload = build_test_json(instrumento)
        content = json.dumps(payload, ensure_ascii=False, indent=2)
        response = HttpResponse(content, content_type='application/json; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{instrumento.slug}.json"'
        return response

    def get_ver_json(self, request, context, *args, **kwargs):
        """Muestra el JSON del test en un modal (sin descargar)."""
        instrumento_id = request.GET.get('id') or getattr(self, 'data', {}).get('id')
        instrumento = get_object_or_404(self.model, pk=instrumento_id)
        payload = build_test_json(instrumento)
        context.update({
            'title': f'JSON · {instrumento.nombre}',
            'instrumento': instrumento,
            'json_text': json.dumps(payload, ensure_ascii=False, indent=2),
            'descargar_url': f'{request.path}?action=descargar_json&id={instrumento.id}',
        })
        return render(request, 'instrumentos/admin/instrumento_json_modal.html', context)
    
        return render(request, 'instrumentos/admin/instrumento_json_modal.html', context)

    def get_importar(self, request, context, *args, **kwargs):
        """Mostrar formulario para importar un test nuevo desde JSON."""
        context['title'] = 'Importar Test desde JSON'
        context['form'] = ImportarTestForm()
        context['action'] = 'importar'
        context['message'] = _import_json_help_message()
        return render(request, 'core/modals/formModal.html', context)

    def get_importar_test(self, request, context, *args, **kwargs):
        """Modal para actualizar un test existente mediante JSON."""
        instrumento_id = request.GET.get('id') or getattr(self, 'data', {}).get('id')
        instrumento = get_object_or_404(self.model, pk=instrumento_id)
        context.update({
            'title': f'Importar / actualizar · {instrumento.nombre}',
            'form': ImportarTestForm(),
            'action': 'importar_test',
            'formid': instrumento.id,
            'message': _import_json_help_message(instrumento),
        })
        return render(request, 'core/modals/formModal.html', context)

    def _procesar_importacion(self, request, form, instrumento_objetivo=None):
        if not form.is_valid():
            return error_json('Formulario no válido. Por favor, revisa los campos e intenta de nuevo.', forms=[form])
        try:
            data = load_test_json_from_form(form)
            result = import_test_from_json(data, instrumento_objetivo=instrumento_objetivo)
            messages.success(request, _success_import_message(result))
            return success_json({
                'mensaje': 'Test actualizado exitosamente' if result['reemplazado'] else (
                    'Test creado exitosamente' if result['created'] else 'Test actualizado exitosamente'
                ),
                'url': request.path,
            })
        except ImportTestError as exc:
            return error_json(str(exc))
        except Exception as exc:
            return error_json(f'Error al importar: {exc}')

    def post_importar(self, request, context, *args, **kwargs):
        """Procesar importación de un test nuevo desde JSON."""
        form = ImportarTestForm(request.POST, request.FILES)
        return self._procesar_importacion(request, form)

    def post_importar_test(self, request, context, *args, **kwargs):
        """Procesar actualización de un test existente desde JSON."""
        instrumento_id = request.POST.get('id') or getattr(self, 'data', {}).get('id')
        instrumento = get_object_or_404(self.model, pk=instrumento_id)
        form = ImportarTestForm(request.POST, request.FILES)
        return self._procesar_importacion(request, form, instrumento_objetivo=instrumento)


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
