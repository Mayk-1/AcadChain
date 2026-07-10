import random
from django.core.management.base import BaseCommand
from blockchain.models import CertificadoModel
from blockchain.blockchain_core import calcular_sha256

class Command(BaseCommand):
    help = 'Genera datos sintéticos masivos de certificados para pruebas de rendimiento'

    def add_arguments(self, parser):
        # Permite pasar la cantidad de registros como argumento en la terminal
        parser.add_argument('total', type=int, help='Cantidad de certificados a generar')

    def handle(self, *args, **kwargs):
        total_registros = kwargs['total']
        
        # Listas base para combinar datos aleatorios
        nombres = ['Daniel', 'Juan', 'Percy', 'Alex', 'Ruth', 'Diana', 'Carlos', 'Luz', 'Edgar', 'Alvaro', 'Anali', 'Jhoel']
        apellidos = ['Garcia', 'Torres', 'Mamani', 'Quispe', 'Flores', 'Condori', 'Chura', 'Ramos', 'Velasquez', 'Apaza']
        carreras = [
            'Ingeniería de Sistemas', 
            'Ingeniería Mecánica Eléctrica', 
            'Ingeniería Electrónica',
            'Administración',
            'Contabilidad'
        ]

        self.stdout.write(self.style.WARNING(f"Iniciando la generación de {total_registros} certificados sintéticos..."))

        certificados_a_crear = []
        
        for i in range(total_registros):
            # 1. Generar datos ficticios combinados
            nombre_completo = f"{random.choice(nombres)} {random.choice(apellidos)} {random.choice(apellidos)}"
            carrera = random.choice(carreras)
            
            # Código único simulado: Año + Código Carrera + Correlativo
            codigo_unico = f"2026-{random.randint(10,99)}-{100000 + i}"
            
            # 2. Simular los datos del "PDF" metidos en un string para calcular su SHA-256
            # En la vida real, aquí meterías los bytes del archivo PDF.
            datos_para_hash = f"{codigo_unico}|{nombre_completo}|{carrera}|Universidad_Nacional_del_Altiplano"
            hash_sha256 = calcular_sha256(datos_para_hash)
            
            # 3. Crear el objeto del modelo en memoria (sin guardar en la BD aún para mayor velocidad)
            certificado = CertificadoModel(
                codigo_unico=codigo_unico,
                nombre_alumno=nombre_completo,
                carrera=carrera,
                hash_certificado=hash_sha256,
                bloque=None # Quedan "pendientes" de ser minados/agrupados en un bloque
            )
            certificados_a_crear.append(certificado)

        # 4. Inserción masiva ultra rápida en MySQL usando bulk_create
        # Esto hace una sola consulta SQL pesada en lugar de miles de consultas individuales
        CertificadoModel.objects.bulk_create(certificados_a_crear)

        self.stdout.write(self.style.SUCCESS(f"¡Éxito! Se han insertado {total_registros} certificados en MySQL en estado 'Pendiente'."))