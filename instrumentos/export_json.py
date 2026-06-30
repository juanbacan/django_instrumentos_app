"""
Exportación de instrumentos al formato JSON usado por la importación del admin.
"""
from .models import Instrumento


def build_test_json(instrumento):
    """Construye el dict exportable de un instrumento y su contenido relacionado."""
    if isinstance(instrumento, (int, str)):
        instrumento = (
            Instrumento.objects
            .prefetch_related(
                'opciones',
                'dimensiones__items',
                'dimensiones__niveles_retroalimentacion',
            )
            .get(pk=instrumento)
        )

    payload = {
        'instrumento': {
            'nombre': instrumento.nombre,
            'slug': instrumento.slug,
            'descripcion': instrumento.descripcion,
            'activo': instrumento.activo,
            'premium': instrumento.premium,
            'tiempo_limite_activo': instrumento.tiempo_limite_activo,
            'tiempo_limite_minutos': instrumento.tiempo_limite_minutos,
        },
        'escalas': [
            {
                'etiqueta': opcion.etiqueta,
                'valor': opcion.valor_nominal,
                'orden': opcion.orden,
            }
            for opcion in instrumento.opciones.order_by('orden', 'valor_nominal')
        ],
        'dimensiones': [],
    }

    for dimension in instrumento.dimensiones.order_by('orden', 'id'):
        dim_data = {
            'nombre': dimension.nombre,
            'orden': dimension.orden,
            'items': [
                {
                    'texto': item.texto,
                    'es_inverso': item.es_inverso,
                    'orden': item.orden,
                }
                for item in dimension.items.order_by('orden', 'id')
            ],
        }

        niveles = list(dimension.niveles_retroalimentacion.order_by('porcentaje_min', 'id'))
        if niveles:
            dim_data['niveles_retroalimentacion'] = [
                {
                    'nombre_nivel': nivel.nombre_nivel,
                    'porcentaje_min': float(nivel.porcentaje_min),
                    'porcentaje_max': float(nivel.porcentaje_max),
                    'mensaje_feedback': nivel.mensaje_feedback,
                    'clase_visual': nivel.clase_visual,
                }
                for nivel in niveles
            ]

        payload['dimensiones'].append(dim_data)

    return payload
