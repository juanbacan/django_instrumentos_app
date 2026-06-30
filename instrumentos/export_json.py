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
                'dimensiones__items__opciones',
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
            'tipo_instrumento': instrumento.tipo_instrumento,
        },
        'dimensiones': [],
    }

    if instrumento.es_escala_likert:
        payload['escalas'] = [
            {
                'etiqueta': opcion.etiqueta,
                'valor': opcion.valor_nominal,
                'orden': opcion.orden,
            }
            for opcion in instrumento.opciones.order_by('orden', 'valor_nominal')
        ]
    else:
        payload['escalas'] = []

    for dimension in instrumento.dimensiones.order_by('orden', 'id'):
        dim_data = {
            'nombre': dimension.nombre,
            'orden': dimension.orden,
            'items': [],
        }

        if instrumento.es_escala_likert:
            dim_data['items'] = [
                {
                    'texto': item.texto,
                    'es_inverso': item.es_inverso,
                    'orden': item.orden,
                }
                for item in dimension.items.order_by('orden', 'id')
            ]
        else:
            for item in dimension.items.order_by('orden', 'id'):
                dim_data['items'].append({
                    'texto_pregunta': item.texto,
                    'orden': item.orden,
                    'opciones': [
                        {
                            'texto': opcion.texto,
                            'valor': opcion.valor,
                            'orden': opcion.orden,
                        }
                        for opcion in item.opciones.order_by('orden', 'valor')
                    ],
                })

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
