from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.inicio_view, name='inicio'),
    path('inicio/', views.inicio_view, name='inicio-alias'),
    
    path('libros/', views.libros_view, name='lista_libros'),
    path('libros/nuevo/', views.libro_form_view, name='libro_crear'),
    path('libros/editar/<str:isbn>/', views.libro_form_view, name='libro_editar'),
    path('libros/eliminar/<str:isbn>/', views.libro_eliminar_view, name='libro_eliminar'),
    
    path('usuarios/', views.usuarios_view, name='lista_usuarios'),
    path('usuarios/nuevo/', views.usuario_form_view, name='usuario_crear'),
    path('usuarios/editar/<int:id>/', views.usuario_form_view, name='usuario_editar'),
    path('usuarios/eliminar/<int:id>/', views.usuario_eliminar_view, name='usuario_eliminar'),
    
    path('prestamos/', views.prestamos_view, name='lista_prestamos'),
    path('prestamos/crear/', views.prestamo_crear_view, name='prestamo_crear'),
    path('prestamos/<int:prestamo_id>/devolver/', views.devolucion_prestamo_view, name='devolucion_prestamo'),
    path('prestamos/<int:prestamo_id>/renovar/', views.renovar_prestamo_view, name='renovar_prestamo'),

    path('multas/', views.multas_view, name='lista_multas'),
    path('multas/<int:multa_id>/pagar/', views.multa_pagar_view, name='multa_pagar'),
    
    path('reportes/', views.reportes_view, name='reportes'),
    path('reportes/generar_reporte_ajax/', views.generar_reporte_ajax, name='generar_reporte_ajax'),
    
    path('api/get-libros/', views.get_libros_api, name='api_get_libros'),
    path('api/get-usuarios/', views.get_usuarios_api, name='api_get_usuarios'),
    
    path('categorias/crear/ajax/', views.categoria_crear_ajax, name='categoria_crear_ajax'),
    path('editoriales/crear/ajax/', views.editorial_crear_ajax, name='editorial_crear_ajax'),

    path('exportar/libros/', views.exportar_libros_csv, name='exportar_libros_csv'),
    path('exportar/usuarios/', views.exportar_usuarios_csv, name='exportar_usuarios_csv'),
    path('exportar/prestamos/', views.exportar_prestamos_csv, name='exportar_prestamos_csv'),
]   