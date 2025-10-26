from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class LoginUsuario(models.Model):
    id = models.AutoField(primary_key=True)
    nombre_usuario = models.CharField(max_length=100, unique=True)
    clave = models.CharField(max_length=128)
    def set_password(self, raw_password): self.clave = make_password(raw_password)
    def check_password(self, raw_password): return check_password(raw_password, self.clave)
    def __str__(self): return self.nombre_usuario

class Usuario(models.Model):
    TIPO_USUARIO_CHOICES = [
        ('basica', 'Estudiante (Básica/Media)'),
        ('universitario', 'Universitario'),
        ('adulto', 'Adulto'),
    ]
    id_usuario = models.AutoField(primary_key=True)
    nombre_completo = models.CharField(max_length=255)
    correo_electronico = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    tipo_usuario = models.CharField(max_length=50, choices=TIPO_USUARIO_CHOICES, default='adulto')
    fecha_registro = models.DateField(auto_now_add=True)
    def __str__(self): return self.nombre_completo

class Categoria(models.Model):
    id = models.AutoField(primary_key=True)
    tipo_categoria = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.tipo_categoria

class Editorial(models.Model):
    id = models.AutoField(primary_key=True)
    nombre_editorial = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.nombre_editorial

class Stock(models.Model):
    id = models.AutoField(primary_key=True)
    copias_totales = models.PositiveIntegerField(default=1)
    copias_disponibles = models.PositiveIntegerField(default=1)
    def __str__(self): return f"Stock ID: {self.id}"

class Libro(models.Model):
    isbn = models.CharField(max_length=20, primary_key=True)
    titulo = models.CharField(max_length=255)
    autor = models.CharField(max_length=255)
    ano_publicacion = models.CharField(max_length=4, blank=True, null=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    editorial = models.ForeignKey(Editorial, on_delete=models.SET_NULL, null=True, blank=True)
    stock = models.OneToOneField(Stock, on_delete=models.CASCADE)
    def __str__(self): return self.titulo

class Prestamo(models.Model):
    id_prestamo = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    login_usuario = models.ForeignKey(LoginUsuario, on_delete=models.CASCADE)
    fecha_prestamo = models.DateField(auto_now_add=True)
    fecha_vencimiento = models.DateField()
    fecha_devolucion = models.DateField(blank=True, null=True)
    cantidad_renovaciones = models.PositiveIntegerField(default=0)
    def __str__(self): return f"Préstamo {self.id_prestamo}"

class DetallePrestamo(models.Model):
    id = models.AutoField(primary_key=True)
    prestamo = models.ForeignKey(Prestamo, on_delete=models.CASCADE)
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE)
    def __str__(self): return f"'{self.libro.titulo}' en préstamo {self.prestamo.id_prestamo}"

class EstadoMulta(models.Model):
    id = models.AutoField(primary_key=True)
    estado_multa = models.CharField(max_length=50, unique=True)
    def __str__(self): return self.estado_multa

class Multa(models.Model):
    id_multa = models.AutoField(primary_key=True)
    prestamo = models.OneToOneField(Prestamo, on_delete=models.CASCADE)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    monto_multa = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_generacion_multa = models.DateField(auto_now_add=True)
    fecha_pago_multa = models.DateField(blank=True, null=True)
    estado_multa = models.ForeignKey(EstadoMulta, on_delete=models.CASCADE)
    def __str__(self): return f"Multa para préstamo {self.prestamo.id_prestamo}"