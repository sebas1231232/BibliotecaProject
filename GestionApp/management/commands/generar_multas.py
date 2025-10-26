from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from datetime import date
from GestionApp.models import Prestamo, Multa, EstadoMulta

class Command(BaseCommand):
    help = 'Busca préstamos vencidos y genera o actualiza multas automáticamente.'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write('Iniciando la tarea de generación de multas...')
        
        today = timezone.now().date()
        
        try:
            estado_pendiente = EstadoMulta.objects.get(estado_multa='Pendiente')
        except EstadoMulta.DoesNotExist:
            self.stdout.write(self.style.ERROR("El estado de multa 'Pendiente' no existe. Abortando."))
            return

        prestamos_vencidos = Prestamo.objects.filter(
            fecha_devolucion__isnull=True,
            fecha_vencimiento__lt=today
        )

        multas_generadas = 0
        multas_actualizadas = 0

        for prestamo in prestamos_vencidos:
            dias_retraso = (today - prestamo.fecha_vencimiento).days
            
            if dias_retraso >= 4:
                monto_calculado = (dias_retraso - 3) * 500
                
                multa, created = Multa.objects.update_or_create(
                    prestamo=prestamo,
                    defaults={
                        'usuario': prestamo.usuario,
                        'monto_multa': monto_calculado,
                        'estado_multa': estado_pendiente,
                    }
                )
                
                if created:
                    multas_generadas += 1
                    self.stdout.write(f"  [+] Creada multa para Préstamo ID {prestamo.id_prestamo} por ${monto_calculado}")
                else:
                    multas_actualizadas += 1
                    self.stdout.write(f"  [*] Actualizada multa para Préstamo ID {prestamo.id_prestamo} a ${monto_calculado}")

        self.stdout.write(self.style.SUCCESS(f'Tarea completada. Multas generadas: {multas_generadas}. Multas actualizadas: {multas_actualizadas}.'))