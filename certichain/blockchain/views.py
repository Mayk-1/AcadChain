from django.shortcuts import render

# Create your views here.
import json
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from .models import BloqueModel, CertificadoModel
from .blockchain_core import calcular_sha256, verificar_prueba_merkle, validar_cadena

# Tamaño máximo aceptado para un PDF de certificado (10 MB)
MAX_TAMANO_PDF_BYTES = 10 * 1024 * 1024

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


def validar_integridad_cadena(request):
    """
    Endpoint GET: Recorre toda la cadena de bloques y confirma que
    cada eslabón (previous_hash <-> block_hash) sigue siendo válido,
    es decir, que ningún bloque fue alterado, borrado o insertado
    fuera de orden desde que se minó.
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido. Use GET.'}, status=405)

    resultado = validar_cadena()
    status_code = 200 if resultado['valida'] else 409

    return JsonResponse(resultado, status=status_code)


def _construir_respuesta_verificacion(certificado):
    """
    Arma la respuesta de verificación (incluyendo la comprobación
    criptográfica con la prueba de Merkle). La usan tanto la verificación
    por código como la verificación subiendo el PDF directamente, para no
    duplicar la lógica.
    """
    # Verificar si ya fue integrado a un bloque de la blockchain
    if certificado.bloque is None:
        return JsonResponse({
            'autentico': False,
            'mensaje': 'El certificado existe pero aún está en la cola de procesamiento (no minado).'
        }, status=200)

    # Verificamos CRIPTOGRÁFICAMENTE que el certificado realmente
    # pertenece a ese bloque, reconstruyendo la raíz de Merkle desde su
    # hash y su prueba guardada. No nos basta con que la base de datos
    # diga que están relacionados: si alguien edita un registro directo
    # en MySQL, esta verificación lo detecta porque la raíz recalculada
    # ya no coincidiría con la del bloque.
    prueba_valida = verificar_prueba_merkle(
        hash_hoja=certificado.hash_certificado,
        prueba=certificado.merkle_proof,
        raiz_esperada=certificado.bloque.merkle_root
    )

    if not prueba_valida:
        return JsonResponse({
            'autentico': False,
            'mensaje': 'ALERTA: El certificado no coincide con la prueba criptográfica de su bloque. Los datos pudieron haber sido alterados.'
        }, status=409)

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
            'fecha_sellado': certificado.bloque.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'prueba_merkle': certificado.merkle_proof,
            'prueba_verificada': prueba_valida
        }
    }, status=200)


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

        return _construir_respuesta_verificacion(certificado)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Formato JSON inválido.'}, status=400)


@csrf_exempt
def verificar_certificado_pdf(request):
    """
    Endpoint POST (multipart/form-data): recibe directamente el archivo
    PDF del certificado (campo 'certificado_pdf'), calcula su SHA-256
    real y busca si ese hash exacto corresponde a un certificado
    registrado. No hace falta conocer el código_unico: el propio
    documento es la prueba de qué certificado se está verificando.
    Si el PDF fue modificado aunque sea un solo byte, el hash cambia
    por completo y no va a encontrar coincidencia.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido. Use POST.'}, status=405)

    archivo = request.FILES.get('certificado_pdf')
    if not archivo:
        return JsonResponse({
            'error': "Falta el archivo. Envíalo en el campo 'certificado_pdf' (multipart/form-data)."
        }, status=400)

    if archivo.content_type != 'application/pdf':
        return JsonResponse({'error': 'El archivo debe ser un PDF.'}, status=400)

    if archivo.size > MAX_TAMANO_PDF_BYTES:
        return JsonResponse({
            'error': f'El archivo supera el tamaño máximo permitido ({MAX_TAMANO_PDF_BYTES // (1024 * 1024)} MB).'
        }, status=400)

    hash_calculado = calcular_sha256(archivo.read())

    certificado = CertificadoModel.objects.filter(hash_certificado=hash_calculado).first()

    if not certificado:
        return JsonResponse({
            'autentico': False,
            'mensaje': 'El archivo no coincide con ningún certificado registrado. Puede ser un documento distinto, o haber sido modificado.'
        }, status=404)

    return _construir_respuesta_verificacion(certificado)


@csrf_exempt
def registrar_certificado(request):
    """
    Endpoint POST (multipart/form-data): registra un nuevo certificado a
    partir del PDF real. El SHA-256 se calcula sobre los bytes reales del
    archivo (no sobre un string simulado). El PDF se guarda además como
    binario directo en MySQL (campo 'archivo_pdf'), separado del hash:
    el archivo es solo un respaldo del documento original, no participa
    en el árbol de Merkle ni en la blockchain (eso sigue dependiendo
    únicamente de 'hash_certificado').

    Campos esperados (multipart/form-data):
      - codigo_unico
      - nombre_alumno
      - carrera
      - certificado_pdf (archivo)

    El certificado queda pendiente ('bloque' = None) hasta que corra el
    siguiente 'python manage.py minar_bloques'.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido. Use POST.'}, status=405)

    codigo_unico = request.POST.get('codigo_unico')
    nombre_alumno = request.POST.get('nombre_alumno')
    carrera = request.POST.get('carrera')
    archivo = request.FILES.get('certificado_pdf')

    campos_faltantes = [nombre for nombre, valor in [
        ('codigo_unico', codigo_unico),
        ('nombre_alumno', nombre_alumno),
        ('carrera', carrera),
        ('certificado_pdf', archivo),
    ] if not valor]

    if campos_faltantes:
        return JsonResponse({
            'error': f"Faltan campos obligatorios: {', '.join(campos_faltantes)}"
        }, status=400)

    if archivo.content_type != 'application/pdf':
        return JsonResponse({'error': 'El archivo debe ser un PDF.'}, status=400)

    if archivo.size > MAX_TAMANO_PDF_BYTES:
        return JsonResponse({
            'error': f'El archivo supera el tamaño máximo permitido ({MAX_TAMANO_PDF_BYTES // (1024 * 1024)} MB).'
        }, status=400)

    if CertificadoModel.objects.filter(codigo_unico=codigo_unico).exists():
        return JsonResponse({'error': 'Ya existe un certificado registrado con ese codigo_unico.'}, status=409)

    # Leemos el archivo UNA sola vez: un objeto de archivo no se puede
    # leer dos veces (el segundo .read() devolvería vacío). Con esos
    # mismos bytes calculamos el hash Y los guardamos como binario.
    bytes_pdf = archivo.read()
    hash_certificado = calcular_sha256(bytes_pdf)

    if CertificadoModel.objects.filter(hash_certificado=hash_certificado).exists():
        return JsonResponse({'error': 'Este PDF ya fue registrado previamente (hash duplicado).'}, status=409)

    certificado = CertificadoModel.objects.create(
        codigo_unico=codigo_unico,
        nombre_alumno=nombre_alumno,
        carrera=carrera,
        hash_certificado=hash_certificado,
        archivo_pdf=bytes_pdf
    )

    return JsonResponse({
        'mensaje': 'Certificado registrado correctamente. Queda pendiente hasta el próximo minado.',
        'codigo_unico': certificado.codigo_unico,
        'hash_sha256': certificado.hash_certificado
    }, status=201)


def descargar_certificado_pdf(request, codigo_unico):
    """
    Endpoint GET: devuelve el PDF binario guardado en MySQL para un
    certificado, tal como fue subido originalmente.
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido. Use GET.'}, status=405)

    certificado = CertificadoModel.objects.filter(codigo_unico=codigo_unico).first()

    if not certificado or not certificado.archivo_pdf:
        raise Http404("No hay un PDF guardado para ese código de certificado.")

    respuesta = HttpResponse(bytes(certificado.archivo_pdf), content_type='application/pdf')
    respuesta['Content-Disposition'] = f'inline; filename="{certificado.codigo_unico}.pdf"'
    return respuesta