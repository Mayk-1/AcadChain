from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from blockchain.blockchain_core import ejecutar_minado


class Command(BaseCommand):
    help = 'Agrupa los certificados pendientes en bloques usando un Árbol de Merkle y actualiza la lista enlazada'

    def add_arguments(self, parser):
        # Permitimos configurar el tamaño máximo de certificados por bloque
        parser.add_argument(
            '--tamano_lote',
            type=int,
            default=1000,
            help='Cantidad de certificados por cada bloque (Por defecto: 1000)'
        )
        # Opcional: firmar los bloques minados a nombre de una autoridad.
        # Sin este flag, los bloques quedan sin firma digital (firmante=None).
        parser.add_argument(
            '--usuario',
            type=str,
            default=None,
            help='Username de la autoridad (is_staff) que firma los bloques minados. Sin este flag, los bloques quedan sin firmar.'
        )

    def handle(self, *args, **options):
        tamano_lote = options['tamano_lote']
        usuario = None

        if options['usuario']:
            try:
                usuario = User.objects.get(username=options['usuario'])
            except User.DoesNotExist:
                raise CommandError(f"No existe ningún usuario con username '{options['usuario']}'.")

            if not usuario.is_staff:
                raise CommandError(f"El usuario '{usuario.username}' no tiene permisos de autoridad (is_staff=False).")

        resultado = ejecutar_minado(tamano_lote=tamano_lote, usuario=usuario)

        if resultado['bloques_creados'] == 0:
            self.stdout.write(self.style.SUCCESS("No hay certificados pendientes por procesar."))
            return

        self.stdout.write(self.style.WARNING(
            f"Detectados {resultado['certificados_procesados']} certificados pendientes. Procesados en {resultado['bloques_creados']} bloque(s)."
        ))

        for bloque in resultado['bloques']:
            firma_info = f" | Firmado por: {bloque['firmante']}" if bloque['firmante'] else " | Sin firma digital"
            self.stdout.write(self.style.SUCCESS(
                f"-> Bloque #{bloque['index']} creado exitosamente. Hash: {bloque['block_hash'][:15]}... | Contiene {bloque['total_certificados']} certificados.{firma_info}"
            ))

        self.stdout.write(self.style.SUCCESS(
            f"¡Proceso terminado! Se han generado {resultado['bloques_creados']} bloques nuevos en la Blockchain."
        ))
