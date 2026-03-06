"""
Formularios para el módulo de administración de Instrumentos/Evaluaciones.
"""
from django import forms
from core.forms import ModelBaseForm
from .models import Instrumento, Dimension, Item, EscalaOpcion


class InstrumentoForm(ModelBaseForm):
    """Formulario para crear/editar Instrumentos"""
    
    class Meta:
        model = Instrumento
        fields = ['nombre', 'slug', 'descripcion', 'activo', 'premium']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del instrumento'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'slug-del-instrumento'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descripción del instrumento'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        help_texts = {
            'slug': 'URL amigable del instrumento (ej: riasec, test-vocacional)',
            'activo': 'Si está activo, el instrumento estará disponible para los usuarios',
        }


class DimensionForm(ModelBaseForm):
    """Formulario para crear/editar Dimensiones"""
    
    class Meta:
        model = Dimension
        fields = ['instrumento', 'nombre', 'orden']
        help_texts = {
            'orden': 'Orden de visualización (menor número aparece primero)',
        }


class ItemForm(ModelBaseForm):
    """Formulario para crear/editar Ítems"""
    
    class Meta:
        model = Item
        fields = ['dimension', 'texto', 'es_inverso', 'orden']
        widgets = {
            'texto': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Texto del ítem o pregunta'
            }),
            'es_inverso': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'orden': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0'
            }),
        }
        help_texts = {
            'es_inverso': 'Marcar si la puntuación de este ítem se debe invertir',
            'orden': 'Orden de visualización dentro de la dimensión',
        }


class EscalaOpcionForm(ModelBaseForm):
    """Formulario para crear/editar Opciones de Escala"""
    
    class Meta:
        model = EscalaOpcion
        fields = ['instrumento', 'etiqueta', 'valor_nominal', 'orden']
        widgets = {
            'etiqueta': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Etiqueta de la opción (ej: Siempre, Nunca)'
            }),
            'valor_nominal': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': '1'
            }),
            'orden': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0'
            }),
        }
        help_texts = {
            'valor_nominal': 'Valor numérico asignado a esta opción',
            'orden': 'Orden de visualización (menor número aparece primero)',
        }


class ImportarTestForm(forms.Form):
    """Formulario para importar test desde JSON"""
    
    json_file = forms.FileField(
        label='Archivo JSON',
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.json,application/json'
        }),
        help_text='Opcional: sube un archivo .json (máximo 5MB).'
    )

    json_text = forms.CharField(
        label='JSON en texto',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 12,
            'placeholder': 'Pega aquí el JSON completo del test...'
        }),
        help_text='Opcional: pega aquí el JSON si no deseas subir archivo. Si completas ambos, se usará este campo.'
    )

    def clean(self):
        cleaned_data = super().clean()
        json_file = cleaned_data.get('json_file')
        json_text = (cleaned_data.get('json_text') or '').strip()
        cleaned_data['json_text'] = json_text

        if not json_file and not json_text:
            raise forms.ValidationError(
                'Debes subir un archivo JSON o pegar el contenido JSON en la caja de texto.'
            )

        return cleaned_data
    
    def clean_json_file(self):
        json_file = self.cleaned_data.get('json_file')
        
        if json_file:
            # Validar extensión
            if not json_file.name.endswith('.json'):
                raise forms.ValidationError('El archivo debe ser de tipo JSON (.json)')
            
            # Validar tamaño (máximo 5MB)
            if json_file.size > 5 * 1024 * 1024:
                raise forms.ValidationError('El archivo es demasiado grande. Máximo 5MB')
        
        return json_file
