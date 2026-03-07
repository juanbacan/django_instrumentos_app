from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Max
from django.http import Http404
from django.http import JsonResponse
from django.utils import timezone

from .models import Instrumento, Dimension, Item, EscalaOpcion, Intento, Respuesta, NivelRetroalimentacion
from .utils import check_premium_access


# ==========================================
# VISTA 1: Lista de Evaluaciones Disponibles
# ==========================================
@login_required
def lista_evaluaciones(request):
    """
    Muestra todos los instrumentos activos disponibles para el usuario.
    """
    instrumentos = Instrumento.objects.filter(activo=True).order_by('nombre')
    
    context = {
        'instrumentos': instrumentos,
    }
    return render(request, 'instrumentos/lista_evaluaciones.html', context)


# ==========================================
# VISTA 2: Detalle de una Evaluación
# ==========================================
def detalle_evaluacion(request, slug):
    """
    Muestra la descripción de un instrumento específico.
    Si el usuario hace POST, crea un nuevo Intento y redirige al formulario.
    Los usuarios no logueados pueden ver el detalle, pero deben loguearse para iniciar.
    """
    instrumento = get_object_or_404(Instrumento, slug=slug, activo=True)
    
    if request.method == 'POST':
        # Verificar que el usuario esté logueado para iniciar la evaluación
        if not request.user.is_authenticated:
            messages.info(request, 'Debes iniciar sesión para poder realizar la evaluación.')
            return redirect('login')
    
    # Verificar acceso premium (solo si está logueado)
    if request.user.is_authenticated:
        redirect_response = check_premium_access(request.user, instrumento)
        if redirect_response:
            messages.warning(
                request,
                f'El test "{instrumento.nombre}" es exclusivo para usuarios premium. '
                'Obtén acceso premium para poder completarlo.'
            )
            return redirect_response
    
    if request.method == 'POST':
        # Crear un nuevo intento para este usuario
        intento = Intento.objects.create(
            usuario=request.user,
            instrumento=instrumento,
            completado=False
        )
        messages.success(request, f'Has iniciado la evaluación "{instrumento.nombre}". ¡Buena suerte!')
        return redirect('instrumentos:realizar_evaluacion', slug=slug, intento_id=intento.id)
    
    # Obtener los últimos intentos del usuario para este instrumento (solo si está logueado)
    intentos_previos = []
    if request.user.is_authenticated:
        intentos_previos = Intento.objects.filter(
            usuario=request.user,
            instrumento=instrumento,
            completado=True
        ).order_by('-fin')[:5]
    
    context = {
        'instrumento': instrumento,
        'intentos_previos': intentos_previos,
    }
    return render(request, 'instrumentos/detalle_evaluacion.html', context)


# ==========================================
# VISTA 3: Realizar la Evaluación (Formulario)
# ==========================================
@login_required
def realizar_evaluacion(request, slug, intento_id):
    """
    GET: Muestra el formulario con ítems paginados y aleatorizados.
    POST: Guarda respuestas parciales o finaliza el intento.
    """
    import random
    from django.core.paginator import Paginator
    
    PREGUNTAS_POR_PAGINA = 10
    
    instrumento = get_object_or_404(Instrumento, slug=slug, activo=True)
    
    # Verificar acceso premium
    redirect_response = check_premium_access(request.user, instrumento)
    if redirect_response:
        messages.warning(
            request,
            f'El test "{instrumento.nombre}" es exclusivo para usuarios premium. '
            'Obtén acceso premium para poder completarlo.'
        )
        return redirect_response
    
    intento = get_object_or_404(Intento, id=intento_id, usuario=request.user, instrumento=instrumento)
    
    # Si el intento ya está completado, redirigir a resultados
    if intento.completado:
        messages.info(request, 'Este intento ya fue completado.')
        return redirect('instrumentos:ver_resultados', intento_id=intento.id)
    
    # Obtener opciones
    opciones = instrumento.opciones.all().order_by('orden')
    
    # Generar o recuperar orden aleatorio de ítems
    if not intento.orden_items:
        # Primera vez: aleatorizar ítems
        items_ids = list(Item.objects.filter(
            dimension__instrumento=instrumento
        ).values_list('id', flat=True))
        random.shuffle(items_ids)
        intento.orden_items = items_ids
        intento.save(update_fields=['orden_items'])
    
    # Obtener ítems en el orden guardado
    items_ordenados = []
    for item_id in intento.orden_items:
        try:
            item = Item.objects.select_related('dimension').get(id=item_id)
            items_ordenados.append(item)
        except Item.DoesNotExist:
            continue
    
    total_preguntas = len(items_ordenados)

    # Obtener respuestas ya guardadas
    respuestas_guardadas = {}
    for respuesta in intento.respuestas.select_related('item', 'opcion'):
        respuestas_guardadas[respuesta.item.id] = respuesta.opcion.id

    # Guardado en tiempo real (AJAX) por pregunta
    if request.method == 'POST' and request.POST.get('accion') == 'guardar_respuesta':
        item_id = request.POST.get('item_id')
        opcion_id = request.POST.get('opcion_id')

        if not item_id or not opcion_id:
            return JsonResponse({'ok': False, 'error': 'Datos incompletos'}, status=400)

        try:
            item = Item.objects.get(id=item_id, dimension__instrumento=instrumento)
            opcion = EscalaOpcion.objects.get(id=opcion_id, instrumento=instrumento)
        except (Item.DoesNotExist, EscalaOpcion.DoesNotExist):
            return JsonResponse({'ok': False, 'error': 'Ítem u opción inválida'}, status=400)

        Respuesta.objects.update_or_create(
            intento=intento,
            item=item,
            defaults={'opcion': opcion}
        )

        total_respondidas_ajax = intento.respuestas.values('item_id').distinct().count()
        porcentaje_ajax = (total_respondidas_ajax / total_preguntas * 100) if total_preguntas > 0 else 0

        return JsonResponse({
            'ok': True,
            'total_respondidas': total_respondidas_ajax,
            'total_preguntas': total_preguntas,
            'porcentaje_progreso': round(porcentaje_ajax, 2),
        })
    
    # Procesar POST (guardar respuestas parciales o finalizar)
    if request.method == 'POST':
        accion = request.POST.get('accion', 'guardar')
        siguiente_pagina = request.POST.get('siguiente_pagina')

        # Guardar respuestas de la página actual
        pagina_actual = request.POST.get('pagina', '1')
        paginator = Paginator(items_ordenados, PREGUNTAS_POR_PAGINA)
        pagina_obj_post = paginator.get_page(pagina_actual)

        opciones_validas = {
            str(op.id): op
            for op in instrumento.opciones.all()
        }

        for item in pagina_obj_post.object_list:
            opcion_id = request.POST.get(f'item_{item.id}')
            if opcion_id and opcion_id in opciones_validas:
                Respuesta.objects.update_or_create(
                    intento=intento,
                    item=item,
                    defaults={'opcion': opciones_validas[opcion_id]}
                )
        
        # Si es finalizar, verificar que todas las preguntas estén respondidas
        if accion == 'finalizar':
            total_items = total_preguntas
            respuestas_actuales = intento.respuestas.values('item_id').distinct().count()
            
            if respuestas_actuales < total_items:
                messages.warning(
                    request, 
                    f'⚠️ No puedes finalizar aún. Debes responder todas las preguntas. Has respondido {respuestas_actuales} de {total_items} preguntas.'
                )
                return redirect(f"{request.path}?pagina={pagina_actual}")
            
            # Finalizar test
            try:
                with transaction.atomic():
                    intento.finalizar_test()
                return redirect('instrumentos:ver_resultados', intento_id=intento.id)
            except Exception as e:
                messages.error(request, f'❌ Ocurrió un error al finalizar la evaluación: {str(e)}. Por favor, intenta de nuevo.')
                return redirect(f"{request.path}?pagina={pagina_actual}")
        
        # Navegación entre páginas
        if siguiente_pagina:
            return redirect(f"{request.path}?pagina={siguiente_pagina}")

    # Refrescar respuestas luego de cualquier guardado POST
    respuestas_guardadas = {
        respuesta.item_id: respuesta.opcion_id
        for respuesta in intento.respuestas.all()
    }
    
    # Paginación
    paginator = Paginator(items_ordenados, PREGUNTAS_POR_PAGINA)
    pagina_numero = request.GET.get('pagina', 1)
    
    try:
        pagina_obj = paginator.get_page(pagina_numero)
    except:
        pagina_obj = paginator.get_page(1)
    
    # Calcular progreso
    total_respondidas = intento.respuestas.values('item_id').distinct().count()
    porcentaje_progreso = (total_respondidas / total_preguntas * 100) if total_preguntas > 0 else 0
    
    context = {
        'instrumento': instrumento,
        'intento': intento,
        'pagina_obj': pagina_obj,
        'opciones': opciones,
        'respuestas_guardadas': respuestas_guardadas,
        'total_preguntas': total_preguntas,
        'total_respondidas': total_respondidas,
        'porcentaje_progreso': round(porcentaje_progreso, 1),
        'es_ultima_pagina': not pagina_obj.has_next(),
    }
    return render(request, 'instrumentos/realizar_evaluacion.html', context)


# ==========================================
# VISTA 4: Ver Resultados de un Intento
# ==========================================
@login_required
def ver_resultados(request, intento_id):
    """
    Muestra los resultados de un intento completado con un gráfico radar y retroalimentación.
    """
    intento = get_object_or_404(Intento, id=intento_id, usuario=request.user)
    
    # Verificar que el intento esté completado
    if not intento.completado:
        messages.warning(request, 'Este intento aún no ha sido completado.')
        return redirect('instrumentos:realizar_evaluacion', slug=intento.instrumento.slug, intento_id=intento.id)
    
    # Obtener los resultados del JSONField (nuevo formato con porcentajes)
    resultados = intento.resultados_brutos or {}

    dimensiones = Dimension.objects.filter(instrumento=intento.instrumento).order_by('orden')
    
    resultados_detalle = {}
    retroalimentaciones = {}
    
    for dimension in dimensiones:
        dim_data = resultados.get(dimension.nombre, {})
        
        # Manejar formato antiguo (solo número) y nuevo (dict con detalles)
        if isinstance(dim_data, dict):
            puntaje = dim_data.get('puntaje_obtenido', 0)
            puntaje_maximo = dim_data.get('puntaje_maximo', 0)
            porcentaje = dim_data.get('porcentaje', 0)
        else:
            # Formato antiguo: fallback
            puntaje = dim_data
            max_val = intento.instrumento.opciones.aggregate(max_val=Max('valor_nominal'))['max_val'] or 0
            total_items = dimension.items.count()
            puntaje_maximo = total_items * max_val
            porcentaje = (puntaje / puntaje_maximo * 100) if puntaje_maximo else 0
        
        resultados_detalle[dimension.nombre] = {
            'puntaje': puntaje,
            'puntaje_maximo': puntaje_maximo,
            'porcentaje': round(porcentaje, 2),
        }
        
        # Buscar el NivelRetroalimentacion que coincida con el porcentaje
        nivel_feedback = NivelRetroalimentacion.objects.filter(
            dimension=dimension,
            porcentaje_min__lte=porcentaje,
            porcentaje_max__gte=porcentaje
        ).first()
        
        if nivel_feedback:
            retroalimentaciones[dimension.nombre] = {
                'nombre_nivel': nivel_feedback.nombre_nivel,
                'mensaje_feedback': nivel_feedback.mensaje_feedback,
                'porcentaje_min': float(nivel_feedback.porcentaje_min),
                'porcentaje_max': float(nivel_feedback.porcentaje_max),
                'clase_visual': nivel_feedback.clase_visual,
            }
    
    context = {
        'intento': intento,
        'resultados': resultados,
        'resultados_detalle': resultados_detalle,
        'retroalimentaciones': retroalimentaciones,
    }
    return render(request, 'instrumentos/resultados.html', context)
