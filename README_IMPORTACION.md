# 📥 Importación de Tests en Formato JSON

[![Django](https://img.shields.io/badge/Django-5.0.4-green.svg)](https://www.djangoproject.com/)
[![JSON](https://img.shields.io/badge/Format-JSON-blue.svg)](https://www.json.org/)

> Guía completa para importar tests psicométricos mediante archivos JSON o copiar/pegar desde textarea. Compatible con retroalimentación automática y configuración premium.

## 📌 Descripción

Esta funcionalidad permite importar tests psicométricos completos de forma masiva, incluyendo:
- ✅ Instrumento (metadata del test)
- ✅ Escalas de respuesta (opciones como "Siempre", "Nunca")
- ✅ Dimensiones (categorías del test)
- ✅ Ítems (preguntas/afirmaciones)
- ✅ **Niveles de retroalimentación** (diagnósticos automáticos) 🆕

## 🎯 Ubicación

**Panel de Administración → Instrumentos → Botón "Importar JSON"**

```
http://localhost:8000/admin/instrumentos/importar/
```

## 📝 Estructura del JSON

El archivo JSON debe contener **tres secciones obligatorias**:

### 1️⃣ Instrumento (Metadata del Test)

```json
{
  "instrumento": {
    "nombre": "Nombre Completo del Test",
    "slug": "nombre-del-test-url-friendly",
    "descripcion": "Descripción detallada del instrumento de evaluación...",
    "activo": true,
    "premium": false
  }
}
```

**Campos:**

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `nombre` | string | ✅ Sí | Nombre completo del instrumento |
| `slug` | string | ✅ Sí | Identificador único en formato URL (solo letras, números, guiones) |
| `descripcion` | string | ⚠️ Opcional | Descripción HTML permitido |
| `activo` | boolean | ⚠️ Opcional (default: `true`) | Si el test está disponible para usuarios |
| `premium` | boolean | ⚠️ Opcional (default: `false`) | Si requiere acceso premium |

**⚠️ Importante**: El `slug` debe ser único. Si ya existe, el test se **actualizará** en lugar de crear uno nuevo.

### 2️⃣ Escalas (Opciones de Respuesta)

```json
{
  "escalas": [
    {"etiqueta": "Nunca", "valor": 1, "orden": 1},
    {"etiqueta": "Rara vez", "valor": 2, "orden": 2},
    {"etiqueta": "A veces", "valor": 3, "orden": 3},
    {"etiqueta": "Frecuentemente", "valor": 4, "orden": 4},
    {"etiqueta": "Siempre", "valor": 5, "orden": 5}
  ]
}
```

**Campos por escala:**

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `etiqueta` | string | ✅ Sí | Texto visible de la opción |
| `valor` | integer | ✅ Sí | Valor numérico asignado (puntuación) |
| `orden` | integer | ⚠️ Opcional | Orden de presentación (default: 1) |

**Ejemplos de escalas comunes:**

<details>
<summary><strong>Escala Likert 1-5 (Frecuencia)</strong></summary>

```json
[
  {"etiqueta": "Nunca", "valor": 1, "orden": 1},
  {"etiqueta": "Rara vez", "valor": 2, "orden": 2},
  {"etiqueta": "A veces", "valor": 3, "orden": 3},
  {"etiqueta": "Frecuentemente", "valor": 4, "orden": 4},
  {"etiqueta": "Siempre", "valor": 5, "orden": 5}
]
```
</details>

<details>
<summary><strong>Escala Likert 1-5 (Acuerdo)</strong></summary>

```json
[
  {"etiqueta": "Totalmente en desacuerdo", "valor": 1, "orden": 1},
  {"etiqueta": "En desacuerdo", "valor": 2, "orden": 2},
  {"etiqueta": "Neutral", "valor": 3, "orden": 3},
  {"etiqueta": "De acuerdo", "valor": 4, "orden": 4},
  {"etiqueta": "Totalmente de acuerdo", "valor": 5, "orden": 5}
]
```
</details>

<details>
<summary><strong>Escala 1-3 (Bajo/Medio/Alto)</strong></summary>

```json
[
  {"etiqueta": "Bajo", "valor": 1, "orden": 1},
  {"etiqueta": "Medio", "valor": 2, "orden": 2},
  {"etiqueta": "Alto", "valor": 3, "orden": 3}
]
```
</details>

### 3️⃣ Dimensiones e Ítems

```json
{
  "dimensiones": [
    {
      "nombre": "Autorregulación",
      "descripcion": "Capacidad para manejar emociones",
      "orden": 1,
      "items": [
        {
          "texto": "Mantengo la calma ante situaciones críticas.",
          "es_inverso": false,
          "orden": 1
        },
        {
          "texto": "Me cuesta controlar mis impulsos bajo presión.",
          "es_inverso": true,
          "orden": 2
        }
      ],
      "niveles_retroalimentacion": [
        {
          "nombre_nivel": "Requiere Atención (Bajo)",
          "porcentaje_min": 0.00,
          "porcentaje_max": 33.99,
          "mensaje_feedback": "<p><strong>Análisis:</strong> Tu nivel es bajo...</p>"
        }
      ]
    }
  ]
}
```

**Campos de dimensión:**

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `nombre` | string | ✅ Sí | Nombre de la dimensión |
| `descripcion` | string | ⚠️ Opcional | Descripción detallada |
| `orden` | integer | ⚠️ Opcional (default: 1) | Orden de presentación |
| `items` | array | ✅ Sí | Lista de preguntas/ítems |
| `niveles_retroalimentacion` | array | ⚠️ Opcional | Diagnósticos automáticos |

**Campos de ítem:**

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `texto` | string | ✅ Sí | Texto completo de la pregunta/afirmación |
| `es_inverso` | boolean | ⚠️ Opcional (default: `false`) | Si el ítem puntúa de forma inversa |
| `orden` | integer | ⚠️ Opcional (default: 1) | Orden dentro de la dimensión |

**🔄 ¿Qué es un ítem inverso?**

Los ítems inversos puntúan al revés:
- Normal: "Siempre" = 5 pts, "Nunca" = 1 pt
- Inverso: "Siempre" = 1 pt, "Nunca" = 5 pts

**Ejemplo:** "Me cuesta controlar mis impulsos" (es_inverso: true)
- Si usuario responde "Siempre" → obtiene 1 punto (malo en autocontrol)
- Si usuario responde "Nunca" → obtiene 5 puntos (bueno en autocontrol)

## 🧠 Niveles de Retroalimentación (Opcional)

**Campos de retroalimentación:**

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `nombre_nivel` | string | ✅ Sí | Identificador del nivel (ej: "Bajo", "Alto") |
| `porcentaje_min` | decimal | ✅ Sí | Porcentaje mínimo (0.00 - 99.99) |
| `porcentaje_max` | decimal | ✅ Sí | Porcentaje máximo (0.01 - 100.00) |
| `mensaje_feedback` | string | ✅ Sí | HTML permitido con diagnóstico y recomendaciones |

**Ejemplo completo:**

```json
"niveles_retroalimentacion": [
  {
    "nombre_nivel": "Requiere Atención (Bajo)",
    "porcentaje_min": 0.00,
    "porcentaje_max": 33.99,
    "mensaje_feedback": "<div style='color: #d32f2f;'><h4>⚠️ Nivel Bajo</h4><p><strong>Análisis:</strong> Tus resultados indican que esta área necesita desarrollo.</p><p><strong>Recomendaciones:</strong></p><ul><li>Practica técnicas de mindfulness</li><li>Busca apoyo de un mentor</li></ul></div>"
  },
  {
    "nombre_nivel": "Adecuado (Medio)",
    "porcentaje_min": 34.00,
    "porcentaje_max": 66.99,
    "mensaje_feedback": "<p>Tu nivel es adecuado, pero puedes mejorar...</p>"
  },
  {
    "nombre_nivel": "Óptimo (Alto)",
    "porcentaje_min": 67.00,
    "porcentaje_max": 100.00,
    "mensaje_feedback": "<p>🎉 ¡Excelente! Demuestras alto dominio en esta área.</p>"
  }
]
```

**📖 Más información:** Ver [README_RETROALIMENTACION.md](README_RETROALIMENTACION.md)

## 📄 Ejemplo Completo

Ver archivos de ejemplo en el repositorio:
- **Básico**: [`ejemplo_importacion.json`](ejemplo_importacion.json) - Test con 3 dimensiones
- **Avanzado**: [`ejemplo_importacion_premium_avanzado.json`](ejemplo_importacion_premium_avanzado.json) - Test premium con retroalimentación HTML enriquecida

## 🔄 Comportamiento de la Importación

### Creación vs. Actualización

| Escenario | Comportamiento |
|-----------|----------------|
| ✨ Slug **NO existe** | Crea un nuevo test completo |
| 🔄 Slug **ya existe** | Actualiza el test existente |

### Reglas de Actualización Detalladas

| Entidad | Criterio de Identificación | Comportamiento |
|---------|---------------------------|----------------|
| **Instrumento** | `slug` | Actualiza `nombre`, `descripcion`, `activo`, `premium` |
| **Escalas** | `instrumento` + `valor` | Actualiza `etiqueta`, `orden` |
| **Dimensiones** | `instrumento` + `nombre` | Actualiza `descripcion`, `orden` |
| **Ítems** | `dimension` + `texto` | Actualiza `es_inverso`, `orden` |
| **Retroalimentación** | `dimension` + `nombre_nivel` | Actualiza `porcentaje_min`, `porcentaje_max`, `mensaje_feedback` |

**⚙️ Transacciones Atómicas:**
- Si ocurre **cualquier error**, todos los cambios se revierten automáticamente
- Garantiza que la base de datos permanece consistente

## ✅ Validaciones del Sistema

El sistema valida automáticamente:

- ✅ **Formato JSON válido**: Sintaxis correcta
- ✅ **Claves requeridas**: `instrumento`, `escalas`, `dimensiones`
- ✅ **Estructura correcta**: Arrays donde deben ser arrays, objetos donde deben ser objetos
- ✅ **Tamaño de archivo**: Máximo 5MB
- ✅ **Extensión de archivo**: Debe ser `.json`
- ✅ **Valores numéricos**: `valor`, `orden`, `porcentaje_min`, `porcentaje_max`
- ✅ **Rangos de porcentajes**: 0.00 - 100.00
- ✅ **Slug único**: Solo letras minúsculas, números y guiones

## 📤 Formas de Importar

### Método 1: Subir Archivo JSON

```bash
1. Ve a Admin → Instrumentos
2. Click en botón "Importar JSON"
3. Click en "Seleccionar archivo"
4. Elige tu archivo .json
5. Click en "Importar Test"
```

**✅ Ventajas:**
- Ideal para archivos grandes
- Puedes versionar el archivo (Git)
- Fácil de compartir

### Método 2: Pegar JSON en Textarea

```bash
1. Ve a Admin → Instrumentos
2. Click en botón "Importar JSON"
3. Copia tu JSON completo
4. Pega en el textarea "O pega tu JSON aquí"
5. Click en "Importar Test"
```

**✅ Ventajas:**
- Más rápido para tests pequeños
- No necesita crear archivo
- Ideal para pruebas rápidas

### Método 3: Programáticamente (Python)

```python
from applications.instrumentos.views_admin import InstrumentoAdminView
import json

# Leer JSON
with open('mi_test.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Importar (desde shell o script)
# view = InstrumentoAdminView()
# result = view._procesar_importacion(data)
```

## 🎯 Mensajes de Resultado

### ✅ Éxito

```
✅ Test "Nombre del Test" creado exitosamente con 3 dimensiones, 12 ítems y 9 niveles de retroalimentación.
```

### ❌ Errores Comunes

| Error | Causa | Solución |
|-------|-------|----------|
| `Error al leer el JSON` | Sintaxis JSON inválida | Validar en [JSONLint](https://jsonlint.com/) |
| `El JSON debe contener la clave 'escalas'` | Falta sección | Agregar todas las claves requeridas |
| `Archivo demasiado grande` | Supera 5MB | Dividir en múltiples tests |
| `Extension no permitida` | No es .json | Cambiar extensión a .json |
| `IntegrityError` | Violación de constraint | Revisar unicidad de slug |

## 🛠️ Troubleshooting

### Problema: "Error al leer el JSON"

**Solución:**
1. Copia tu JSON
2. Ve a [JSONLint.com](https://jsonlint.com/)
3. Pega y valida
4. Corrige errores de sintaxis (comillas, comas, llaves)

### Problema: "El JSON debe contener la clave X"

**Solución:**
Verifica que tu JSON tenga la estructura completa:
```json
{
  "instrumento": { ... },
  "escalas": [ ... ],
  "dimensiones": [ ... ]
}
```

### Problema: "Slug ya existe"

**Comportamiento esperado:** No es un error, el sistema actualiza el test existente.

**Si no quieres actualizar:**
- Cambia el `slug` a uno nuevo
- Ejemplo: `"slug": "test-2026-v2"`

### Problema: Los niveles de retroalimentación no aparecen en resultados

**Causas posibles:**
1. Porcentajes con rangos incorrectos (verificar que cubran 0-100%)
2. Usuario obtuvo puntaje fuera de todos los rangos
3. Dimensión sin niveles de retroalimentación

**Solución:**
```json
// Asegúrate de cubrir todo el rango 0-100%
[
  {"nombre_nivel": "Bajo", "porcentaje_min": 0.00, "porcentaje_max": 33.99},
  {"nombre_nivel": "Medio", "porcentaje_min": 34.00, "porcentaje_max": 66.99},
  {"nombre_nivel": "Alto", "porcentaje_min": 67.00, "porcentaje_max": 100.00}
]
```

## 🎓 Tips y Mejores Prácticas

### Nomenclatura de Slugs

✅ **Buenas prácticas:**
```
"slug": "riasec-2026"
"slug": "competencias-socioemocionales"
"slug": "liderazgo-educativo-premium"
```

❌ **Evitar:**
```
"slug": "RIASEC 2026"  // Espacios y mayúsculas
"slug": "test_nuevo"   // Guión bajo en lugar de guión
"slug": "prueba123!@#" // Caracteres especiales
```

### Orden de Presentación

```json
// Los ítems se mostrarán en el orden especificado
{
  "items": [
    {"texto": "Primera pregunta", "orden": 1},
    {"texto": "Segunda pregunta", "orden": 2},
    {"texto": "Tercera pregunta", "orden": 3}
  ]
}
```

**💡 Tip:** Numera de 10 en 10 para facilitar inserciones futuras:
```json
{"orden": 10}, {"orden": 20}, {"orden": 30}
// Puedes insertar orden: 15 entre 10 y 20 sin renumerar todo
```

### HTML en Retroalimentación

```json
{
  "mensaje_feedback": "<div style='background: #f0f0f0; padding: 15px;'><h4 style='color: #2e7d32;'>✅ Diagnóstico</h4><p><strong>Análisis:</strong> Tu nivel es excelente.</p><ul><li>Fortaleza 1</li><li>Fortaleza 2</li></ul></div>"
}
```

**✅ Permitido:**
- Tags HTML: `<p>`, `<strong>`, `<ul>`, `<li>`, `<h4>`, `<div>`
- Estilos inline: `style="..."`
- Emojis: ✅ 🎉 ⚠️ 📊

**❌ No recomendado:**
- `<script>` (por seguridad)
- `<iframe>` (por seguridad)
- JavaScript en eventos: `onclick="..."`

### Versionado de Tests

Si necesitas actualizar un test sin perder el anterior:

```bash
# Versión 1
"slug": "competencias-docentes-v1"

# Versión 2 (nueva)
"slug": "competencias-docentes-v2"
```

Luego puedes desactivar la v1:
```json
{
  "instrumento": {
    "slug": "competencias-docentes-v1",
    "activo": false
  }
}
```

## 📊 Visualización en Admin

Una vez importado, puedes:

### Ver/Editar Instrumento
```
Admin → Instrumentos → [Tu Test]
```

### Ver/Editar Dimensiones
```
Admin → Dimensiones → Filtrar por instrumento
```

### Ver/Editar Niveles de Retroalimentación
```
Admin → Dimensiones → [Dimensión] → Tab "Niveles de retroalimentación"
```

### Validar si un Test es Premium
```
Admin → Instrumentos → [Tu Test] → Campo "premium"
```

El acceso se controla por `user.premium` (campo del usuario), no por una whitelist por instrumento.

## 🔗 Enlaces Útiles

- **[README Principal](README.md)**: Documentación completa del sistema
- **[README_RETROALIMENTACION.md](README_RETROALIMENTACION.md)**: Configurar diagnósticos
- **[README_PREMIUM.md](README_PREMIUM.md)**: Sistema de acceso premium
- **[JSONLint](https://jsonlint.com/)**: Validador de JSON online
- **[JSON.org](https://www.json.org/)**: Documentación oficial de JSON

---

<div align="center">

**¿Necesitas ayuda?** Abre un [issue en GitHub](https://github.com/juanbacan/Quierosermaestro/issues)

⭐ Si te gusta este sistema, dale una estrella en GitHub ⭐

</div>
