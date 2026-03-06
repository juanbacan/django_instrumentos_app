from django.urls import path
from . import views
from . import views_admin

app_name = 'instrumentos'

urlpatterns = [
    # ========== VISTAS PÚBLICAS (Usuarios) ==========
    # Lista de evaluaciones disponibles
    path('', views.lista_evaluaciones, name='lista_evaluaciones'),
    
    # Detalle de una evaluación específica
    path('<slug:slug>/', views.detalle_evaluacion, name='detalle_evaluacion'),
    
    # Realizar la evaluación (formulario)
    path('<slug:slug>/realizar/<int:intento_id>/', views.realizar_evaluacion, name='realizar_evaluacion'),
    
    # Ver resultados de un intento completado
    path('resultados/<int:intento_id>/', views.ver_resultados, name='ver_resultados'),
]


# ========== VISTAS DE ADMINISTRACIÓN ==========
instrumentos_urls = (
    {
        "nombre": "Dashboard",
        "url": 'dashboard/',
        "vista": views_admin.InstrumentosAdminView.as_view(),
        "namespace": 'admin_instrumentos_dashboard',
    },
    {
        "nombre": "Instrumentos",
        "url": 'instrumentos/',
        "vista": views_admin.InstrumentoAdminView.as_view(),
        "namespace": 'admin_instrumentos',
    },
    {
        "nombre": "Dimensiones",
        "url": 'dimensiones/',
        "vista": views_admin.DimensionAdminView.as_view(),
        "namespace": 'admin_dimensiones',
    },
    {
        "nombre": "Ítems",
        "url": 'items/',
        "vista": views_admin.ItemAdminView.as_view(),
        "namespace": 'admin_items',
    },
    {
        "nombre": "Opciones de Escala",
        "url": 'escalas/',
        "vista": views_admin.EscalaOpcionAdminView.as_view(),
        "namespace": 'admin_escalas',
    },
    {
        "nombre": "Intentos",
        "url": 'intentos/',
        "vista": views_admin.IntentoAdminView.as_view(),
        "namespace": 'admin_intentos',
    },
    {
        "nombre": "Respuestas",
        "url": 'respuestas/',
        "vista": views_admin.RespuestaAdminView.as_view(),
        "namespace": 'admin_respuestas',
    },
)
