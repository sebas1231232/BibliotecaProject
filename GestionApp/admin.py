from django.contrib import admin
from .models import *
from .forms import LoginUsuarioAdminForm

@admin.register(LoginUsuario)
class LoginUsuarioAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre_usuario')
    form = LoginUsuarioAdminForm

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('id_usuario', 'nombre_completo', 'correo_electronico', 'tipo_usuario')

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('id', 'tipo_categoria')

@admin.register(Editorial)
class EditorialAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre_editorial')

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('id', 'copias_totales', 'copias_disponibles')

@admin.register(Libro)
class LibroAdmin(admin.ModelAdmin):
    list_display = ('isbn', 'titulo', 'autor', 'categoria', 'editorial')

@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    list_display = ('id_prestamo', 'usuario', 'login_usuario', 'fecha_prestamo', 'fecha_vencimiento')

@admin.register(DetallePrestamo)
class DetallePrestamoAdmin(admin.ModelAdmin):
    list_display = ('id', 'prestamo', 'libro')

@admin.register(EstadoMulta)
class EstadoMultaAdmin(admin.ModelAdmin):
    list_display = ('id', 'estado_multa')

@admin.register(Multa)
class MultaAdmin(admin.ModelAdmin):
    list_display = ('id_multa', 'prestamo', 'usuario', 'monto_multa', 'estado_multa')