# Importaciones
import json
import csv
from datetime import date, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.db.models import Q, Count, IntegerField
from django.db.models.functions import Cast, TruncMonth
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.utils import timezone

from .models import *
from .forms import *
from .decorators import login_required


def login_view(request):
    """
    Gestiona el inicio de sesión del bibliotecario.
    Si el método es POST, valida los datos del formulario.
    Si las credenciales son correctas, establece las variables de sesión para autenticar al bibliotecario y
    redirige a la página de inicio. 
    Si no, muestra los errores correspondientes.
    Si el método es GET, simplemente muestra el formulario de login vacío.
    """
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            nombre_usuario = form.cleaned_data['nombre_usuario']
            clave = form.cleaned_data['clave']
            
            try:
                # Busca al usuario en el modelo de Login
                user = LoginUsuario.objects.get(nombre_usuario=nombre_usuario)
                # Comprueba la contraseña
                if user.check_password(clave):
                    # Si la contraseña es correcta, se guardan datos en la sesión
                    request.session['login_usuario_id'] = user.id
                    request.session['login_usuario_nombre'] = user.nombre_usuario
                    return redirect('inicio')
                else:
                    form.add_error(None, "La contraseña es incorrecta.")
            except LoginUsuario.DoesNotExist:
                form.add_error(None, "El usuario no existe.")
    else:
        form = LoginForm()
    
    return render(request, 'GestionApp/login.html', {'form': form})


def logout_view(request):
    """
    Cierra la sesión del usuario actual.
    Elimina las variables de sesión de la petición y redirige a la página de login.
    """
    try:
        del request.session['login_usuario_id']
        del request.session['login_usuario_nombre']
    except KeyError:
        # Si las claves no existen en la sesión, no hace nada y continúa.
        pass
    return redirect('login')


@login_required
def inicio_view(request):
    """
    Vista principal que muestra el catálogo de libros con filtros.
    Permite filtrar los libros por texto (título o autor), categoría y editorial,
    usando los parámetros GET de la URL.
    """
    query_params = request.GET
    libros = Libro.objects.select_related('stock', 'categoria', 'editorial').all()

    q_text = query_params.get('q', None)
    categoria_id = query_params.get('categoria', None)
    editorial_id = query_params.get('editorial', None)

    if q_text:
        libros = libros.filter(Q(titulo__icontains=q_text) | Q(autor__icontains=q_text))
    if categoria_id:
        libros = libros.filter(categoria_id=categoria_id)
    if editorial_id:
        libros = libros.filter(editorial_id=editorial_id)

    contexto = {
        'resultados_libros': libros.distinct(),
        'categorias': Categoria.objects.all().order_by('tipo_categoria'),
        'editoriales': Editorial.objects.all().order_by('nombre_editorial'),
        'query_params': query_params,
    }
    return render(request, 'GestionApp/inicio.html', contexto)


@login_required
def libros_view(request):
    """
    Muestra una lista completa de todos los libros en el sistema.
    Permite realizar búsquedas simples por título o autor.
    """
    query = request.GET.get('q', '')
    campo = request.GET.get('campo', 'titulo')
    
    libros = Libro.objects.select_related('stock', 'categoria', 'editorial').all()
    
    if query:
        if campo == 'titulo':
            libros = libros.filter(titulo__icontains=query)
        elif campo == 'autor':
            libros = libros.filter(autor__icontains=query)

    return render(request, 'GestionApp/lista_libros.html', {
        'libros': libros.order_by('titulo'),
        'query': query,
        'campo_seleccionado': campo
    })


@login_required
def usuarios_view(request):
    """
    Muestra una lista de todos los usuarios registrados en la biblioteca.
    Permite realizar búsquedas por nombre o correo electrónico.
    """
    query = request.GET.get('q', '')
    campo = request.GET.get('campo', 'nombre_completo')
    
    usuarios = Usuario.objects.all()

    if query:
        if campo == 'nombre_completo':
            usuarios = usuarios.filter(nombre_completo__icontains=query)
        elif campo == 'correo_electronico':
            usuarios = usuarios.filter(correo_electronico__icontains=query)

    return render(request, 'GestionApp/lista_usuarios.html', {
        'usuarios': usuarios.order_by('nombre_completo'),
        'query': query,
        'campo_seleccionado': campo
    })


@login_required
def prestamos_view(request):
    """
    Vista para gestionar y visualizar el historial de préstamos.
    Permite filtrar los préstamos por estado ('activos', 'vencidos', 'devueltos')
    y buscar por nombre de usuario o título de libro.
    """
    estado_filtro = request.GET.get('estado', 'activos')
    query = request.GET.get('q', '')
    campo = request.GET.get('campo', 'usuario')
    
    prestamos = Prestamo.objects.select_related('usuario', 'login_usuario').prefetch_related('detalleprestamo_set__libro').all()

    today = timezone.now().date()

    if estado_filtro == 'activos':
        prestamos = prestamos.filter(fecha_devolucion__isnull=True, fecha_vencimiento__gte=today)
    elif estado_filtro == 'vencidos':
        prestamos = prestamos.filter(fecha_devolucion__isnull=True, fecha_vencimiento__lt=today)
    elif estado_filtro == 'devueltos':
        prestamos = prestamos.filter(fecha_devolucion__isnull=False)

    if query:
        if campo == 'usuario':
            prestamos = prestamos.filter(usuario__nombre_completo__icontains=query)
        elif campo == 'libro':
            prestamos = prestamos.filter(detalleprestamo__libro__titulo__icontains=query)

    contexto = {
        'prestamos': prestamos.distinct().order_by('-fecha_prestamo'),
        'estado_filtro': estado_filtro,
        'today': today,
        'query': query,
        'campo_seleccionado': campo
    }
    return render(request, 'GestionApp/lista_prestamos.html', contexto)


@login_required
def multas_view(request):
    """
    Muestra una lista de todas las multas generadas.
    Permite filtrar por estado ('Pendiente', 'Pagada') y buscar por nombre de usuario.
    """
    estado_filtro = request.GET.get('estado', 'Pendiente')
    query = request.GET.get('q', '')
    
    multas = Multa.objects.select_related('usuario', 'estado_multa').all()

    if estado_filtro != 'todas':
        multas = multas.filter(estado_multa__estado_multa=estado_filtro)

    if query:
        multas = multas.filter(usuario__nombre_completo__icontains=query)

    contexto = {
        'multas': multas.order_by('-fecha_generacion_multa'),
        'estado_filtro': estado_filtro,
        'query': query
    }
    return render(request, 'GestionApp/lista_multas.html', contexto)


@login_required
def reportes_view(request):
    """
    Simplemente renderiza la página de reportes. La lógica de generación
    de datos para los gráficos se maneja a través de una vista AJAX separada.
    """
    return render(request, 'GestionApp/reportes.html')


@login_required
def libro_form_view(request, isbn=None):
    """
    Gestiona la creación y edición de un libro. Es una vista que renderiza
    un formulario en un modal a través de peticiones AJAX.
    - Si `isbn` es None, se trata de la creación de un libro nuevo.
    - Si `isbn` tiene un valor, se edita el libro existente.
    Maneja la lógica de creación y actualización del stock asociado al libro.
    """
    instance = None
    if isbn:
        instance = get_object_or_404(Libro, pk=isbn)
    
    if request.method == 'POST':
        form = LibroForm(request.POST, instance=instance)

        if form.is_valid():
            copias = int(request.POST.get('copias_totales', 1))
            
            if instance:
                prestamos_activos = DetallePrestamo.objects.filter(libro=instance, prestamo__fecha_devolucion__isnull=True).count()

                if copias < prestamos_activos:
                    form.add_error('copias_totales', f"No se puede reducir a {copias} copias, porque ya hay {prestamos_activos} préstamos activos.")

                else:
                    instance.stock.copias_totales = copias
                    instance.stock.copias_disponibles = copias - prestamos_activos
                    instance.stock.save()
                    form.save()

            else:
                nuevo_stock = Stock.objects.create(copias_totales=copias, copias_disponibles=copias)
                libro = form.save(commit=False)
                libro.stock = nuevo_stock
                libro.save()
            
            if form.is_valid():
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': '¡Libro guardado exitosamente!'})
                return redirect('lista_libros')
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'errors': form.errors.as_json()})
    else:
        initial_data = {}

        if instance:
            initial_data['copias_totales'] = instance.stock.copias_totales

        else:
            last_numeric_isbn = Libro.objects.annotate(isbn_as_int=Cast('isbn', IntegerField())).order_by('-isbn_as_int').first()

            if last_numeric_isbn:
                next_isbn = last_numeric_isbn.isbn_as_int + 1

            else:
                next_isbn = 1
            initial_data['isbn'] = next_isbn

        form = LibroForm(instance=instance, initial=initial_data)

    return render(request, 'GestionApp/libro_form.html', {'form': form, 'instance': instance})


@login_required
@require_POST # Para asegurar que esta vista solo acepte peticiones POST
def libro_eliminar_view(request, isbn):
    """
    Gestiona la eliminación de un libro vía AJAX.
    Valida que el libro no tenga préstamos activos antes de permitir su eliminación.
    También elimina el registro de stock asociado.
    """
    libro = get_object_or_404(Libro, pk=isbn)
    prestamos_activos = DetallePrestamo.objects.filter(libro=libro, prestamo__fecha_devolucion__isnull=True).count()

    if prestamos_activos > 0:
        return JsonResponse({'success': False, 'error': f'No se puede eliminar. Este libro tiene {prestamos_activos} préstamo(s) activo(s).'})
    
    try:
        if libro.stock:
            libro.stock.delete()

        libro.delete()

        return JsonResponse({'success': True, 'message': 'Libro eliminado exitosamente.'})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def usuario_form_view(request, id=None):
    """
    Gestiona la creación y edición de un usuario. Funciona de manera similar
    a `libro_form_view`, manejando un formulario en un modal vía AJAX.
    """
    instance = None
    if id:
        instance = get_object_or_404(Usuario, pk=id)
    
    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': '¡Usuario guardado exitosamente!'})
            return redirect('lista_usuarios')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors.as_json()})
    else:
        form = UsuarioForm(instance=instance)
        
    return render(request, 'GestionApp/usuario_form.html', {'form': form, 'instance': instance})


@login_required
@require_POST
def usuario_eliminar_view(request, id):
    """
    Gestiona la eliminación de un usuario vía AJAX.
    Valida que el usuario no tenga préstamos activos antes de la eliminación.
    """
    usuario = get_object_or_404(Usuario, pk=id)
    prestamos_activos = Prestamo.objects.filter(usuario=usuario, fecha_devolucion__isnull=True).count()
    if prestamos_activos > 0:
        return JsonResponse({'success': False, 'error': f'No se puede eliminar. Este usuario tiene {prestamos_activos} préstamo(s) activo(s).'})
    
    try:
        usuario.delete()
        return JsonResponse({'success': True, 'message': 'Usuario eliminado exitosamente.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
def prestamo_crear_view(request):
    """
    Procesa la creación de un nuevo préstamo a través de una petición AJAX (POST).
    Recibe el ID del usuario y una lista de ISBNs de los libros seleccionados.

    Realiza varias validaciones críticas antes de crear el préstamo:
    1. Límite de préstamos por tipo de usuario.
    2. Si el usuario tiene multas pendientes.
    3. Disponibilidad de stock para cada libro solicitado.

    Utiliza una transacción atómica (`transaction.atomic`) para asegurar que todas
    las operaciones de base de datos se completen exitosamente o ninguna.
    """
    data = json.loads(request.body)
    usuario_id = data.get('usuario_id')
    libro_isbns = data.get('libros', [])
    try:
        with transaction.atomic():
            usuario = Usuario.objects.get(pk=usuario_id)
            login_usuario = LoginUsuario.objects.get(pk=request.session.get('login_usuario_id'))
            
            limites = {'basica': 2, 'media': 3, 'universitario': 5, 'adulto': 3}
            limite_prestamo = limites.get(usuario.tipo_usuario, 3)
            prestamos_activos = Prestamo.objects.filter(usuario=usuario, fecha_devolucion__isnull=True).count()

            if (prestamos_activos + len(libro_isbns)) > limite_prestamo:
                return JsonResponse({'success': False, 'error': f'Límite de préstamo excedido. El usuario puede pedir {limite_prestamo - prestamos_activos} libro(s) más.'})

            multas_pendientes = Multa.objects.filter(usuario=usuario, estado_multa__estado_multa='Pendiente').exists()

            if multas_pendientes:
                return JsonResponse({'success': False, 'error': 'El usuario tiene multas pendientes y no puede realizar nuevos préstamos.'})

            libros_a_prestar = Libro.objects.filter(isbn__in=libro_isbns, stock__copias_disponibles__gt=0)

            if len(libros_a_prestar) != len(libro_isbns):
                return JsonResponse({'success': False, 'error': 'Uno o más libros seleccionados ya no están disponibles.'})

            nuevo_prestamo = Prestamo.objects.create(
                usuario=usuario,
                login_usuario=login_usuario,
                fecha_vencimiento=date.today() + timedelta(days=14)
            )
            for libro in libros_a_prestar:
                DetallePrestamo.objects.create(prestamo=nuevo_prestamo, libro=libro)
                libro.stock.copias_disponibles -= 1
                libro.stock.save()
                
            return JsonResponse({'success': True, 'message': '¡Préstamo registrado exitosamente!'})
    except Usuario.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'El usuario seleccionado no existe.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Ocurrió un error inesperado: {str(e)}'})


@require_POST
def get_libros_api(request):
    """
    API interna para obtener detalles de libros a partir de una lista de ISBNs.
    Utilizada por el frontend para mostrar la lista de libros en la selección de préstamo.
    """
    try:
        data = json.loads(request.body)
        isbns = data.get('isbns', [])
        if not isbns:
            return JsonResponse({'libros': []})
        libros = Libro.objects.filter(isbn__in=isbns)
        libros_data = list(libros.values('isbn', 'titulo', 'autor'))
        return JsonResponse({'libros': libros_data})
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_usuarios_api(request):
    """
    API interna para obtener una lista de todos los usuarios.
    Utilizada para poblar el selector de usuarios en la página de préstamos.
    """
    usuarios = Usuario.objects.all().order_by('nombre_completo')
    usuarios_data = list(usuarios.values('id_usuario', 'nombre_completo'))
    return JsonResponse({'usuarios': usuarios_data})


@require_POST
def categoria_crear_ajax(request):
    """
    Permite crear una nueva categoría 'al vuelo' desde el formulario de libros,
    sin necesidad de recargar la página.
    """
    data = json.loads(request.body)
    nombre_categoria = data.get('nombre')
    if nombre_categoria:
        categoria, created = Categoria.objects.get_or_create(tipo_categoria=nombre_categoria)
        if created:
            return JsonResponse({'success': True, 'id': categoria.id, 'nombre': categoria.tipo_categoria})
        else:
            return JsonResponse({'success': False, 'error': 'Esa categoría ya existe.'})
    return JsonResponse({'success': False, 'error': 'Petición inválida.'})


@require_POST
def editorial_crear_ajax(request):
    """
    Permite crear una nueva editorial 'al vuelo' desde el formulario de libros.
    """
    data = json.loads(request.body)
    nombre_editorial = data.get('nombre')
    if nombre_editorial:
        editorial, created = Editorial.objects.get_or_create(nombre_editorial=nombre_editorial)
        if created:
            return JsonResponse({'success': True, 'id': editorial.id, 'nombre': editorial.nombre_editorial})
        else:
            return JsonResponse({'success': False, 'error': 'Esa editorial ya existe.'})
    return JsonResponse({'success': False, 'error': 'Petición inválida.'})


@require_POST
@login_required
def devolucion_prestamo_view(request, prestamo_id):
    """
    Registra la devolución de un préstamo.
    Actualiza la fecha de devolución y restaura el stock de los libros devueltos.
    NOTA: La generación de multas fue desacoplada y ahora es manejada por un
    comando de gestión (`generar_multas`) para mejorar la fiabilidad.
    """
    try:
        with transaction.atomic():
            prestamo = get_object_or_404(Prestamo, pk=prestamo_id, fecha_devolucion__isnull=True)
            prestamo.fecha_devolucion = date.today()
            
            detalles = DetallePrestamo.objects.filter(prestamo=prestamo)
            for detalle in detalles:
                detalle.libro.stock.copias_disponibles += 1
                detalle.libro.stock.save()
            
            prestamo.save()
            return JsonResponse({'success': True, 'message': 'Devolución registrada exitosamente.'})

    except Prestamo.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'El préstamo no existe o ya fue devuelto.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Ocurrió un error: {str(e)}'}, status=500)


@require_POST
@login_required
def renovar_prestamo_view(request, prestamo_id):
    """
    Gestiona la renovación de un préstamo existente vía AJAX (POST).
    Añade 14 días a la fecha de vencimiento.

    Implementa las siguientes reglas de negocio:
    1. Un préstamo no puede tener más de 2 renovaciones.
    2. Un préstamo vencido solo puede ser renovado si tiene 3 días de retraso o menos.
    """
    try:
        prestamo = get_object_or_404(Prestamo, pk=prestamo_id, fecha_devolucion__isnull=True)

        if prestamo.cantidad_renovaciones >= 2:
            return JsonResponse({'success': False, 'error': 'Este préstamo ya ha alcanzado el límite de renovaciones.'})

        hoy = date.today()
        if hoy > prestamo.fecha_vencimiento:
            dias_retraso = (hoy - prestamo.fecha_vencimiento).days
            if dias_retraso > 3:
                return JsonResponse({'success': False, 'error': f'No se puede renovar. El préstamo tiene {dias_retraso} días de retraso.'})

        prestamo.fecha_vencimiento += timedelta(days=14)
        prestamo.cantidad_renovaciones += 1
        prestamo.save()
        
        return JsonResponse({'success': True, 'message': f'Préstamo renovado. Nueva fecha de vencimiento: {prestamo.fecha_vencimiento.strftime("%Y-%m-%d")}.'})

    except Prestamo.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'El préstamo no existe o ya fue devuelto.'}, status=404)
    

@require_POST
@login_required
def multa_pagar_view(request, multa_id):
    """
    Marca una multa como 'Pagada' y registra la fecha del pago.
    """
    try:
        multa = get_object_or_404(Multa, pk=multa_id)
        estado_pagada, _ = EstadoMulta.objects.get_or_create(estado_multa='Pagada')
        
        multa.estado_multa = estado_pagada
        multa.fecha_pago_multa = timezone.now().date()
        multa.save()
        
        return JsonResponse({'success': True, 'message': 'Multa marcada como pagada.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_POST
def generar_reporte_ajax(request):
    """
    Endpoint AJAX para generar los datos de los reportes personalizados.
    Recibe qué se quiere analizar ('libros', 'usuarios', etc.), la métrica
    y la agrupación, y devuelve los datos procesados para que Chart.js los grafique.
    Utiliza `annotate` y `Count` del ORM de Django para realizar los cálculos
    de forma eficiente en la base de datos.
    """
    try:
        data = json.loads(request.body)
        analizar = data.get('analizar')
        metrica = data.get('metrica')
        agrupar_por = data.get('agrupar_por')

        labels = []
        dataset = []
        qs = None

        if analizar == 'libros':

            if metrica == 'top_5':
                qs = Libro.objects.annotate(conteo_prestamos=Count('detalleprestamo')).filter(conteo_prestamos__gt=0).order_by('-conteo_prestamos')[:5]

                if qs:
                    labels = [libro.titulo for libro in qs]
                    dataset = [libro.conteo_prestamos for libro in qs]

            elif metrica == 'agrupado':
                if agrupar_por == 'categoria':
                    qs = Categoria.objects.annotate(conteo_prestamos=Count('libro__detalleprestamo')).filter(conteo_prestamos__gt=0).order_by('-conteo_prestamos')

                    if qs:
                        labels = [cat.tipo_categoria for cat in qs]
                        dataset = [cat.conteo_prestamos for cat in qs]

                elif agrupar_por == 'editorial':
                    qs = Editorial.objects.annotate(conteo_prestamos=Count('libro__detalleprestamo')).filter(conteo_prestamos__gt=0).order_by('-conteo_prestamos')

                    if qs:
                        labels = [ed.nombre_editorial for ed in qs]
                        dataset = [ed.conteo_prestamos for ed in qs]

        elif analizar == 'usuarios':
            if metrica == 'top_5_activos':
                qs = Usuario.objects.annotate(conteo_prestamos=Count('prestamo')).filter(conteo_prestamos__gt=0).order_by('-conteo_prestamos')[:5]

                if qs:
                    labels = [user.nombre_completo for user in qs]
                    dataset = [user.conteo_prestamos for user in qs]

            elif metrica == 'mas_multados':
                qs = Usuario.objects.annotate(conteo_multas=Count('multa')).filter(conteo_multas__gt=0).order_by('-conteo_multas')[:10]

                if qs:
                    labels = [user.nombre_completo for user in qs]
                    dataset = [user.conteo_multas for user in qs]

        elif analizar == 'actividad':
            if metrica == 'prestamos_mes':
                qs = Prestamo.objects.annotate(mes=TruncMonth('fecha_prestamo')).values('mes').annotate(conteo=Count('id_prestamo')).order_by('mes')

                if qs:
                    labels = [item['mes'].strftime('%Y-%m') for item in qs]
                    dataset = [item['conteo'] for item in qs]

            elif metrica == 'nuevos_usuarios_mes':
                qs = Usuario.objects.annotate(mes=TruncMonth('fecha_registro')).values('mes').annotate(conteo=Count('id_usuario')).order_by('mes')

                if qs:
                    labels = [item['mes'].strftime('%Y-%m') for item in qs]
                    dataset = [item['conteo'] for item in qs]
        
        if qs is None:
            return JsonResponse({'success': False, 'error': f'Combinación de reporte inválida.'})

        return JsonResponse({'success': True, 'labels': labels, 'data': dataset})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def exportar_libros_csv(request):
    """
    Genera y devuelve un archivo CSV con la lista de todos los libros.
    Utiliza el módulo `csv` de Python y `HttpResponse` para construir el archivo en memoria.
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="libros.csv"'
    response.write(u'\ufeff'.encode('utf8'))

    writer = csv.writer(response)
    writer.writerow(['ISBN', 'Título', 'Autor', 'Año Publicación', 'Categoría', 'Editorial', 'Copias Totales', 'Copias Disponibles'])

    libros = Libro.objects.select_related('categoria', 'editorial', 'stock').all()
    for libro in libros:
        writer.writerow([
            libro.isbn,
            libro.titulo,
            libro.autor,
            libro.ano_publicacion,
            libro.categoria.tipo_categoria if libro.categoria else '',
            libro.editorial.nombre_editorial if libro.editorial else '',
            libro.stock.copias_totales,
            libro.stock.copias_disponibles
        ])
    return response


@login_required
def exportar_usuarios_csv(request):
    """
    Genera y devuelve un archivo CSV con la lista de todos los usuarios.
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="usuarios.csv"'
    response.write(u'\ufeff'.encode('utf8'))

    writer = csv.writer(response)
    writer.writerow(['ID Usuario', 'Nombre Completo', 'Correo Electrónico', 'Teléfono', 'Dirección', 'Tipo Usuario', 'Fecha Registro'])

    usuarios = Usuario.objects.all()
    for usuario in usuarios:
        writer.writerow([
            usuario.id_usuario,
            usuario.nombre_completo,
            usuario.correo_electronico,
            usuario.telefono,
            usuario.direccion,
            usuario.get_tipo_usuario_display(),
            usuario.fecha_registro
        ])
    return response


@login_required
def exportar_prestamos_csv(request):
    """
    Genera un archivo CSV con el detalle de cada libro prestado individualmente.
    Calcula el estado ('Activo', 'Vencido', 'Devuelto') para cada registro.
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="prestamos_detallado.csv"'
    response.write(u'\ufeff'.encode('utf8'))

    writer = csv.writer(response)
    writer.writerow(['ID Préstamo', 'Usuario', 'Libro Prestado (ISBN)', 'Título del Libro', 'Fecha Préstamo', 'Fecha Vencimiento', 'Fecha Devolución', 'Estado'])

    detalles = DetallePrestamo.objects.select_related('prestamo', 'libro', 'prestamo__usuario').all().order_by('-prestamo__fecha_prestamo')
    today = timezone.now().date()

    for detalle in detalles:
        estado = "Devuelto"
        if not detalle.prestamo.fecha_devolucion:
            if detalle.prestamo.fecha_vencimiento < today:
                estado = "Vencido"
            else:
                estado = "Activo"

        writer.writerow([
            detalle.prestamo.id_prestamo,
            detalle.prestamo.usuario.nombre_completo,
            detalle.libro.isbn,
            detalle.libro.titulo,
            detalle.prestamo.fecha_prestamo,
            detalle.prestamo.fecha_vencimiento,
            detalle.prestamo.fecha_devolucion if detalle.prestamo.fecha_devolucion else 'N/A',
            estado
        ])
    return response