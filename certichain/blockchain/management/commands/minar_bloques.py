from django.core.management.base import BaseCommand
from blockchain.models import CertificadoModel, BloqueModel
from blockchain.blockchain_core import MerkleTree, calcular_sha256, obtener_o_crear_genesis

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

    def handle(self, *args, **options):
        tamano_lote = options['tamano_lote']

        # 1. Asegurar que exista el bloque Génesis (Bloque 0)
        obtener_o_crear_genesis()

        # 2. Traer todos los certificados que no pertenecen a ningún bloque
        certificados_pendientes = CertificadoModel.objects.filter(bloque__isnull=True).order_by('id')
        total_pendientes = certificados_pendientes.count()

        if total_pendientes == 0:
            self.stdout.write(self.style.SUCCESS("No hay certificados pendientes por procesar."))
            return

        self.stdout.write(self.style.WARNING(f"Detectados {total_pendientes} certificados pendientes. Procesando en lotes de {tamano_lote}..."))

        # Convertimos el QuerySet a una lista para segmentarlo en memoria fácilmente
        lista_certificados = list(certificados_pendientes)
        bloques_creados = 0

        # Procesar en porciones (lotes)
        for i in range(0, len(lista_certificados), tamano_lote):
            lote_actual = lista_certificados[i : i + tamano_lote]
            
            # Extraer solo los hashes de este grupo de certificados
            lista_hashes = [cert.hash_certificado for cert in lote_actual]

            # 3. CONSTRUIR ÁRBOL DE MERKLE: Obtenemos la raíz común del lote
            arbol_merkle = MerkleTree(lista_hashes)
            merkle_root_actual = arbol_merkle.root

            # 4. CONEXIÓN DE LA LISTA ENLAZADA: Obtener el último bloque minado para sacar su hash
            ultimo_bloque = BloqueModel.objects.order_by('-index').first()
            nuevo_index = ultimo_bloque.index + 1
            previous_hash = ultimo_bloque.block_hash

            # Calcular el hash del bloque actual combinando sus propiedades
            string_contenido_bloque = f"{nuevo_index}{merkle_root_actual}{previous_hash}"
            hash_bloque_actual = calcular_sha256(string_contenido_bloque)

            # 5. GUARDAR EL NUEVO BLOQUE EN MYSQL
            nuevo_bloque = BloqueModel.objects.create(
                index=nuevo_index,
                merkle_root=merkle_root_actual,
                previous_hash=previous_hash,
                block_hash=hash_bloque_actual
            )

            # 6. VINCULAR LOS CERTIFICADOS AL BLOQUE Y GUARDAR SU PRUEBA DE MERKLE
            # Cada certificado necesita su propio camino de hashes (arbol_merkle.proofs[i])
            # para poder demostrar después, por su cuenta, que pertenece a este bloque.
            for cert, prueba_cert in zip(lote_actual, arbol_merkle.proofs):
                cert.bloque = nuevo_bloque
                cert.merkle_proof = prueba_cert

            CertificadoModel.objects.bulk_update(lote_actual, ['bloque', 'merkle_proof'])

            self.stdout.write(self.style.SUCCESS(
                f"-> Bloque #{nuevo_index} creado exitosamente. Hash: {hash_bloque_actual[:15]}... | Contiene {len(lote_actual)} certificados."
            ))
            bloques_creados += 1

        self.stdout.write(self.style.SUCCESS(f"¡Proceso terminado! Se han generado {bloques_creados} bloques nuevos en la Blockchain."))