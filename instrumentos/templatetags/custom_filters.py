"""
Filtros de plantilla personalizados para la app instrumentos.
"""
from django import template

register = template.Library()


@register.filter(name='dict_get')
def dict_get(dictionary, key):
    """
    Obtiene un valor de un diccionario usando una clave dinámica.
    
    Uso en template:
    {{ mi_diccionario|dict_get:clave_variable }}
    
    Args:
        dictionary: El diccionario del que obtener el valor
        key: La clave para buscar en el diccionario
        
    Returns:
        El valor asociado a la clave, o None si no existe
    """
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter(name='percentage')
def percentage(value, max_value=100):
    """
    Calcula el porcentaje de un valor respecto a un máximo.
    
    Uso en template:
    {{ puntaje|percentage:puntaje_maximo }}
    
    Args:
        value: El valor numérico
        max_value: El valor máximo (por defecto 100)
        
    Returns:
        El porcentaje como float
    """
    try:
        return (float(value) / float(max_value)) * 100
    except (ValueError, ZeroDivisionError, TypeError):
        return 0
