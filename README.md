# 📋 Django Instrumentos - Sistema de Evaluaciones Psicométricas

[![Django](https://img.shields.io/badge/Django-5.0.4-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple.svg)](https://getbootstrap.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> Sistema completo y robusto de evaluaciones psicométricas para Django con retroalimentación inteligente, control de acceso premium, importación masiva JSON y visualización de resultados.

## ✨ Características Principales

- 🎯 **Evaluaciones Psicométricas Completas**: Tests con múltiples dimensiones e ítems
- 📊 **Visualización Avanzada**: Gráficos radar interactivos con Chart.js 4.4.0
- 🧠 **Retroalimentación Inteligente**: Diagnósticos automáticos basados en porcentajes
- 💎 **Sistema Premium**: Control de acceso con `user.premium` + bypass para staff/superuser
- 📥 **Importación JSON**: Carga masiva de tests desde archivos o textarea
- 🔄 **Auto-guardado AJAX**: Persistencia automática de respuestas
- 📱 **Responsive Design**: Optimizado para móviles y tablets
- 🔐 **Seguro**: Autenticación requerida, validación de pertenencia, transacciones atómicas
- ⚡ **Optimizado**: Bulk operations, select_related, prefetch_related
- 🎨 **UI/UX Profesional**: Bootstrap 5.3, FontAwesome, diseño moderno

## 📦 Instalación

### Requisitos

```bash
Django>=5.0.4
Python>=3.12
PostgreSQL>=15 (recomendado) o SQLite
```

### Pasos de Instalación

1. **Clonar o agregar la app a tu proyecto Django**

```bash
# Si usas este como paquete independiente
git clone https://github.com/juanbacan/Quierosermaestro.git

# O copia la carpeta applications/instrumentos/ a tu proyecto
```

2. **Agregar a INSTALLED_APPS en settings.py**

```python
INSTALLED_APPS = [
    # ... otras apps
    'applications.instrumentos',
]
```

3. **Configurar URLs en tu proyecto**

```python
# urls.py principal
urlpatterns = [
    # ... otras rutas
    path('evaluaciones/', include('applications.instrumentos.urls')),
]
```

4. **Ejecutar migraciones**

```bash
python manage.py makemigrations instrumentos
python manage.py migrate instrumentos
```

5. **Cargar tests de ejemplo (opcional)**

```bash
python manage.py cargar_tests_ejemplo
```

6. **Configurar settings (opcional para premium)**

```python
# settings.py
TESTS_PRECAVIDOS_PREMIUM_URL = '/premium/'  # URL donde redirigir usuarios sin acceso
```

## 🚀 Inicio Rápido

### 1. Crear tu primer test

**Opción A: Desde el Admin**

```python
# Accede al admin de Django
http://localhost:8000/admin/instrumentos/instrumento/add/

# Crea:
# - Instrumento (ej: "RIASEC")
# - Escala de Opciones (ej: 1-5)
# - Dimensiones (ej: "Realista", "Investigador")
# - Ítems por dimensión
# - Niveles de retroalimentación (Bajo/Medio/Alto)
```

**Opción B: Importar JSON**

```bash
# Ve a Admin → Instrumentos → Botón "Importar JSON"
# Sube el archivo ejemplo_importacion_premium_avanzado.json
```

**Opción C: Management Command**

```bash
python manage.py cargar_tests_ejemplo
```

### 2. Acceder a las evaluaciones

```
# Lista de tests disponibles
http://localhost:8000/evaluaciones/

# Detalle de un test específico
http://localhost:8000/evaluaciones/<slug>/

# Realizar evaluación
http://localhost:8000/evaluaciones/<slug>/realizar/<intento_id>/

# Ver resultados
http://localhost:8000/evaluaciones/resultados/<intento_id>/
```

## 📁 Estructura de la Aplicación

```
applications/instrumentos/
├── models.py                           # 7 modelos principales
├── views.py                            # Vistas del usuario final
├── views_admin.py                      # Vistas del panel admin (importación)
├── forms.py                            # Formularios (ImportarTestForm)
├── utils.py                            # Utilidades premium y helpers
├── urls.py                             # Rutas de la aplicación
├── admin.py                            # Configuración del admin Django
├── management/
│   └── commands/
│       └── cargar_tests_ejemplo.py     # Command para datos de ejemplo
├── templates/
│   └── instrumentos/
│       ├── lista_evaluaciones.html     # Lista de instrumentos
│       ├── detalle_evaluacion.html     # Detalle e inicio de evaluación
│       ├── realizar_evaluacion.html    # Formulario con AJAX
│       ├── resultados.html             # Resultados + retroalimentación
│       └── admin/
│           └── importar_tests.html     # UI de importación JSON
├── ejemplo_importacion.json            # Ejemplo básico de importación
├── ejemplo_importacion_premium_avanzado.json  # Ejemplo avanzado con premium
├── README.md                           # Documentación principal (este archivo)
├── README_IMPORTACION.md               # Guía de importación JSON
├── README_RETROALIMENTACION.md         # Guía de retroalimentación
└── README_PREMIUM.md                   # Guía de sistema premium
```

## �️ Modelos de Datos

### 1. Instrumento
Contenedor principal de la evaluación.

```python
class Instrumento(ModeloBase):
    nombre = CharField(max_length=255)
    slug = SlugField(unique=True)  # Para URLs amigables
    descripcion = TextField()
    activo = BooleanField(default=True)
    premium = BooleanField(default=False)  # ⭐ Control de acceso
```

**Características:**
- Heredan de `ModeloBase` (created_at, updated_at, etc.)
- Campo `premium` para control de acceso
- Admin personalizado con badges de estado

### 2. Dimension
Categorías dentro de un instrumento (ej: "Empatía", "Liderazgo").

```python
class Dimension(models.Model):
    instrumento = ForeignKey(Instrumento)
    nombre = CharField(max_length=255)
    descripcion = TextField(blank=True)
    orden = PositiveIntegerField(default=1)
```

### 3. Item (Pregunta)
Pregunta o afirmación individual del test.

```python
class Item(models.Model):
    dimension = ForeignKey(Dimension)
    texto = TextField()  # Pregunta completa
    es_inverso = BooleanField(default=False)  # Reverse scoring
    orden = PositiveIntegerField(default=1)
```

**Nota:** Los ítems inversos se puntúan al revés (ej: "Nunca" = 5 pts)

### 4. EscalaOpcion
Opciones de respuesta (ej: "Siempre" = 5 pts, "Nunca" = 1 pt).

```python
class EscalaOpcion(models.Model):
    instrumento = ForeignKey(Instrumento)
    etiqueta = CharField(max_length=100)  # "Siempre"
    valor_nominal = IntegerField()  # 5
    orden = PositiveIntegerField(default=1)
```

### 5. Intento
Registro de cada vez que un usuario toma un test.

```python
class Intento(models.Model):
    usuario = ForeignKey(CustomUser)
    instrumento = ForeignKey(Instrumento)
    inicio = DateTimeField(auto_now_add=True)
    fin = DateTimeField(null=True, blank=True)
    completado = BooleanField(default=False)
    resultados_brutos = JSONField(default=dict)  # Puntajes calculados
    
    def calcular_resultados(self):  # Calcula porcentajes por dimensión
        # Retorna: {"Empatía": {"puntaje_obtenido": 18, "puntaje_maximo": 25, "porcentaje": 72.0}}
```

### 6. Respuesta
Respuesta del usuario a cada ítem.

```python
class Respuesta(models.Model):
    intento = ForeignKey(Intento)
    item = ForeignKey(Item)
    opcion = ForeignKey(EscalaOpcion)
    
    class Meta:
        unique_together = ('intento', 'item')  # Una respuesta por ítem
```

### 7. NivelRetroalimentacion ⭐
Diagnósticos automáticos basados en porcentajes.

```python
class NivelRetroalimentacion(models.Model):
    dimension = ForeignKey(Dimension)
    nombre_nivel = CharField(max_length=100)  # "Bajo", "Medio", "Alto"
    porcentaje_min = DecimalField(max_digits=5, decimal_places=2)  # 0.00
    porcentaje_max = DecimalField(max_digits=5, decimal_places=2)  # 33.99
    mensaje_feedback = TextField()  # HTML permitido
```

**Ejemplo:**
- Si usuario obtiene 28% en "Empatía" → Muestra diagnóstico "Bajo" (0-33.99%)
- Si obtiene 55% → Muestra diagnóstico "Medio" (34-66.99%)

### 8. Control de Acceso Premium en Usuario 💎
El acceso premium se resuelve con el campo `premium` del modelo de usuario.

```python
class CustomUser(AbstractUser):
    premium = models.BooleanField(default=False)
```

Si `instrumento.premium=True`, el usuario debe tener `user.premium=True` (excepto staff/superuser, que tienen bypass).

## �️ Rutas y Vistas

### Rutas del Usuario Final

| URL | Vista | Protección | Descripción |
|-----|-------|------------|-------------|
| `/evaluaciones/` | `lista_evaluaciones` | `@login_required` | Lista de tests disponibles |
| `/evaluaciones/<slug>/` | `detalle_evaluacion` | `@login_required` + premium | Detalle del test + botón iniciar |
| `/evaluaciones/<slug>/realizar/<id>/` | `realizar_evaluacion` | `@login_required` + premium | Formulario del test (AJAX) |
| `/evaluaciones/resultados/<id>/` | `ver_resultados` | `@login_required` + ownership | Resultados + gráfico + retroalimentación |

### Rutas del Admin

| URL | Vista | Protección | Descripción |
|-----|-------|------------|-------------|
| `/admin/instrumentos/importar/` | `InstrumentoAdminView.get_importar` | `@staff_required` | UI de importación JSON |
| `/admin/instrumentos/importar/` (POST) | `InstrumentoAdminView.post_importar` | `@staff_required` | Procesa importación JSON |

## 💻 Vistas del Sistema

### 1. `lista_evaluaciones` (User)
```python
@login_required
def lista_evaluaciones(request):
    """
    Muestra todos los instrumentos activos.
    Los tests premium se marcan con badge 💎.
    """
```

### 2. `detalle_evaluacion` (User)
```python
@login_required
def detalle_evaluacion(request, slug):
    """
    GET: Muestra descripción del test + intentos previos
    POST: Crea nuevo intento y redirige al formulario
    
    ⭐ Verifica acceso premium con check_premium_access()
    """
```

### 3. `realizar_evaluacion` (User) - ⚡ Optimizada
```python
@login_required
def realizar_evaluacion(request, slug, intento_id):
    """
    GET: Muestra formulario paginado (10 ítems/página)
         - Ítems aleatorizados (orden único por intento)
         - Auto-guardado AJAX cada 30 segundos
         - Barra de progreso en tiempo real
    
    POST: Guarda respuestas con bulk_create()
          Finaliza intento y calcula resultados
          Redirige a ver_resultados
    
    ⭐ Verifica acceso premium
    🔒 Usa transaction.atomic() para integridad
    """
```

### 4. `ver_resultados` (User) - 📊 Visualización
```python
@login_required
def ver_resultados(request, intento_id):
    """
    Muestra:
    1. Gráfico radar (Chart.js) con puntajes por dimensión
    2. Tabla de resultados detallados
    3. 🧠 Retroalimentación automática por dimensión
       (diagnósticos basados en porcentajes)
    4. Botones de acción (repetir test, ver otros)
    
    🔒 Verifica ownership (solo tus intentos)
    """
```

### 5. `InstrumentoAdminView` (Admin) - 📥 Importación
```python
class InstrumentoAdminView(views.View):
    """
    GET /admin/instrumentos/importar/
        Muestra formulario de importación (file upload + textarea)
    
    POST /admin/instrumentos/importar/
        Procesa JSON y crea/actualiza:
        - Instrumento
        - Escalas
        - Dimensiones
        - Ítems
        - 🧠 Niveles de retroalimentación
    
    ⚡ Usa transaction.atomic() y bulk_create()
    """
```

## 🎨 Características de UI/UX

### Diseño Visual Moderno
- ✅ **Framework**: Bootstrap 5.3 con tema personalizado
- ✅ **Colores**: Primary, info, success, warning gradient badges
- ✅ **Componentes**: Cards con shadow, gradients, hover effects
- ✅ **Iconos**: FontAwesome 6 + emojis contextuales
- ✅ **Tipografía**: Responsive, legible en todos los dispositivos

### Formulario de Evaluación - ⚡ Optimizado
- ✅ **Paginación**: 10 ítems por página (configurable)
- ✅ **Aleatorización**: Orden único preservado por intento
- ✅ **Auto-guardado**: AJAX cada 30 segundos (progreso no se pierde)
- ✅ **Progress Bar**: Actualización en tiempo real (0-100%)
- ✅ **Botones Radio**: Estilo btn-check de Bootstrap (accesible)
- ✅ **Agrupación**: Ítems agrupados por dimensión en cards
- ✅ **Validación**: Cliente (required) + Servidor (all items answered)
- ✅ **Mobile-First**: Optimizado para táctil

### Página de Resultados - 📊 Completa
- ✅ **Gráfico Radar**: Chart.js 4.4.0 interactivo
  - Tooltips con valores exactos
  - Animaciones suaves
  - Responsive (adapta a pantalla)
- ✅ **Tabla de Puntajes**: Por dimensión con porcentajes
- ✅ **🧠 Retroalimentación**: Cards con diagnósticos automáticos
  - Color-coded por nivel (rojo/amarillo/verde)
  - HTML enriquecido (negritas, listas, emojis)
  - Recomendaciones personalizadas
- ✅ **Meta Info**: Fecha, duración, test realizado
- ✅ **Acciones**: Repetir test, ver otros, volver al dashboard

### Admin UI
- ✅ **Importación JSON**: Drag & drop + textarea paste
- ✅ **Inlines**: Dimensiones, ítems, niveles de retroalimentación
- ✅ **Badges**: Estado premium, vigencia de accesos
- ✅ **Filtros**: Por instrumento, activo, premium

## � Guías de Uso

### 🎯 Crear Test desde Cero (Admin Manual)

#### 1. Crear Instrumento
```
Admin → Instrumentos → Agregar Instrumento

Nombre: Test de Orientación Vocacional RIASEC
Slug: riasec-2026
Descripción: Evalúa tus intereses vocacionales según el modelo de Holland...
Activo: ✓
Premium: ☐  (desmarcado para acceso público)
```

#### 2. Crear Escala de Opciones
```
En la misma página (inline):

- Totalmente en desacuerdo | Valor: 1 | Orden: 1
- En desacuerdo           | Valor: 2 | Orden: 2
- Neutral                 | Valor: 3 | Orden: 3
- De acuerdo              | Valor: 4 | Orden: 4
- Totalmente de acuerdo   | Valor: 5 | Orden: 5
```

#### 3. Crear Dimensiones e Ítems
```
Admin → Dimensiones → Agregar Dimensión

Instrumento: RIASEC-2026
Nombre: Realista
Orden: 1

[Tab: Ítems]
- "Me gusta trabajar con herramientas y maquinaria" | Es Inverso: ☐ | Orden: 1
- "Prefiero trabajar al aire libre"                 | Es Inverso: ☐ | Orden: 2
- "Me gusta reparar cosas"                          | Es Inverso: ☐ | Orden: 3

[Tab: Niveles de Retroalimentación]
- Bajo   | 0.00 - 33.99  | "Tu nivel es bajo, te recomendamos..."
- Medio  | 34.00 - 66.99 | "Tu nivel es adecuado, puedes mejorar en..."
- Alto   | 67.00 - 100.00| "¡Excelente! Tu nivel es óptimo en..."
```

### 📥 Importar Test desde JSON (Recomendado)

#### Opción 1: Archivo JSON
```bash
1. Prepara tu archivo JSON (ver ejemplo_importacion_premium_avanzado.json)
2. Ve a Admin → Instrumentos → Botón "Importar JSON"
3. Selecciona tu archivo .json
4. Click en "Importar Test"
5. ✅ Verás confirmación con estadísticas
```

#### Opción 2: Pegar JSON en Textarea
```bash
1. Copia el contenido JSON completo
2. Ve a Admin → Instrumentos → Botón "Importar JSON"
3. Pega en el textarea "O pega tu JSON aquí"
4. Click en "Importar Test"
5. ✅ Confirmación instantánea
```

**Ver guías detalladas:**
- [README_IMPORTACION.md](README_IMPORTACION.md) - Estructura JSON completa
- [README_RETROALIMENTACION.md](README_RETROALIMENTACION.md) - Configurar diagnósticos
- [README_PREMIUM.md](README_PREMIUM.md) - Sistema de acceso premium

## 🧪 Management Commands

### cargar_tests_ejemplo

Carga 2 tests de ejemplo completos con retroalimentación:

```bash
python manage.py cargar_tests_ejemplo
```

**Crea:**
1. **Test Gratuito**: "Autorregulación Emocional"
   - 1 dimensión: Control Emocional
   - 5 ítems (incluye ítems inversos)
   - 3 niveles de retroalimentación (Bajo/Medio/Alto)
   - Acceso: Todos los usuarios

2. **Test Premium**: "Empatía y Relaciones Interpersonales - Premium"
   - 2 dimensiones: Capacidad Empática + Habilidades Sociales
   - 8 ítems totales
   - 6 niveles de retroalimentación (3 por dimensión)
    - Acceso: Solo usuarios premium + staff
    - ⭐ Se activa `user.premium` en el superusuario (si el campo existe)

**Características:**
- ✅ Idempotente (puedes ejecutarlo múltiples veces)
- ✅ Actualiza si ya existe (no duplica)
- ✅ Mensajes de retroalimentación en HTML enriquecido
- ✅ Emojis y formato profesional

### Crear tu propio Management Command

Ejemplo de estructura:

```python
# Ejecutar: python manage.py shell < populate_instrumentos.py

from applications.instrumentos.models import Instrumento, Dimension, Item, EscalaOpcion
from core.models import CustomUser

# Crear usuario de prueba (si no existe)
user, created = CustomUser.objects.get_or_create(
    username='testuser',
    defaults={'email': 'test@example.com'}
)
if created:
    user.set_password('password123')
    user.save()
    print(f"✓ Usuario creado: {user.username}")

# Crear Instrumento
instrumento = Instrumento.objects.create(
    nombre="Test de Orientación Vocacional RIASEC",
    slug="riasec",
    descripcion="Este test evalúa tus intereses vocacionales según el modelo de Holland (RIASEC)...",
    activo=True
)
print(f"✓ Instrumento creado: {instrumento.nombre}")

# Crear Escala de Opciones
opciones_data = [
    ("Totalmente en desacuerdo", 1),
    ("En desacuerdo", 2),
    ("Neutral", 3),
    ("De acuerdo", 4),
    ("Totalmente de acuerdo", 5),
]

for orden, (etiqueta, valor) in enumerate(opciones_data, 1):
    EscalaOpcion.objects.create(
        instrumento=instrumento,
        etiqueta=etiqueta,
        valor_nominal=valor,
        orden=orden
    )
print(f"✓ {len(opciones_data)} opciones de escala creadas")

# Crear Dimensiones e Ítems
dimensiones_data = {
    "Realista": [
        "Me gusta trabajar con herramientas y maquinaria",
        "Prefiero trabajar al aire libre",
        "Me gusta reparar cosas",
        "Disfruto trabajar con mis manos",
    ],
    "Investigador": [
        "Me gusta resolver problemas complejos",
        "Disfruto investigando temas a profundidad",
        "Me gusta analizar datos",
        "Prefiero trabajar de manera independiente",
    ],
    "Artístico": [
        "Me gusta expresarme creativamente",
        "Disfruto las actividades artísticas",
        "Me gusta diseñar cosas nuevas",
        "Prefiero ambientes de trabajo no estructurados",
    ],
    "Social": [
        "Me gusta ayudar a las personas",
        "Disfruto trabajar en equipo",
        "Me gusta enseñar a otros",
        "Prefiero trabajar con personas",
    ],
    "Emprendedor": [
        "Me gusta liderar proyectos",
        "Disfruto tomar decisiones importantes",
        "Me gusta persuadir a otros",
        "Prefiero ambientes competitivos",
    ],
    "Convencional": [
        "Me gusta trabajar con números",
        "Disfruto seguir procedimientos establecidos",
        "Me gusta organizar información",
        "Prefiero ambientes estructurados",
    ],
}

for orden, (nombre_dim, items_textos) in enumerate(dimensiones_data.items(), 1):
    dimension = Dimension.objects.create(
        instrumento=instrumento,
        nombre=nombre_dim,
        orden=orden
    )
    
    for item_orden, texto in enumerate(items_textos, 1):
        Item.objects.create(
            dimension=dimension,
            texto=texto,
            es_inverso=False,
            orden=item_orden
        )
    
    print(f"✓ Dimensión '{nombre_dim}' creada con {len(items_textos)} ítems")

print("\n¡Datos de prueba creados exitosamente! 🎉")
print(f"\nAccede a: http://localhost:8000/evaluaciones/")
```

## 🔐 Seguridad

### Autenticación y Autorización
- ✅ **Todas las vistas requieren login**: `@login_required`
- ✅ **Ownership validation**: Usuario solo ve sus propios intentos
- ✅ **Premium access control**: `instrumento.premium` + `user.premium`
- ✅ **Staff bypass**: Admin/staff acceden a todo
- ✅ **Regla simple y trazable**: Permisos premium centralizados en el usuario

### Integridad de Datos
- ✅ **Transacciones atómicas**: `transaction.atomic()` en operaciones críticas
- ✅ **Unique constraints**: No duplicar respuestas (intento + item)
- ✅ **Validación de servidor**: No confiar en validación de cliente
- ✅ **Bulk operations**: Prevenir race conditions
- ✅ **JSONField validation**: Estructura de resultados validada

### Protección Web
- ✅ **CSRF protection**: Tokens en todos los formularios
- ✅ **SQL Injection**: ORM de Django (prepared statements)
- ✅ **XSS**: Templates con auto-escape (excepto HTML explícito)
- ✅ **File upload validation**: Tipo, tamaño, extensión

### Buenas Prácticas
- ✅ **No exponer IDs secuenciales sensibles**: Usar UUIDs si es crítico
- ✅ **Rate limiting**: Considerar en producción (django-ratelimit)
- ✅ **Logs de auditoría**: ModeloBase incluye created_at/updated_at
- ✅ **Secrets en variables de entorno**: No hardcodear en código

## 📱 Responsive & Accesibilidad

### Diseño Responsive
- ✅ **Mobile-First**: Diseñado primero para móviles
- ✅ **Breakpoints**: sm, md, lg, xl de Bootstrap
- ✅ **Touch-Friendly**: Botones grandes (min 44x44px)
- ✅ **Gráficos adaptables**: Chart.js con responsive: true
- ✅ **Navegación**: Colapsable en móviles
- ✅ **Tablas**: Scroll horizontal en pantallas pequeñas

### Accesibilidad (A11y)
- ✅ **Semántica HTML**: Uso correcto de headings, nav, main, section
- ✅ **Labels en formularios**: Todos los inputs tienen label asociado
- ✅ **Contraste de color**: WCAG AA compliant
- ✅ **Keyboard navigation**: Tab order lógico
- ✅ **Screen readers**: aria-labels en elementos interactivos
- ✅ **Focus visible**: Outline en elementos enfocados

### Performance
- ✅ **Lazy loading**: Imágenes y componentes no críticos
- ✅ **Minificación**: CSS/JS minificados en producción
- ✅ **CDN**: Bootstrap, Chart.js desde CDN con fallback
- ✅ **Bulk operations**: Reduce queries a BD
- ✅ **Select/Prefetch related**: Optimiza ORM queries
- ✅ **Caching**: Considerar django-cache en producción

## 🚦 Checklist de Instalación

### ✅ Paso 1: Agregar App al Proyecto
```python
# settings.py
INSTALLED_APPS = [
    # ...
    'applications.instrumentos',
]
```

### ✅ Paso 2: Configurar URLs
```python
# urls.py principal
from django.urls import path, include

urlpatterns = [
    # ...
    path('evaluaciones/', include('applications.instrumentos.urls')),
]
```

### ✅ Paso 3: Configurar Settings (Opcional)
```python
# settings.py

# URL para redireccionar usuarios sin acceso premium
TESTS_PRECAVIDOS_PREMIUM_URL = '/pricing/'  # O tu página de planes

# Alternativa avanzada con reverse()
TESTS_PRECAVIDOS_PREMIUM_URL = {
    'name': 'planes:premium',
    'kwargs': {'slug': 'plan-premium'},
    'fallback': '/pricing/'
}
```

### ✅ Paso 4: Ejecutar Migraciones
```bash
python manage.py makemigrations instrumentos
python manage.py migrate instrumentos
```

### ✅ Paso 5: Crear Superusuario (si no existe)
```bash
python manage.py createsuperuser
```

### ✅ Paso 6: Cargar Datos de Ejemplo
```bash
python manage.py cargar_tests_ejemplo
```

### ✅ Paso 7: Probar el Sistema
```bash
# Iniciar servidor
python manage.py runserver

# Acceder a:
http://localhost:8000/admin/                  # Panel admin
http://localhost:8000/evaluaciones/           # Lista de tests
http://localhost:8000/evaluaciones/autorregulacion-emocional/  # Test gratuito
```

### ✅ Paso 8: Importar Tests Reales
```bash
# Opción A: Desde Admin UI
Admin → Instrumentos → "Importar JSON" → Subir archivo

# Opción B: Crear manualmente
Admin → Instrumentos → Agregar Instrumento
```

## 🎓 Principios y Buenas Prácticas

### Arquitectura
- ✅ **MVT Pattern**: Separación clara de Modelo-Vista-Template
- ✅ **DRY**: No repetir código (utils.py, ModeloBase)
- ✅ **SOLID**: Single responsibility, Open/Closed, etc.
- ✅ **Fat Models, Thin Views**: Lógica en modelos (calcular_resultados)

### Código
- ✅ **Comentado en español**: Docstrings y comentarios claros
- ✅ **Type hints**: Python 3.12+ (donde aplica)
- ✅ **PEP 8 compliant**: Estilo consistente
- ✅ **Nombres descriptivos**: Variables y funciones autoexplicativas

### Base de Datos
- ✅ **Optimización de queries**: select_related(), prefetch_related()
- ✅ **Bulk operations**: bulk_create(), bulk_update()
- ✅ **Transacciones atómicas**: transaction.atomic() en operaciones críticas
- ✅ **Índices**: db_index=True en campos clave
- ✅ **JSONField**: Flexibilidad para resultados dinámicos

### Django Best Practices
- ✅ **Class-Based Views**: Cuando tiene sentido (InstrumentoAdminView)
- ✅ **Function-Based Views**: Para lógica específica
- ✅ **Signals**: Para lógica desacoplada (si se necesita)
- ✅ **Custom Managers**: Queries reutilizables
- ✅ **Admin personalizado**: Inlines, filtros, acciones
- ✅ **Forms validation**: clean() methods

### Testing (Recomendado Implementar)
```python
# tests.py
class InstrumentoTestCase(TestCase):
    def test_crear_instrumento(self):
        # Test creación
    
    def test_realizar_evaluacion(self):
        # Test flujo completo
    
    def test_calcular_resultados(self):
        # Test cálculo de porcentajes
    
    def test_retroalimentacion(self):
        # Test niveles de retroalimentación
    
    def test_premium_access(self):
        # Test control de acceso
```

## 📖 Documentación Adicional

- **[README_IMPORTACION.md](README_IMPORTACION.md)**: Guía completa de importación JSON
- **[README_RETROALIMENTACION.md](README_RETROALIMENTACION.md)**: Sistema de diagnósticos automáticos
- **[README_PREMIUM.md](README_PREMIUM.md)**: Control de acceso y configuración premium
- **[ejemplo_importacion.json](ejemplo_importacion.json)**: Ejemplo básico de test
- **[ejemplo_importacion_premium_avanzado.json](ejemplo_importacion_premium_avanzado.json)**: Ejemplo avanzado

## 🤝 Contribuir

Si quieres contribuir a este proyecto:

1. Fork el repositorio
2. Crea una rama feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add: AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para más detalles.

## 👨‍💻 Autor

**Juan Bacan**
- GitHub: [@juanbacan](https://github.com/juanbacan)
- Proyecto: [Quierosermaestro](https://github.com/juanbacan/Quierosermaestro)

## 🙏 Agradecimientos

- Django Software Foundation
- Bootstrap team
- Chart.js community
- Comunidad de desarrolladores Python/Django

## 📊 Estadísticas del Proyecto

- **Modelos**: 7 (Instrumento, Dimension, Item, EscalaOpcion, Intento, Respuesta, NivelRetroalimentacion)
- **Vistas**: 5 (Lista, Detalle, Realizar, Resultados, Importar)
- **Templates**: 5 (incluye admin)
- **Forms**: 1 (ImportarTestForm)
- **Management Commands**: 1 (cargar_tests_ejemplo)
- **Líneas de código**: ~2000+ (models, views, templates)
- **Tests**: (Pendiente implementar)

---

<div align="center">

**Desarrollado con ❤️ usando Django 5.0.4, Bootstrap 5.3 y Chart.js 4.4.0**

⭐ Si te gusta este proyecto, dale una estrella en GitHub ⭐

[🐛 Reportar Bug](https://github.com/juanbacan/Quierosermaestro/issues) · 
[✨ Solicitar Feature](https://github.com/juanbacan/Quierosermaestro/issues) · 
[📖 Documentación](https://github.com/juanbacan/Quierosermaestro)

</div>
