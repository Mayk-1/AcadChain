from django.shortcuts import render

# Create your views here.
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import BloqueModel, CertificadoModel

def listar_blockchain(request):
    """
    Endpoint GET: Retorna todos los bloques de la lista enlazada 
    ordenados cronológicamente.
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido. Use GET.'}, status=405)
        
    bloques = BloqueModel.objects.order_by('index')
    lista_bloques = []
    
    for b in bloques:
        lista_bloques.append({
            'index': b.index,
            'timestamp': b.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'merkle_root': b.merkle_root,
            'previous_hash': b.previous_hash,
            'block_hash': b.block_hash,
            'total_certificados': b.certificados.count() # Relación FK inversa
        })
        
    return JsonResponse({'longitud_cadena': len(lista_bloques), 'blockchain': lista_bloques}, safe=False)


@csrf_exempt # Desactivamos CSRF temporalmente solo para facilitar pruebas de desarrollo (POST)
def verificar_certificado(request):
    """
    Endpoint POST: Recibe el 'codigo_unico' del certificado,
    lo busca en MySQL y verifica su autenticidad y el bloque contenedor.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido. Use POST.'}, status=405)
        
    try:
        # Leer los datos JSON que envía el cliente
        data = json.loads(request.body)
        codigo = data.get('codigo_unico')
        
        if not codigo:
            return JsonResponse({'error': 'Falta el campo obligatorio: codigo_unico'}, status=400)
            
        # Buscar el certificado en la base de datos
        certificado = CertificadoModel.objects.filter(codigo_unico=codigo).first()
        
        if not certificado:
            return JsonResponse({
                'autentico': False,
                'mensaje': 'El certificado no existe en los registros de la universidad.'
            }, status=404)
            
        # Verificar si ya fue integrado a un bloque de la blockchain
        if certificado.bloque is None:
            return JsonResponse({
                'autentico': False,
                'mensaje': 'El certificado existe pero aún está en la cola de procesamiento (no minado).'
            }, status=200)
            
        # Si tiene bloque asignado, devolvemos toda la traza de seguridad criptográfica
        return JsonResponse({
            'autentico': True,
            'mensaje': 'Certificado verificado e inmutable.',
            'datos_alumno': {
                'nombre': certificado.nombre_alumno,
                'carrera': certificado.carrera,
                'hash_sha256': certificado.hash_certificado
            },
            'evidencia_blockchain': {
                'bloque_index': certificado.bloque.index,
                'merkle_root_del_bloque': certificado.bloque.merkle_root,
                'hash_del_bloque': certificado.bloque.block_hash,
                'hash_bloque_anterior': certificado.bloque.previous_hash,
                'fecha_sellado': certificado.bloque.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }
        }, status=200)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Formato JSON inválido.'}, status=400)