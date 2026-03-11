from django.db import models
from django.conf import settings
from django.db.models import Max, Min
from django.utils import timezone

from core.models import ModeloBase

class Instrumento(ModeloBase):
    """Contenedor principal: p.ej. 'Dimensión 2 - Socioemocional' o 'RIASEC'"""
    nombre = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    premium = models.BooleanField(
        default=False,
        help_text="Si está marcado, solo usuarios con acceso premium podrán completar este test"
    )

    def __str__(self):
        return self.nombre
    
    def num_items(self):
        """Cuenta total de ítems asociados a este instrumento"""
        return Item.objects.filter(dimension__instrumento=self).count()


class AccesoPremiumInstrumento(ModeloBase):
    """Registro de usuarios con acceso premium a instrumentos específicos"""
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='accesos_premium',
        on_delete=models.CASCADE
    )
    instrumento = models.ForeignKey(
        Instrumento,
        related_name='accesos_usuarios',
        on_delete=models.CASCADE
    )
    activo = models.BooleanField(
        default=True,
        help_text="Si está inactivo, el usuario pierde acceso a este test premium"
    )
    fecha_expiracion = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha en que expira el acceso (opcional)"
    )

    class Meta:
        unique_together = ('usuario', 'instrumento')
        verbose_name = 'Acceso Premium a Instrumento'
        verbose_name_plural = 'Accesos Premium a Instrumentos'

    def __str__(self):
        return f"{self.usuario.username} → {self.instrumento.nombre}"

    @property
    def esta_vigente(self):
        """Verifica si el acceso aún es válido"""
        if not self.activo:
            return False
        if self.fecha_expiracion:
            return self.fecha_expiracion > timezone.now()
        return True


class Dimension(ModeloBase):
    """Categorías: p.ej. 'Empatía', 'Autorregulación', 'Realista'"""
    instrumento = models.ForeignKey(Instrumento, related_name='dimensiones', on_delete=models.CASCADE)
    nombre = models.CharField(max_length=200)
    orden = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.instrumento.nombre} - {self.nombre}"


class NivelRetroalimentacion(ModeloBase):
    """Diagnóstico y consejo basado en el rango de puntaje de una dimensión.
    Permite definir mensajes dinámicos según el porcentaje obtenido (Bajo/Medio/Alto, etc.)
    """
    dimension = models.ForeignKey(Dimension, related_name='niveles_retroalimentacion', on_delete=models.CASCADE)
    
    # Nombre del nivel: "Requiere Atención (Bajo)", "Adecuado (Medio)", "Óptimo (Alto)"
    nombre_nivel = models.CharField(max_length=200, help_text="Ej: Bajo, Medio, Alto")
    
    # Rangos en porcentaje (0 a 100) para universalidad
    porcentaje_min = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Porcentaje mínimo (ej: 0.00)"
    )
    porcentaje_max = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Porcentaje máximo (ej: 33.33)"
    )
    
    # El texto rico con diagnóstico y recomendaciones
    mensaje_feedback = models.TextField(
        help_text="Diagnóstico y recomendaciones que verá el usuario cuando caiga en este rango"
    )
    
    # Opciones de clases visuales Bootstrap
    CLASE_VISUAL_CHOICES = [
        ('danger', 'Rojo (Peligro) - Para niveles bajos o críticos'),
        ('warning', 'Amarillo (Advertencia) - Para niveles medios o en desarrollo'),
        ('success', 'Verde (Éxito) - Para niveles altos o sobresalientes'),
        ('info', 'Azul (Información) - Para niveles informativos'),
        ('primary', 'Azul primario - Para destacar'),
        ('secondary', 'Gris - Neutral por defecto'),
    ]
    
    # Clase visual para representación de colores (opcional)
    clase_visual = models.CharField(
        max_length=20,
        choices=CLASE_VISUAL_CHOICES,
        default='secondary',
        help_text="Color para representar visualmente este nivel de retroalimentación"
    )

    class Meta:
        ordering = ['dimension', 'porcentaje_min']

    def __str__(self):
        return f"[{self.dimension.nombre}] {self.nombre_nivel} ({self.porcentaje_min}% - {self.porcentaje_max}%)"


class Item(ModeloBase):
    """La afirmación o pregunta individual"""
    dimension = models.ForeignKey(Dimension, related_name='items', on_delete=models.CASCADE)
    texto = models.TextField()
    es_inverso = models.BooleanField(
        default=False, 
        help_text="Si es True, la puntuación se invierte (5=1, 4=2...)"
    )
    orden = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"[{self.dimension.nombre}] {self.texto[:50]}..."


class EscalaOpcion(ModeloBase):
    """Opciones de respuesta: p.ej. 'Siempre' (5 pts), 'Nunca' (1 pt)"""
    instrumento = models.ForeignKey(Instrumento, related_name='opciones', on_delete=models.CASCADE)
    etiqueta = models.CharField(max_length=200) # p.ej. "Siempre"
    valor_nominal = models.PositiveIntegerField() # p.ej. 5
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['orden']

    def __str__(self):
        return f"{self.etiqueta} ({self.valor_nominal} pts)"


class Intento(ModeloBase):
    """Registro de cuando un usuario toma un test específico"""
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='intentos', on_delete=models.CASCADE)
    instrumento = models.ForeignKey(Instrumento, on_delete=models.CASCADE)
    inicio = models.DateTimeField(auto_now_add=True)
    fin = models.DateTimeField(null=True, blank=True)
    completado = models.BooleanField(default=False)
    
    # Almacena los puntajes finales por dimensión
    resultados_brutos = models.JSONField(null=True, blank=True, help_text="Almacena los puntajes finales por dimensión")
    
    # Almacena el orden aleatorio de los ítems (lista de IDs) para mantener consistencia
    orden_items = models.JSONField(null=True, blank=True, help_text="Orden aleatorizado de los IDs de ítems")

    def __str__(self):
        return f"{self.instrumento.nombre} - {self.usuario.username}"

    def calcular_resultados(self):
        """Calcula puntajes brutos y porcentajes por dimensión considerando ítems inversos.
        Devuelve un dict con puntaje_obtenido, puntaje_maximo y porcentaje para cada dimensión.
        """
        respuestas = self.respuestas.select_related('item__dimension', 'opcion')
        opciones = self.instrumento.opciones.all()
        
        if not opciones.exists() or not respuestas.exists():
            return {}

        max_val = opciones.aggregate(Max('valor_nominal'))['valor_nominal__max']
        min_val = opciones.aggregate(Min('valor_nominal'))['valor_nominal__min']
        constante_inversion = max_val + min_val

        # Diccionario temporal para acumular datos
        calculo_temp = {}

        for r in respuestas:
            dim_nombre = r.item.dimension.nombre
            dim_id = r.item.dimension.id
            valor_seleccionado = r.opcion.valor_nominal
            
            puntaje_final = (
                constante_inversion - valor_seleccionado
                if r.item.es_inverso
                else valor_seleccionado
            )
            
            if dim_nombre not in calculo_temp:
                calculo_temp[dim_nombre] = {
                    'dimension_id': dim_id,
                    'puntaje_obtenido': 0,
                    'items_count': 0
                }
            
            calculo_temp[dim_nombre]['puntaje_obtenido'] += puntaje_final
            calculo_temp[dim_nombre]['items_count'] += 1

        # Formatear el JSON final con porcentajes
        resultados = {}
        for dim_nombre, datos in calculo_temp.items():
            puntaje_max_posible = datos['items_count'] * max_val
            puntaje_min_posible = datos['items_count'] * min_val
            
            # Fórmula de porcentaje ajustada a la escala mínima
            rango_total = puntaje_max_posible - puntaje_min_posible
            puntaje_ajustado = datos['puntaje_obtenido'] - puntaje_min_posible
            
            porcentaje = (
                (puntaje_ajustado / rango_total) * 100
                if rango_total > 0
                else 0
            )
            
            resultados[dim_nombre] = {
                'dimension_id': datos['dimension_id'],
                'puntaje_obtenido': datos['puntaje_obtenido'],
                'puntaje_maximo': puntaje_max_posible,
                'porcentaje': round(porcentaje, 2)
            }
            
        return resultados

    def finalizar_test(self):
        """Llama a este método cuando el usuario envíe la última pregunta"""
        self.completado = True
        self.fin = timezone.now()
        self.resultados_brutos = self.calcular_resultados()
        self.save()


class Respuesta(ModeloBase):
    """La elección del usuario para cada ítem"""
    intento = models.ForeignKey(Intento, related_name='respuestas', on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    opcion = models.ForeignKey(EscalaOpcion, on_delete=models.CASCADE)

    def __str__(self):
        return f"Respuesta de {self.intento.usuario} a Item {self.item.id}"