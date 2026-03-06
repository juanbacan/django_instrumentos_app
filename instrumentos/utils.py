"""
Utilidades para el módulo de Instrumentos/Evaluaciones.

Incluye funciones para gestionar acceso premium a tests.
"""
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse, NoReverseMatch


def get_premium_url():
    """
    Obtiene la URL de premium desde settings.
    
    Configuración en settings.py:
    
    Opción 1: URL simple (string)
        TESTS_PRECAVIDOS_PREMIUM_URL = '/premium/'
    
    Opción 2: URL named con kwargs (dict)
        TESTS_PRECAVIDOS_PREMIUM_URL = {
            'name': 'tienda:producto',
            'kwargs': {'slug': 'precavidos-premium'},
            'fallback': '/premium/'
        }
    
    Returns:
        str: URL de premium resuelta
    """
    premium_config = getattr(settings, 'TESTS_PRECAVIDOS_PREMIUM_URL', '/premium/')

    if isinstance(premium_config, dict):
        url_name = premium_config.get('name')
        url_kwargs = premium_config.get('kwargs', {})
        fallback_url = premium_config.get('fallback', '/premium/')
        
        if url_name:
            try:
                return reverse(url_name, kwargs=url_kwargs or None)
            except NoReverseMatch:
                return fallback_url
        return fallback_url

    return premium_config


def redirect_to_premium():
    """
    Redirige a la URL de premium configurada.
    
    Maneja tanto URLs simples (string) como configuraciones 
    de URL con name y kwargs (dict).
    
    Returns:
        HttpResponseRedirect: Redirección a la URL de premium
    """
    return redirect(get_premium_url())


def user_has_premium_access(user, instrumento):
    """
    Verifica si un usuario tiene acceso a un instrumento premium.
    
    El acceso se otorga si:
    1. El instrumento NO es premium
    2. El usuario es staff/admin
    3. El usuario está en la whitelist de acceso premium (si existe AccesoPremiumInstrumento)
    
    Args:
        user: Usuario a verificar
        instrumento: Instrumento para el que se verifica acceso
    
    Returns:
        bool: True si el usuario tiene acceso, False en caso contrario
    """
    # Si el instrumento no es premium, todos pueden acceder
    if not instrumento.premium:
        return True
    
    # Staff y admin siempre tienen acceso
    if user and (user.is_staff or user.is_admin):
        return True
    
    # Verificar si el usuario está en la whitelist
    try:
        from .models import AccesoPremiumInstrumento
        if user and AccesoPremiumInstrumento.objects.filter(
            usuario=user,
            instrumento=instrumento,
            activo=True
        ).exists():
            return True
    except ImportError:
        pass
    
    return False


def check_premium_access(user, instrumento):
    """
    Verifica y redirige si es necesario.
    
    Returns:
        HttpResponseRedirect o None
        
    Ejemplo en vista:
        redirect_response = check_premium_access(request.user, instrumento)
        if redirect_response:
            return redirect_response
    """
    if not user_has_premium_access(user, instrumento):
        return redirect_to_premium()
    return None
