from django import forms
from .models import Libro, Categoria, Editorial, LoginUsuario, Usuario
from django.contrib.auth.forms import ReadOnlyPasswordHashField

class LibroForm(forms.ModelForm):
    copias_totales = forms.IntegerField(
        initial=1, 
        min_value=1, 
        label="Número de Copias Totales",
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full p-2 border border-gray-300 rounded-md shadow-sm'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categoria'].required = True
        self.fields['editorial'].required = True
        self.fields['ano_publicacion'].required = True

    class Meta:
        model = Libro
        fields = ['isbn', 'titulo', 'autor', 'ano_publicacion', 'categoria', 'editorial']
        labels = {
            'isbn': 'ISBN (ID Local)',
            'titulo': 'Título del Libro',
            'autor': 'Autor',
            'ano_publicacion': 'Año de Publicación',
            'categoria': 'Categoría',
            'editorial': 'Editorial',
        }
        widgets = {
            'isbn': forms.TextInput(attrs={'class': 'mt-1 block w-full p-2 border border-gray-300 rounded-md shadow-sm', 'type': 'number'}),
            'titulo': forms.TextInput(attrs={'class': 'mt-1 block w-full p-2 border border-gray-300 rounded-md shadow-sm'}),
            'autor': forms.TextInput(attrs={'class': 'mt-1 block w-full p-2 border border-gray-300 rounded-md shadow-sm'}),
            'ano_publicacion': forms.TextInput(attrs={'class': 'mt-1 block w-full p-2 border border-gray-300 rounded-md shadow-sm'}),
            'categoria': forms.Select(attrs={'class': 'mt-1 block w-full p-2 border border-gray-300 rounded-md shadow-sm'}),
            'editorial': forms.Select(attrs={'class': 'mt-1 block w-full p-2 border border-gray-300 rounded-md shadow-sm'}),
        }
        error_messages = {
            'isbn': {
                'required': 'El ISBN es obligatorio.',
                'unique': 'Ya existe un libro con este ISBN.'
            },
            'titulo': {
                'required': 'El título no puede estar vacío.',
            },
            'autor': {
                'required': 'El autor no puede estar vacío.',
            },
            'ano_publicacion': {
                'required': 'El año de publicación es obligatorio.',
            },
            'categoria': {
                'required': 'Debes seleccionar una categoría.',
            },
            'editorial': {
                'required': 'Debes seleccionar una editorial.',
            },
        }

    def clean_isbn(self):
        isbn = self.cleaned_data.get('isbn')
        if self.instance.pk != isbn and Libro.objects.filter(isbn=isbn).exists():
            raise forms.ValidationError("Ya existe un libro con este ISBN. Por favor, ingrese uno diferente.")
        return isbn
    

class UsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['nombre_completo', 'correo_electronico', 'telefono', 'direccion', 'tipo_usuario']
        labels = {
            'nombre_completo': 'Nombre Completo',
            'correo_electronico': 'Correo Electrónico',
            'telefono': 'Teléfono (Opcional)',
            'direccion': 'Dirección (Opcional)',
            'tipo_usuario': 'Tipo de Usuario',
        }
        widgets = {
            'nombre_completo': forms.TextInput(attrs={'class': 'mt-1 block w-full p-2 border border-gray-300 rounded-md shadow-sm'}),
            'correo_electronico': forms.EmailInput(attrs={'class': 'mt-1 block w-full p-2 border border-gray-300 rounded-md shadow-sm'}),
            'telefono': forms.TextInput(attrs={'class': 'mt-1 block w-full p-2 border border-gray-300 rounded-md shadow-sm'}),
            'direccion': forms.Textarea(attrs={'class': 'mt-1 block w-full p-2 border border-gray-300 rounded-md shadow-sm', 'rows': 3}),
            'tipo_usuario': forms.Select(attrs={'class': 'mt-1 block w-full p-2 border border-gray-300 rounded-md shadow-sm'}),
        }
        error_messages = {
            'nombre_completo': {
                'required': 'El nombre del usuario es obligatorio.',
            },
            'correo_electronico': {
                'required': 'El correo electrónico es obligatorio.',
                'unique': 'Ya existe un usuario con este correo electrónico.'
            },
        }


class LoginForm(forms.Form):
    nombre_usuario = forms.CharField(
        label="Nombre de Usuario", 
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'mt-1 block w-full p-2 border border-gray-300 rounded-md shadow-sm'})
    )
    clave = forms.CharField(
        label="Contraseña", 
        widget=forms.PasswordInput(attrs={'class': 'mt-1 block w-full p-2 border border-gray-300 rounded-md shadow-sm'})
    )

class LoginUsuarioAdminForm(forms.ModelForm):
    clave = forms.CharField(label="Clave", widget=forms.PasswordInput)

    class Meta:
        model = LoginUsuario
        fields = ['nombre_usuario', 'clave']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["clave"])
        if commit:
            user.save()
        return user