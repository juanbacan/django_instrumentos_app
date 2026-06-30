"""
Importación de tests desde JSON (formato compatible con export_json).
"""
import json

from django.db import transaction

from .models import (
    Instrumento,
    Dimension,
    Item,
    ItemOpcion,
    EscalaOpcion,
    NivelRetroalimentacion,
)


class ImportTestError(Exception):
    """Error de validación o importación de un test JSON."""


def _get_tipo_instrumento(data):
    instrumento = data.get('instrumento') or {}
    tipo = instrumento.get('tipo_instrumento', Instrumento.TIPO_ESCALA_LIKERT)
    validos = {choice[0] for choice in Instrumento.TIPO_INSTRUMENTO_CHOICES}
    if tipo not in validos:
        raise ImportTestError(
            f'tipo_instrumento inválido: "{tipo}". '
            f'Valores permitidos: {", ".join(sorted(validos))}.'
        )
    return tipo


def _validate_escala_likert(data):
    if 'escalas' not in data:
        raise ImportTestError('Para tipo escala_likert el JSON debe contener la clave "escalas".')
    if not isinstance(data['escalas'], list) or not data['escalas']:
        raise ImportTestError('Para tipo escala_likert "escalas" debe ser una lista no vacía.')

    for dim_idx, dimension_data in enumerate(data['dimensiones'], start=1):
        for item_idx, item_data in enumerate(dimension_data.get('items', []), start=1):
            prefix = f'dimensiones[{dim_idx}].items[{item_idx}]'
            if 'opciones' in item_data:
                raise ImportTestError(
                    f'{prefix}: los ítems Likert no deben incluir "opciones". '
                    'Use texto, es_inverso y orden.'
                )
            if 'texto_pregunta' in item_data and 'texto' not in item_data:
                raise ImportTestError(
                    f'{prefix}: use "texto" en lugar de "texto_pregunta" para escala_likert.'
                )
            if 'texto' not in item_data:
                raise ImportTestError(f'{prefix}: falta el campo "texto".')


def _validate_opciones_progresivas(data):
    if 'escalas' in data and data['escalas']:
        raise ImportTestError(
            'Para tipo opciones_progresivas "escalas" debe omitirse o ser una lista vacía.'
        )

    for dim_idx, dimension_data in enumerate(data['dimensiones'], start=1):
        for item_idx, item_data in enumerate(dimension_data.get('items', []), start=1):
            prefix = f'dimensiones[{dim_idx}].items[{item_idx}]'
            if 'texto' in item_data or 'es_inverso' in item_data:
                raise ImportTestError(
                    f'{prefix}: formato Likert detectado (texto/es_inverso). '
                    'Use texto_pregunta, orden y opciones.'
                )
            if 'texto_pregunta' not in item_data:
                raise ImportTestError(f'{prefix}: falta el campo "texto_pregunta".')
            opciones = item_data.get('opciones')
            if not isinstance(opciones, list) or len(opciones) != 4:
                raise ImportTestError(
                    f'{prefix}: debe incluir exactamente 4 "opciones".'
                )
            valores_vistos = set()
            for op_idx, opcion_data in enumerate(opciones, start=1):
                op_prefix = f'{prefix}.opciones[{op_idx}]'
                if not isinstance(opcion_data, dict):
                    raise ImportTestError(f'{op_prefix}: debe ser un objeto.')
                if 'texto' not in opcion_data or not str(opcion_data['texto']).strip():
                    raise ImportTestError(f'{op_prefix}: falta "texto" o está vacío.')
                if 'valor' not in opcion_data:
                    raise ImportTestError(f'{op_prefix}: falta "valor".')
                try:
                    valor = int(opcion_data['valor'])
                except (TypeError, ValueError) as exc:
                    raise ImportTestError(f'{op_prefix}: "valor" debe ser un entero.') from exc
                if valor < 1 or valor > 4:
                    raise ImportTestError(f'{op_prefix}: "valor" debe estar entre 1 y 4.')
                if valor in valores_vistos:
                    raise ImportTestError(f'{prefix}: los valores de opciones deben ser únicos (1-4).')
                valores_vistos.add(valor)


def validate_test_json_structure(data):
    if not isinstance(data, dict):
        raise ImportTestError('El JSON debe ser un objeto.')
    for key in ('instrumento', 'dimensiones'):
        if key not in data:
            raise ImportTestError(f'El JSON debe contener la clave "{key}"')
    if not isinstance(data['instrumento'], dict):
        raise ImportTestError('La clave "instrumento" debe ser un objeto.')
    if 'slug' not in data['instrumento']:
        raise ImportTestError('El JSON debe incluir instrumento.slug')
    if not isinstance(data['dimensiones'], list):
        raise ImportTestError('La clave "dimensiones" debe ser una lista.')

    tipo = _get_tipo_instrumento(data)
    if tipo == Instrumento.TIPO_ESCALA_LIKERT:
        _validate_escala_likert(data)
    else:
        _validate_opciones_progresivas(data)


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


def _apply_instrumento_fields(instrumento, instrumento_data):
    instrumento.nombre = instrumento_data['nombre']
    instrumento.descripcion = instrumento_data.get('descripcion', '')
    instrumento.activo = instrumento_data.get('activo', True)
    instrumento.premium = instrumento_data.get('premium', False)
    instrumento.tiempo_limite_activo = instrumento_data.get('tiempo_limite_activo', False)
    instrumento.tiempo_limite_minutos = instrumento_data.get('tiempo_limite_minutos')
    instrumento.tipo_instrumento = instrumento_data.get(
        'tipo_instrumento',
        Instrumento.TIPO_ESCALA_LIKERT,
    )
    instrumento.save()


def _import_escalas_likert(instrumento, escalas_data):
    for escala_data in escalas_data:
        EscalaOpcion.objects.update_or_create(
            instrumento=instrumento,
            valor_nominal=escala_data['valor'],
            defaults={
                'etiqueta': escala_data['etiqueta'],
                'orden': escala_data.get('orden', escala_data['valor']),
            },
        )


def _import_items_likert(dimension, items_data):
    for item_data in items_data:
        Item.objects.update_or_create(
            dimension=dimension,
            texto=item_data['texto'],
            defaults={
                'es_inverso': item_data.get('es_inverso', False),
                'orden': item_data.get('orden', 1),
            },
        )


def _import_items_progresivas(dimension, items_data):
    for item_data in items_data:
        item, _ = Item.objects.update_or_create(
            dimension=dimension,
            texto=item_data['texto_pregunta'],
            defaults={
                'es_inverso': False,
                'orden': item_data.get('orden', 1),
            },
        )
        item.opciones.all().delete()
        for opcion_data in sorted(item_data['opciones'], key=lambda o: o.get('orden', o['valor'])):
            ItemOpcion.objects.create(
                item=item,
                texto=opcion_data['texto'],
                valor=int(opcion_data['valor']),
                orden=opcion_data.get('orden', int(opcion_data['valor'])),
            )


def _import_niveles_retroalimentacion(dimension, niveles_data):
    total = 0
    for nivel_data in niveles_data:
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
        total += 1
    return total


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
    tipo = instrumento_data.get('tipo_instrumento', Instrumento.TIPO_ESCALA_LIKERT)
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
        _apply_instrumento_fields(instrumento, instrumento_data)
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
                'tipo_instrumento': tipo,
            },
        )

    if tipo == Instrumento.TIPO_ESCALA_LIKERT:
        _import_escalas_likert(instrumento, data['escalas'])

    total_niveles = 0
    for dimension_data in data['dimensiones']:
        dimension, _ = Dimension.objects.update_or_create(
            instrumento=instrumento,
            nombre=dimension_data['nombre'],
            defaults={
                'orden': dimension_data.get('orden', 1),
            },
        )

        items_data = dimension_data.get('items', [])
        if tipo == Instrumento.TIPO_ESCALA_LIKERT:
            _import_items_likert(dimension, items_data)
        else:
            _import_items_progresivas(dimension, items_data)

        total_niveles += _import_niveles_retroalimentacion(
            dimension,
            dimension_data.get('niveles_retroalimentacion', []),
        )

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
