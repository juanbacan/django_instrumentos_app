from django.contrib import admin
from django.utils.html import format_html
from .models import Instrumento, Dimension, Item, EscalaOpcion, Intento, Respuesta, NivelRetroalimentacion


class DimensionInline(admin.TabularInline):
	"""Inline para dimensiones dentro del instrumento"""
	model = Dimension
	extra = 1
	fields = ['nombre', 'orden']
	ordering = ['orden']


class EscalaOpcionInline(admin.TabularInline):
	"""Inline para opciones de escala dentro del instrumento"""
	model = EscalaOpcion
	extra = 1
	fields = ['etiqueta', 'valor_nominal', 'orden']
	ordering = ['orden']


@admin.register(Instrumento)
class InstrumentoAdmin(admin.ModelAdmin):
	"""Administrador para Instrumentos/Evaluaciones"""
	list_display = ['nombre', 'slug', 'activo', 'premium_badge', 'estado_badge', 'num_dimensiones', 'num_items', 'created_at']
	list_filter = ['activo', 'premium', 'created_at']
	search_fields = ['nombre', 'slug', 'descripcion']
	prepopulated_fields = {'slug': ('nombre',)}

	inlines = [DimensionInline, EscalaOpcionInline]
    
	fieldsets = (
		('Información Básica', {
			'fields': ('nombre', 'slug', 'descripcion')
		}),
		('Estado', {
			'fields': ('activo', 'premium')
		}),
	)
    
	def premium_badge(self, obj):
		"""Muestra un badge si el instrumento es premium"""
		if obj.premium:
			return format_html('<span style="background-color: #FFD700; color: #333; padding: 3px 10px; border-radius: 3px;">★ Premium</span>')
		return format_html('<span style="color: #999;">–</span>')
	premium_badge.short_description = 'Premium'
    
	def estado_badge(self, obj):
		"""Muestra un badge de estado activo/inactivo"""
		if obj.activo:
			return format_html('<span style="color: green;">●</span> Activo')
		return format_html('<span style="color: red;">●</span> Inactivo')
	estado_badge.short_description = 'Estado'
    
	def num_dimensiones(self, obj):
		"""Cuenta el número de dimensiones"""
		return obj.dimensiones.count()
	num_dimensiones.short_description = 'Dimensiones'
    
	def num_items(self, obj):
		"""Cuenta el número total de ítems"""
		return Item.objects.filter(dimension__instrumento=obj).count()
	num_items.short_description = 'Ítems'


class ItemInline(admin.TabularInline):
	"""Inline para ítems dentro de una dimensión"""
	model = Item
	extra = 1
	fields = ['texto', 'es_inverso', 'orden']
	ordering = ['orden']


class NivelRetroalimentacionInline(admin.TabularInline):
	"""Inline para niveles de retroalimentación dentro de una dimensión"""
	model = NivelRetroalimentacion
	extra = 1
	fields = ['nombre_nivel', 'porcentaje_min', 'porcentaje_max', 'mensaje_feedback']
	ordering = ['porcentaje_min']


@admin.register(Dimension)
class DimensionAdmin(admin.ModelAdmin):
	"""Administrador para Dimensiones"""
	list_display = ['nombre', 'instrumento', 'orden', 'num_items', 'created_at']
	list_filter = ['instrumento', 'created_at']
	search_fields = ['nombre', 'instrumento__nombre']
	inlines = [ItemInline, NivelRetroalimentacionInline]
    
	fieldsets = (
		(None, {
			'fields': ('instrumento', 'nombre', 'orden')
		}),
	)
    
	def num_items(self, obj):
		"""Cuenta el número de ítems en esta dimensión"""
		return obj.items.count()
	num_items.short_description = 'Ítems'


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
	"""Administrador para Ítems/Preguntas"""
	list_display = ['texto_corto', 'dimension', 'es_inverso', 'orden', 'created_at']
	list_filter = ['dimension__instrumento', 'dimension', 'es_inverso', 'created_at']
	search_fields = ['texto', 'dimension__nombre']
    
	fieldsets = (
		(None, {
			'fields': ('dimension', 'texto', 'es_inverso', 'orden')
		}),
	)
    
	def texto_corto(self, obj):
		"""Muestra una versión corta del texto del ítem"""
		return obj.texto[:60] + '...' if len(obj.texto) > 60 else obj.texto
	texto_corto.short_description = 'Texto'


@admin.register(EscalaOpcion)
class EscalaOpcionAdmin(admin.ModelAdmin):
	"""Administrador para Opciones de Escala"""
	list_display = ['etiqueta', 'valor_nominal', 'instrumento', 'orden', 'created_at']
	list_filter = ['instrumento', 'created_at']
	search_fields = ['etiqueta', 'instrumento__nombre']
    
	fieldsets = (
		(None, {
			'fields': ('instrumento', 'etiqueta', 'valor_nominal', 'orden')
		}),
	)


class RespuestaInline(admin.TabularInline):
	"""Inline para respuestas dentro de un intento"""
	model = Respuesta
	extra = 0
	fields = ['item', 'opcion']
	readonly_fields = ['item', 'opcion']
	can_delete = False
    
	def has_add_permission(self, request, obj=None):
		return False


@admin.register(Intento)
class IntentoAdmin(admin.ModelAdmin):
	"""Administrador para Intentos de Evaluación"""
	list_display = ['id', 'usuario', 'instrumento', 'completado', 'estado_badge', 'inicio', 'fin', 'num_respuestas']
	list_filter = ['completado', 'instrumento', 'inicio', 'fin']
	search_fields = ['usuario__username', 'usuario__email', 'instrumento__nombre']
	readonly_fields = ['inicio', 'fin', 'resultados_brutos', 'ver_resultados_json']
	inlines = [RespuestaInline]
    
	fieldsets = (
		('Información del Intento', {
			'fields': ('usuario', 'instrumento', 'completado')
		}),
		('Fechas', {
			'fields': ('inicio', 'fin')
		}),
		('Resultados', {
			'fields': ('resultados_brutos', 'ver_resultados_json'),
			'classes': ('collapse',)
		}),
	)
    
	def estado_badge(self, obj):
		"""Muestra un badge del estado del intento"""
		if obj.completado:
			return format_html('<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">✓ Completado</span>')
		return format_html('<span style="background-color: #ffc107; color: black; padding: 3px 10px; border-radius: 3px;">○ En Progreso</span>')
	estado_badge.short_description = 'Estado'
    
	def num_respuestas(self, obj):
		"""Cuenta el número de respuestas"""
		return obj.respuestas.count()
	num_respuestas.short_description = 'Respuestas'
    
	def ver_resultados_json(self, obj):
		"""Muestra los resultados en formato legible con puntajes y porcentajes"""
		if obj.resultados_brutos:
			html = '<table style="border-collapse: collapse; width: 100%;">'
			html += '<tr style="background-color: #f8f9fa;"><th style="border: 1px solid #ddd; padding: 8px;">Dimensión</th><th style="border: 1px solid #ddd; padding: 8px;">Puntaje</th><th style="border: 1px solid #ddd; padding: 8px;">Máximo</th><th style="border: 1px solid #ddd; padding: 8px;">Porcentaje</th></tr>'
			for dimension, datos in obj.resultados_brutos.items():
				# Manejar formato antiguo (solo número) y formato nuevo (dict con puntaje, máximo, porcentaje)
				if isinstance(datos, dict):
					puntaje = datos.get('puntaje_obtenido', 0)
					maximo = datos.get('puntaje_maximo', 0)
					porcentaje = datos.get('porcentaje', 0)
					html += f'<tr><td style="border: 1px solid #ddd; padding: 8px;"><strong>{dimension}</strong></td><td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{puntaje}</td><td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{maximo}</td><td style="border: 1px solid #ddd; padding: 8px; text-align: center;"><strong>{porcentaje}%</strong></td></tr>'
				else:
					# Formato antiguo: solo número
					html += f'<tr><td style="border: 1px solid #ddd; padding: 8px;"><strong>{dimension}</strong></td><td style="border: 1px solid #ddd; padding: 8px; text-align: center;" colspan="3">{datos}</td></tr>'
			html += '</table>'
			return format_html(html)
		return 'No hay resultados disponibles'
	ver_resultados_json.short_description = 'Resultados Detallados'


@admin.register(Respuesta)
class RespuestaAdmin(admin.ModelAdmin):
	"""Administrador para Respuestas"""
	list_display = ['intento', 'item_texto', 'opcion', 'created_at']
	list_filter = ['intento__instrumento', 'intento__completado', 'created_at']
	search_fields = ['intento__usuario__username', 'item__texto']
	readonly_fields = ['intento', 'item', 'opcion', 'created_at']
    
	fieldsets = (
		(None, {
			'fields': ('intento', 'item', 'opcion', 'created_at')
		}),
	)
    
	def item_texto(self, obj):
		"""Muestra una versión corta del texto del ítem"""
		return obj.item.texto[:50] + '...' if len(obj.item.texto) > 50 else obj.item.texto
	item_texto.short_description = 'Ítem'
    
	def has_add_permission(self, request):
		# No permitir agregar respuestas manualmente desde el admin
		return False
    
	def has_delete_permission(self, request, obj=None):
		# No permitir eliminar respuestas individuales
		return False


@admin.register(NivelRetroalimentacion)
class NivelRetroalimentacionAdmin(admin.ModelAdmin):
	"""Administrador para Niveles de Retroalimentación"""
	list_display = ['nombre_nivel', 'dimension', 'rango_porcentaje', 'created_at']
	list_filter = ['dimension__instrumento', 'dimension', 'created_at']
	search_fields = ['nombre_nivel', 'dimension__nombre', 'mensaje_feedback']
	ordering = ['dimension', 'porcentaje_min']
    
	fieldsets = (
		('Información del Nivel', {
			'fields': ('dimension', 'nombre_nivel')
		}),
		('Rango de Porcentaje', {
			'fields': ('porcentaje_min', 'porcentaje_max'),
			'description': 'Define el rango de porcentaje en el que este nivel de retroalimentación será aplicable'
		}),
		('Mensaje de Retroalimentación', {
			'fields': ('mensaje_feedback',),
			'classes': ('wide',)
		}),
	)
    
	def rango_porcentaje(self, obj):
		"""Muestra el rango de porcentaje de forma legible"""
		return f"{obj.porcentaje_min}% - {obj.porcentaje_max}%"
	rango_porcentaje.short_description = 'Rango'
