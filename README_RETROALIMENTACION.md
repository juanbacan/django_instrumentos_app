# 🧠 Sistema de Retroalimentación Automática

[![Django](https://img.shields.io/badge/Django-5.0.4-green.svg)](https://www.djangoproject.com/)
[![AI](https://img.shields.io/badge/Feature-Auto%20Diagnosis-blue.svg)]()

> Sistema inteligente de diagnósticos y recomendaciones automáticas basadas en porcentajes de desempeño. Proporciona feedback personalizado por dimensión según el nivel de logro del usuario.

## 📌 Descripción

La retroalimentación automática permite que cada test genere diagnósticos personalizados basándose en el porcentaje obtenido por el usuario en cada dimensión. No necesitas programar nada: solo defines los rangos y mensajes en tu JSON o en el Admin.

## 🎯 ¿Cómo Funciona?

### Flujo del Sistema

```
1. Usuario completa el test
      ↓
2. Sistema calcula porcentaje por dimensión
      ↓
3. Sistema busca NivelRetroalimentacion que coincida con el porcentaje
      ↓
4. Muestra diagnóstico y recomendaciones en página de resultados
```

### Ejemplo Visual

```
Dimensión: "Autorregulación Emocional"
Usuario obtiene: 45% de puntaje

Niveles definidos:
├─ Bajo   (0% - 33.99%)   → ⚠️ Requiere Atención
├─ Medio  (34% - 66.99%)  → ✅ ESTE SE MUESTRA (45% cae aquí)
└─ Alto   (67% - 100%)    → 🎉 Óptimo

Resultado mostrado:
"Tu nivel es adecuado, pero puedes mejorar en..."
```

## 📝 Estructura del JSON

Agrega la clave `niveles_retroalimentacion` dentro de cada dimensión:

```json
{
    "instrumento": {
        "nombre": "Nombre del Test",
        "slug": "slug-del-test",
        "descripcion": "Descripción del test",
        "activo": true
    },
    "escalas": [
        {"etiqueta": "Nunca", "valor": 1, "orden": 1},
        {"etiqueta": "Siempre", "valor": 5, "orden": 5}
    ],
    "dimensiones": [
        {
            "nombre": "Autorregulación Emocional",
            "orden": 1,
            "items": [
                {"texto": "Pregunta 1", "es_inverso": false, "orden": 1},
                {"texto": "Pregunta 2", "es_inverso": true, "orden": 2}
            ],
            "niveles_retroalimentacion": [
                {
                    "nombre_nivel": "Requiere Atención (Bajo)",
                    "porcentaje_min": 0.00,
                    "porcentaje_max": 33.99,
                    "mensaje_feedback": "<p>Texto con diagnóstico y recomendaciones HTML permitido</p>"
                },
                {
                    "nombre_nivel": "Adecuado (Medio)",
                    "porcentaje_min": 34.00,
                    "porcentaje_max": 66.99,
                    "mensaje_feedback": "<p>Texto con diagnóstico...</p>"
                },
                {
                    "nombre_nivel": "Óptimo (Alto)",
                    "porcentaje_min": 67.00,
                    "porcentaje_max": 100.00,
                    "mensaje_feedback": "<p>¡Excelente! Texto de felicitación...</p>"
                }
            ]
        }
    ]
}
```

## 📊 Campos de `niveles_retroalimentacion`

| Campo | Tipo | Requerido | Rango/Formato | Descripción |
|-------|------|-----------|---------------|-------------|
| `nombre_nivel` | string | ✅ Sí | Max 100 chars | Identificador único del nivel (ej: "Bajo", "Óptimo") |
| `porcentaje_min` | decimal | ✅ Sí | 0.00 - 99.99 | Porcentaje mínimo del rango (inclusivo) |
| `porcentaje_max` | decimal | ✅ Sí | 0.01 - 100.00 | Porcentaje máximo del rango (inclusivo) |
| `mensaje_feedback` | text/HTML | ✅ Sí | Sin límite | Diagnóstico, análisis y recomendaciones. **HTML permitido** |

### ⚠️ Reglas de Porcentajes

- Los rangos **NO deben superponerse**
- Los rangos **deben cubrir 0% - 100%** para garantizar que siempre haya feedback
- Usa **exactamente 2 decimales**: `0.00`, `33.99`, `100.00`
- Si un puntaje cae en el límite exacto (ej: 34.00), se toma el rango que lo incluye

**✅ Buena práctica (sin espacios):**
```
Bajo:  0.00 - 33.99
Medio: 34.00 - 66.99
Alto:  67.00 - 100.00
```

**❌ Evitar (hay espacio entre 33.99 y 35.00):**
```
Bajo:  0.00 - 33.99
Medio: 35.00 - 66.99  ← Usuario con 34.50% no recibiría feedback
Alto:  67.00 - 100.00
```

## 🔄 Ciclo de Vida de la Retroalimentación

### 1️⃣ Importación/Creación

**Al importar JSON:**
```python
# Django ejecuta internamente:
NivelRetroalimentacion.objects.update_or_create(
    dimension=dimension,
    nombre_nivel="Bajo",
    defaults={
        'porcentaje_min': 0.00,
        'porcentaje_max': 33.99,
        'mensaje_feedback': "..."
    }
)
```

**Comportamiento:**
- ✅ Si el `nombre_nivel` **no existe** → Crea nuevo
- 🔄 Si el `nombre_nivel` **ya existe** → Actualiza porcentajes y mensaje
- ❌ **No se duplican** niveles

### 2️⃣ Ejecución del Test

```python
# Usuario completa test
for respuesta in respuestas:
    puntaje += respuesta.opcion.valor

# Sistema calcula porcentaje
porcentaje = (puntaje_obtenido / puntaje_maximo) * 100
# Ejemplo: (18 / 25) * 100 = 72.00%
```

### 3️⃣ Búsqueda de Retroalimentación

```python
# Django busca el nivel que contenga el porcentaje
feedback = NivelRetroalimentacion.objects.filter(
    dimension=dimension,
    porcentaje_min__lte=72.00,  # menor o igual
    porcentaje_max__gte=72.00   # mayor o igual
).first()

# Resultado: "Óptimo (Alto)" (67% - 100%)
```

### 4️⃣ Visualización en Resultados

```html
<!-- Renderizado en resultados.html -->
<div class="feedback-card">
    <h4>Autorregulación Emocional</h4>
    <span class="badge bg-success">Óptimo (Alto) - 72%</span>
    <div class="mensaje">
        {{ feedback.mensaje_feedback|safe }}
    </div>
</div>
```

## 🎨 Formato del `mensaje_feedback`

### Opción 1: HTML Enriquecido (Recomendado)

```html
<div style="background-color: #e8f5e9; padding: 20px; border-radius: 8px; border-left: 5px solid #4caf50;">
    <h4 style="color: #2e7d32; margin-top: 0;">✅ Diagnóstico: Nivel Alto</h4>
    
    <p><strong>📊 Análisis:</strong> Demuestras excelente control emocional y capacidad de autorregulación bajo presión. Tus estrategias de manejo del estrés son efectivas.</p>
    
    <h5 style="color: #1b5e20;">🎯 Fortalezas Identificadas:</h5>
    <ul style="color: #2e7d32;">
        <li>✓ Mantienes la calma ante adversidades</li>
        <li>✓ Gestionas eficazmente tu estrés</li>
        <li>✓ Eres modelo de autorregulación para otros</li>
    </ul>
    
    <h5 style="color: #1b5e20;">🚀 Próximos Pasos:</h5>
    <ol>
        <li>Comparte tus estrategias con colegas</li>
        <li>Considera ser mentor en bienestar emocional</li>
        <li>Documenta tus técnicas de autorregulación</li>
    </ol>
    
    <p style="margin-top: 15px; font-style: italic; color: #558b2f;">"La autorregulación es la base de la resiliencia profesional."</p>
</div>
```

### Opción 2: HTML Simple

```html
<p><strong>Análisis:</strong> Tu nivel en esta dimensión es adecuado, pero hay áreas de mejora.</p>
<p><strong>Recomendaciones:</strong></p>
<ul>
    <li>Practica técnicas de mindfulness diariamente</li>
    <li>Establece rutinas de descompresión</li>
    <li>Busca apoyo de un mentor</li>
</ul>
```

### Opción 3: Texto Plano

```
Análisis: Tus resultados indican que esta área necesita atención urgente.

Recomendaciones:
- Toma un curso de manejo de estrés
- Practica respiración diafragmática
- Consulta con un profesional de bienestar

Recursos sugeridos:
- Libro: "Mindfulness para docentes"
- App: Calm o Headspace
```

### Tags HTML Permitidos

✅ **Seguros y recomendados:**
```html
<p>, <strong>, <em>, <b>, <i>
<h4>, <h5>, <h6>
<ul>, <ol>, <li>
<div>, <span>
<br>
style="..." (inline styles)
```

⚠️ **Usar con cuidado:**
```html
<a href="...">  <!-- Links externos -->
<img src="...">  <!-- Imágenes -->
```

❌ **No permitidos (seguridad):**
```html
<script>  <!-- JavaScript -->
<iframe>  <!-- Embeds -->
onclick="..."  <!-- Event handlers -->
```

### Emojis Recomendados

```
📊 Análisis / Diagnóstico
🎯 Objetivos / Metas
✅ Éxito / Logro
⚠️ Atención / Cuidado
💡 Recomendaciones / Tips
🚀 Próximos pasos
📈 Progreso / Mejora
🔴 Crítico / Urgente
🟠 Medio / Moderado
🟢 Bueno / Óptimo
🎉 Celebración / Excelente
✓ Fortalezas
```

## 📄 Ejemplo Completo de Dimensión con Retroalimentación

Ver archivo completo: [`ejemplo_importacion.json`](ejemplo_importacion.json)

```json
{
  "instrumento": {
    "nombre": "Competencias Socioemocionales",
    "slug": "competencias-socioemocionales-2026",
    "descripcion": "Evaluación de habilidades socioemocionales para docentes",
    "activo": true,
    "premium": false
  },
  "escalas": [
    {"etiqueta": "Nunca", "valor": 1, "orden": 1},
    {"etiqueta": "Rara vez", "valor": 2, "orden": 2},
    {"etiqueta": "A veces", "valor": 3, "orden": 3},
    {"etiqueta": "Frecuentemente", "valor": 4, "orden": 4},
    {"etiqueta": "Siempre", "valor": 5, "orden": 5}
  ],
  "dimensiones": [
    {
      "nombre": "Autorregulación",
      "orden": 1,
      "items": [
        {"texto": "Mantengo la calma ante situaciones críticas.", "es_inverso": false, "orden": 1},
        {"texto": "Me resulta difícil controlar mis impulsos.", "es_inverso": true, "orden": 2},
        {"texto": "Tengo estrategias para manejar el estrés.", "es_inverso": false, "orden": 3}
      ],
      "niveles_retroalimentacion": [
        {
          "nombre_nivel": "Requiere Atención (Bajo)",
          "porcentaje_min": 0.00,
          "porcentaje_max": 33.99,
          "mensaje_feedback": "<div style='background-color: #ffebee; padding: 15px; border-radius: 8px; border-left: 4px solid #d32f2f;'><h4 style='color: #b71c1c; margin-top: 0;'>⚠️ Diagnóstico: Autorregulación Baja</h4><p><strong>📊 Análisis:</strong> Tus resultados indican que situaciones de tensión pueden estar desbordando tu capacidad de respuesta. La autorregulación es fundamental para crear un ambiente positivo.</p><h5 style='color: #c62828;'>💡 Plan de Mejora Urgente:</h5><ol><li><strong>Inmediato:</strong> Implementa pausas activas durante tu jornada</li><li><strong>Diario:</strong> Practica técnicas de respiración diafragmática (4-7-8)</li><li><strong>Semanal:</strong> Busca espacios de descompresión antes de entrar al aula</li><li><strong>Mensual:</strong> Toma curso de mindfulness para docentes</li></ol><p style='margin-top: 15px; color: #d32f2f;'><strong>📚 Recursos:</strong> Libro \"El cerebro del niño\" de Daniel Siegel</p></div>"
        },
        {
          "nombre_nivel": "Adecuado (Medio)",
          "porcentaje_min": 34.00,
          "porcentaje_max": 66.99,
          "mensaje_feedback": "<div style='background-color: #fff3e0; padding: 15px; border-radius: 8px; border-left: 4px solid #ff9800;'><h4 style='color: #e65100; margin-top: 0;'>🔄 Diagnóstico: Autorregulación en Desarrollo</h4><p><strong>📊 Análisis:</strong> Posees herramientas adecuadas para manejar conflictos típicos. Sin embargo, bajo presión sostenida podrías experimentar desgaste emocional.</p><h5 style='color: #ef6c00;'>🎯 Estrategia de Fortalecimiento:</h5><ul><li>✓ Mantén tus estrategias actuales de manejo del estrés</li><li>✓ Participa en grupos de apoyo con otros docentes</li><li>✓ Desarrolla un plan personal de autocuidado</li><li>✓ Establece límites claros entre vida laboral y personal</li></ul></div>"
        },
        {
          "nombre_nivel": "Óptimo (Alto)",
          "porcentaje_min": 67.00,
          "porcentaje_max": 100.00,
          "mensaje_feedback": "<div style='background-color: #e8f5e9; padding: 15px; border-radius: 8px; border-left: 4px solid #4caf50;'><h4 style='color: #2e7d32; margin-top: 0;'>🎉 ¡Excelente! Autorregulación Óptima</h4><p><strong>📊 Análisis:</strong> Muestras un <strong>alto grado de control emocional</strong> y eres capaz de separar problemas personales de tu práctica docente.</p><h5 style='color: #388e3c;'>✓ Fortalezas Identificadas:</h5><ul style='color: #2e7d32;'><li>✓ Mantienes la calma ante adversidades</li><li>✓ Gestionas eficazmente tu estrés</li><li>✓ Eres modelo de autorregulación para estudiantes</li></ul><h5 style='color: #388e3c;'>🚀 Próximos Pasos:</h5><p>Comparte tus estrategias con colegas y considera ser mentor en bienestar emocional.</p></div>"
        }
      ]
    }
  ]
}
```

## 🛠️ Gestión desde el Admin

### Crear/Editar Niveles Manualmente

#### Opción 1: Inline en Dimensión

```bash
1. Admin → Dimensiones → [Seleccionar dimensión]
2. Scroll hasta "Niveles de retroalimentación"
3. Click en "Agregar otro Nivel de retroalimentación"
4. Completar campos:
   - Nombre nivel: "Bajo"
   - Porcentaje min: 0.00
   - Porcentaje max: 33.99
   - Mensaje feedback: [HTML o texto]
5. Guardar
```

#### Opción 2: CRUD Independiente

```bash
1. Admin → Niveles de Retroalimentación → Agregar
2. Seleccionar dimensión
3. Completar formulario
4. Guardar
```

### Listar Todos los Niveles

```bash
Admin → Niveles de Retroalimentación → Ver todos
```

**Columnas visibles:**
- Dimensión
- Nombre del nivel
- Rango de porcentaje (XX% - YY%)
- Instrumento asociado

**Filtros disponibles:**
- Por instrumento
- Por dimensión

### Actualizar Retroalimentación Sin Perder Datos

**Escenario:** Quieres mejorar el mensaje feedback sin perder respuestas de usuarios.

**Solución 1: Editar directo en Admin**
```bash
1. Admin → Niveles de Retroalimentación
2. Buscar el nivel específico
3. Editar campo "Mensaje feedback"
4. Guardar
```

**Solución 2: Reimportar JSON**
```json
{
  "instrumento": {
    "slug": "mismo-slug-del-test-existente",
    ...
  },
  "dimensiones": [
    {
      "nombre": "Dimensión Existente",
      "niveles_retroalimentacion": [
        {
          "nombre_nivel": "Bajo",  // Mismo nombre
          "porcentaje_min": 0.00,
          "porcentaje_max": 33.99,
          "mensaje_feedback": "<p>NUEVO MENSAJE MEJORADO</p>"
        }
      ]
    }
  ]
}
```

**Resultado:** Solo se actualiza el mensaje, no afecta respuestas previas.

## 🎓 Buenas Prácticas y Tips

### 1. Casos de Uso por Nivel

**3 Niveles (Básico):**
```
Bajo   →  0% - 33%    → Necesita mejora urgente
Medio  → 34% - 66%    → Adecuado, puede mejorar
Alto   → 67% - 100%   → Óptimo
```

**4 Niveles (Recomendado):**
```
Crítico    →  0% - 24%    → Atención inmediata
Bajo       → 25% - 49%    → Requiere trabajo
Adecuado   → 50% - 74%    → Funcional
Óptimo     → 75% - 100%   → Excelente
```

**5 Niveles (Avanzado):**
```
Muy Bajo      →  0% - 20%    → Crisis
Bajo          → 21% - 40%    → Deficiente
Medio         → 41% - 60%    → Aceptable
Alto          → 61% - 80%    → Bueno
Muy Alto      → 81% - 100%   → Excepcional
```

### 2. Personalización por Público

**Para Docentes:**
```html
<p>💼 <strong>Impacto en el aula:</strong> Este nivel puede generar conflictos con estudiantes...</p>
<p>👥 <strong>Relación con padres:</strong> Fortalece tu comunicación empática...</p>
```

**Para Estudiantes:**
```html
<p>📚 <strong>En tus estudios:</strong> Esta habilidad te ayudará a...</p>
<p>🎯 <strong>En tu futuro:</strong> Desarrollar esta competencia te preparará para...</p>
```

### 3. Estructura de Mensajes Efectivos

```html
<div>
    <!-- 1. Diagnóstico claro -->
    <h4>🔴 Nivel: [Nombre]</h4>
    
    <!-- 2. Análisis de la situación -->
    <p><strong>📊 Análisis:</strong> Descripción objetiva del nivel...</p>
    
    <!-- 3. Impacto/Consecuencias -->
    <p><strong>⚠️ Impacto:</strong> Cómo afecta este nivel...</p>
    
    <!-- 4. Recomendaciones concretas -->
    <h5>💡 Plan de Acción:</h5>
    <ol>
        <li>Acción inmediata (próxima semana)</li>
        <li>Acción a corto plazo (próximo mes)</li>
        <li>Acción a mediano plazo (próximos 3 meses)</li>
    </ol>
    
    <!-- 5. Recursos (opcional) -->
    <p><strong>📚 Recursos recomendados:</strong> Libro/curso/app...</p>
    
    <!-- 6. Frase motivacional (opcional) -->
    <p style="font-style: italic;">"Frase inspiradora relevante"</p>
</div>
```

### 4. Testing de Retroalimentación

Antes de publicar tu test, verifica que:

```bash
✅ Todos los rangos cubren 0% - 100%
✅ No hay superposiciones entre rangos
✅ Los mensajes son claros y accionables
✅ El HTML renderiza correctamente (sin errores visuales)
✅ Los emojis se ven bien en todos los dispositivos
✅ Los enlaces externos (si los hay) funcionan
✅ El tono es apropiado para tu público objetivo
```

**Cómo probar:**
```bash
1. Crea un intento de prueba
2. Responde de forma que caigas en cada nivel (0%, 40%, 80%)
3. Verifica que el mensaje se vea bien
4. Ajusta según necesario
```

## 🔧 Troubleshooting

### Problema: "No aparece retroalimentación en resultados"

**Causas posibles:**

1. **Dimensión sin niveles definidos**
   ```sql
   SELECT * FROM instrumentos_nivelretroalimentacion 
   WHERE dimension_id = [ID];
   -- Si retorna vacío, no hay niveles
   ```
   **Solución:** Agregar niveles desde Admin o JSON

2. **Rangos no cubren el porcentaje obtenido**
   ```
   Usuario obtuvo: 34.5%
   Niveles: 0-33%, 35-66%, 67-100%
   → 34.5% no está en ningún rango
   ```
   **Solución:** Ajustar rangos sin espacios (0-33.99, 34-66.99, etc.)

3. **Error en la consulta**
   ```python
   # Verifica en logs si hay error SQL
   ```
   **Solución:** Revisar logs de Django

### Problema: "HTML no se renderiza correctamente"

**Causa:** Template tiene `{{ mensaje_feedback }}` en lugar de `{{ mensaje_feedback|safe }}`

**Solución:**
```html
<!-- ✅ Correcto -->
{{ feedback.mensaje_feedback|safe }}

<!-- ❌ Incorrecto (muestra tags como texto) -->
{{ feedback.mensaje_feedback }}
```

### Problema: "Mensaje muy largo, rompe el diseño"

**Solución 1: Limitar con CSS**
```html
<div style="max-height: 400px; overflow-y: auto;">
    {{ feedback.mensaje_feedback|safe }}
</div>
```

**Solución 2: Usar collapsible**
```html
<details>
    <summary>Ver diagnóstico completo</summary>
    {{ feedback.mensaje_feedback|safe }}
</details>
```

### Problema: "Quiero diferentes niveles por dimensión"

**¡Esto es completamente posible!**

```json
{
  "dimensiones": [
    {
      "nombre": "Liderazgo",
      "niveles_retroalimentacion": [
        {"nombre_nivel": "Emergente", "porcentaje_min": 0, "porcentaje_max": 40},
        {"nombre_nivel": "Competente", "porcentaje_min": 41, "porcentaje_max": 75},
        {"nombre_nivel": "Experto", "porcentaje_min": 76, "porcentaje_max": 100}
      ]
    },
    {
      "nombre": "Comunicación",
      "niveles_retroalimentacion": [
        {"nombre_nivel": "Introvertido", "porcentaje_min": 0, "porcentaje_max": 50},
        {"nombre_nivel": "Equilibrado", "porcentaje_min": 51, "porcentaje_max": 100}
      ]
    }
  ]
}
```

## 📊 Ejemplos de Mensajes por Contexto

### Para Tests Vocacionales

```html
<h4>🎯 Perfil: Investigador (Alto)</h4>
<p>Tienes fuerte inclinación hacia actividades analíticas y científicas.</p>
<h5>Carreras recomendadas:</h5>
<ul>
    <li>🔬 Investigación científica</li>
    <li>💻 Ciencias de la computación</li>
    <li>🧪 Química o Biología</li>
    <li>📊 Análisis de datos</li>
</ul>
```

### Para Tests de Liderazgo

```html
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 12px;">
    <h4>👑 Liderazgo Transformacional</h4>
    <p>Demuestras capacidad excepcional para inspirar y movilizar equipos hacia objetivos compartidos.</p>
    <p><strong>Tu estilo:</strong> Visionario y empático</p>
    <p><strong>Próximo nivel:</strong> Expande tu influencia a nivel organizacional</p>
</div>
```

### Para Tests Emocionales

```html
<div style="background-color: #e3f2fd; padding: 15px; border-left: 4px solid #2196f3;">
    <h4 style="color: #1565c0;">🧘 Inteligencia Emocional Equilibrada</h4>
    <p>Reconoces tus emociones y las de otros, permitiéndote responder (no reaccionar) en situaciones desafiantes.</p>
    <blockquote style="border-left: 3px solid #64b5f6; padding-left: 10px; color: #1976d2;">
        "Entre estímulo y respuesta hay un espacio. En ese espacio está nuestro poder de elegir." - Viktor Frankl
    </blockquote>
</div>
```

## 🔗 Referencias y Enlaces

- **[README Principal](README.md)**: Documentación completa del sistema
- **[README_IMPORTACION.md](README_IMPORTACION.md)**: Guía de importación JSON
- **[README_PREMIUM.md](README_PREMIUM.md)**: Sistema de acceso premium
- **[ejemplo_importacion.json](ejemplo_importacion.json)**: Ejemplo completo con retroalimentación

## 📝 Checklist de Implementación

```
[ ] Definir número de niveles por dimensión (3, 4 o 5)
[ ] Establecer rangos de porcentajes sin espacios
[ ] Redactar mensajes con estructura clara (análisis + recomendaciones)
[ ] Agregar HTML/CSS para mejorar visualización
[ ] Incluir emojis relevantes
[ ] Probar con diferentes porcentajes
[ ] Verificar que se vea bien en móvil
[ ] Revisar ortografía y gramática
[ ] Validar que el tono sea apropiado
[ ] Importar o crear en Admin
[ ] Hacer test completo y verificar retroalimentación
```

---

<div align="center">

**¿Preguntas?** Abre un [issue en GitHub](https://github.com/juanbacan/Quierosermaestro/issues)

⭐ **Este sistema te ahorra horas de programación** ⭐

Implementa diagnósticos inteligentes sin escribir una línea de código Python

</div>
