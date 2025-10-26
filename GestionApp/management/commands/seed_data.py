import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from faker import Faker
from GestionApp.models import (
    LoginUsuario, Usuario, Categoria, Editorial, Stock, Libro,
    Prestamo, DetallePrestamo, EstadoMulta, Multa
)

class Command(BaseCommand):
    help = 'Puebla la base de datos con una gran cantidad de datos de prueba.'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        if Usuario.objects.exists() or Libro.objects.exists():
            self.stdout.write(self.style.WARNING('La base de datos ya contiene datos. Abortando el seeder.'))
            return

        self.stdout.write('Iniciando el seeder...')
        fake = Faker('es_ES')

        self.stdout.write('Creando usuario de acceso principal...')
        admin_user = LoginUsuario(nombre_usuario='bibliotecario')
        admin_user.set_password('bibliotecario1234')
        admin_user.save()

        estado_pendiente, _ = EstadoMulta.objects.get_or_create(estado_multa='Pendiente')
        estado_pagada, _ = EstadoMulta.objects.get_or_create(estado_multa='Pagada')
        
        self.stdout.write('Creando categorías y editoriales...')
        categorias_nombres = ['Novela Histórica', 'Ciencia Ficción', 'Historia Universal', 'Biografía', 'Fantasía Épica', 'Misterio y Suspense', 'Literatura Infantil', 'Desarrollo de Software', 'Poesía Clásica', 'Autoayuda y Bienestar']
        editoriales_nombres = ['Planeta', 'Anagrama', 'Penguin Random House', 'Siglo XXI', 'Salamandra', 'Minotauro', 'Alfaguara', 'Ediciones B', 'Cátedra', 'Alianza Editorial']
        
        categorias = [Categoria.objects.create(tipo_categoria=nombre) for nombre in categorias_nombres]
        editoriales = [Editorial.objects.create(nombre_editorial=nombre) for nombre in editoriales_nombres]

        self.stdout.write('Creando 50 usuarios...')
        tipos_usuario = ['adulto', 'universitario', 'basica']
        usuarios = []
        for _ in range(50):
            profile = fake.profile()
            usuario = Usuario.objects.create(
                nombre_completo=profile['name'],
                correo_electronico=profile['mail'],
                telefono=fake.phone_number(),
                direccion=profile['address'],
                tipo_usuario=random.choice(tipos_usuario)
            )
            usuarios.append(usuario)

        self.stdout.write('Creando 150 libros...')
        libros = []
        for i in range(150):
            stock = Stock.objects.create(copias_totales=random.randint(1, 15), copias_disponibles=0)
            stock.copias_disponibles = stock.copias_totales
            stock.save()
            
            libro = Libro.objects.create(
                isbn=str(9780000000000 + i),
                titulo=fake.catch_phrase().title(),
                autor=fake.name(),
                ano_publicacion=str(fake.year()),
                categoria=random.choice(categorias),
                editorial=random.choice(editoriales),
                stock=stock
            )
            libros.append(libro)

        self.stdout.write('Creando un historial extenso de préstamos y multas...')
        today = timezone.now().date()
        
        def get_random_book():
            book = random.choice(libros)
            while book.stock.copias_disponibles == 0:
                book = random.choice(libros)
            return book

        for _ in range(15):
            fecha_prestamo = today - timedelta(days=random.randint(1, 10))
            prestamo = Prestamo.objects.create(usuario=random.choice(usuarios), login_usuario=admin_user, fecha_prestamo=fecha_prestamo, fecha_vencimiento=fecha_prestamo + timedelta(days=14))
            libro_prestado = get_random_book()
            DetallePrestamo.objects.create(prestamo=prestamo, libro=libro_prestado)
            libro_prestado.stock.copias_disponibles -= 1
            libro_prestado.stock.save()

        for _ in range(20):
            fecha_prestamo = today - timedelta(days=random.randint(20, 40))
            prestamo = Prestamo.objects.create(usuario=random.choice(usuarios), login_usuario=admin_user, fecha_prestamo=fecha_prestamo, fecha_vencimiento=fecha_prestamo + timedelta(days=14))
            libro_prestado = get_random_book()
            DetallePrestamo.objects.create(prestamo=prestamo, libro=libro_prestado)
            libro_prestado.stock.copias_disponibles -= 1
            libro_prestado.stock.save()

        for _ in range(40):
            usuario_con_prestamo = random.choice(usuarios)
            fecha_prestamo = today - timedelta(days=random.randint(30, 365))
            fecha_vencimiento = fecha_prestamo + timedelta(days=14)
            
            if random.random() < 0.3:
                dias_retraso = random.randint(4, 40)
                fecha_devolucion = fecha_vencimiento + timedelta(days=dias_retraso)
                
                monto_multa = (dias_retraso - 3) * 500 

                prestamo_multado = Prestamo.objects.create(usuario=usuario_con_prestamo, login_usuario=admin_user, fecha_prestamo=fecha_prestamo, fecha_vencimiento=fecha_vencimiento, fecha_devolucion=fecha_devolucion)
                libro_prestado_multa = get_random_book()
                DetallePrestamo.objects.create(prestamo=prestamo_multado, libro=libro_prestado_multa)
                
                multa = Multa.objects.create(prestamo=prestamo_multado, usuario=usuario_con_prestamo, monto_multa=monto_multa, estado_multa=random.choice([estado_pendiente, estado_pagada]))
                if multa.estado_multa == estado_pagada:
                    multa.fecha_pago_multa = fecha_devolucion + timedelta(days=random.randint(1, 10))
                    multa.save()
            else:
                fecha_devolucion = fecha_prestamo + timedelta(days=random.randint(1, 13))
                prestamo_normal = Prestamo.objects.create(usuario=usuario_con_prestamo, login_usuario=admin_user, fecha_prestamo=fecha_prestamo, fecha_vencimiento=fecha_vencimiento, fecha_devolucion=fecha_devolucion)
                libro_prestado_normal = get_random_book()
                DetallePrestamo.objects.create(prestamo=prestamo_normal, libro=libro_prestado_normal)
        
        self.stdout.write(self.style.SUCCESS('¡Seeder completado exitosamente con un gran volumen de datos!'))