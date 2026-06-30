"""
Importación de tests desde JSON (formato compatible con export_json).
"""
import json

from django.db import transaction

from .models import Instrumento, Dimension, Item, EscalaOpcion, NivelRetroalimentacion


class ImportTestError(Exception):
    """Error de validación o importación de un test JSON."""


def validate_test_json_structure(data):
    if not isinstance(data, dict):
        raise ImportTestError('El JSON debe ser un objeto.')
    for key in ('instrumento', 'escalas', 'dimensiones'):
        if key not in data:
            raise ImportTestError(f'El JSON debe contener la clave "{key}"')
    if not isinstance(data['instrumento'], dict):
        raise ImportTestError('La clave "instrumento" debe ser un objeto.')
    if 'slug' not in data['instrumento']:
        raise ImportTestError('El JSON debe incluir instrumento.slug')
    if not isinstance(data['escalas'], list):
        raise ImportTestError('La clave "escalas" debe ser una lista.')
    if not isinstance(data['dimensiones'], list):
        raise ImportTestError('La clave "dimensiones" debe ser una lista.')


def parse_test_json_text(json_text):
    try:
        return json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise ImportTestError(f'Error al leer el JSON: {exc}') from exc


def parse_test_json_file(json_file):
    try:
        content = json_file.read().decode('utf-8')
    except UnicodeDecodeError as exc:
        raise ImportTestError('No se pudo decodificar el archivo. Usa UTF-8.') from exc
    return parse_test_json_text(content)


def load_test_json_from_form(form):
    json_file = form.cleaned_data.get('json_file')
    json_text = (form.cleaned_data.get('json_text') or '').strip()
    if json_text:
        return parse_test_json_text(json_text)
    if json_file:
        return parse_test_json_file(json_file)
    raise ImportTestError('Debes subir un archivo JSON o pegar el contenido JSON en la caja de texto.')


@transaction.atomic
def import_test_from_json(data, instrumento_objetivo=None):
    """
    Crea o actualiza un instrumento desde JSON.

    Si `instrumento_objetivo` se indica, actualiza ese registro (reemplaza escalas,
    dimensiones, ítems y retroalimentación). El slug del JSON debe coincidir
    o se fuerza al del instrumento objetivo.
    """
    validate_test_json_structure(data)
    instrumento_data = dict(data['instrumento'])
    reemplazado = instrumento_objetivo is not None

    if instrumento_objetivo is not None:
        json_slug = instrumento_data.get('slug')
        if json_slug and json_slug != instrumento_objetivo.slug:
            raise ImportTestError(
                f'El slug del JSON ("{json_slug}") no coincide con el test '
                f'seleccionado ("{instrumento_objetivo.slug}").'
            )
        instrumento_data['slug'] = instrumento_objetivo.slug
        instrumento_objetivo.dimensiones.all().delete()
        instrumento_objetivo.opciones.all().delete()
        instrumento = instrumento_objetivo
        created = False
        instrumento.nombre = instrumento_data['nombre']
        instrumento.descripcion = instrumento_data.get('descripcion', '')
        instrumento.activo = instrumento_data.get('activo', True)
        instrumento.premium = instrumento_data.get('premium', False)
        instrumento.tiempo_limite_activo = instrumento_data.get('tiempo_limite_activo', False)
        instrumento.tiempo_limite_minutos = instrumento_data.get('tiempo_limite_minutos')
        instrumento.save()
    else:
        instrumento, created = Instrumento.objects.update_or_create(
            slug=instrumento_data['slug'],
            defaults={
                'nombre': instrumento_data['nombre'],
                'descripcion': instrumento_data.get('descripcion', ''),
                'activo': instrumento_data.get('activo', True),
                'premium': instrumento_data.get('premium', False),
                'tiempo_limite_activo': instrumento_data.get('tiempo_limite_activo', False),
                'tiempo_limite_minutos': instrumento_data.get('tiempo_limite_minutos'),
            },
        )

    for escala_data in data['escalas']:
        EscalaOpcion.objects.update_or_create(
            instrumento=instrumento,
            valor_nominal=escala_data['valor'],
            defaults={
                'etiqueta': escala_data['etiqueta'],
                'orden': escala_data.get('orden', escala_data['valor']),
            },
        )

    total_niveles = 0
    for dimension_data in data['dimensiones']:
        dimension, _ = Dimension.objects.update_or_create(
            instrumento=instrumento,
            nombre=dimension_data['nombre'],
            defaults={
                'orden': dimension_data.get('orden', 1),
            },
        )

        for item_data in dimension_data.get('items', []):
            Item.objects.update_or_create(
                dimension=dimension,
                texto=item_data['texto'],
                defaults={
                    'es_inverso': item_data.get('es_inverso', False),
                    'orden': item_data.get('orden', 1),
                },
            )

        for nivel_data in dimension_data.get('niveles_retroalimentacion', []):
            NivelRetroalimentacion.objects.update_or_create(
                dimension=dimension,
                nombre_nivel=nivel_data['nombre_nivel'],
                defaults={
                    'porcentaje_min': nivel_data['porcentaje_min'],
                    'porcentaje_max': nivel_data['porcentaje_max'],
                    'mensaje_feedback': nivel_data['mensaje_feedback'],
                    'clase_visual': nivel_data.get('clase_visual', 'secondary'),
                },
            )
            total_niveles += 1

    total_dimensiones = len(data['dimensiones'])
    total_items = sum(len(d.get('items', [])) for d in data['dimensiones'])

    return {
        'instrumento': instrumento,
        'created': created,
        'total_dimensiones': total_dimensiones,
        'total_items': total_items,
        'total_niveles': total_niveles,
        'reemplazado': reemplazado,
    }
