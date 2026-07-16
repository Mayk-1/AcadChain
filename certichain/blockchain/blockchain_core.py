import hashlib
from typing import List, Union
from django.contrib.auth.models import User
from .models import BloqueModel, CertificadoModel, AutoridadClave
from . import firma as firma_digital

def calcular_sha256(datos: Union[str, bytes]) -> str:
    """Calcula el hash SHA-256 de una cadena de texto o para archivos pdf."""

    # Si la entrada es un string (texto), lo codificamos a bytes
    if isinstance(datos, str):
        datos = datos.encode('utf-8')
    
    # Calculamos el hash sobre los bytes
    return hashlib.sha256(datos).hexdigest()

# ==========================================
# ALGORITMO: ÁRBOL DE MERKLE
# ==========================================
class MerkleTree:
    def __init__(self, lista_hashes: List[str]):
        """
        Recibe una lista con los hashes SHA-256 de los certificados.
        Si la lista está vacía, genera un hash por defecto.

        Además de calcular la raíz (self.root), construye la "prueba de
        Merkle" (self.proofs) de cada hoja: la lista mínima de hashes
        hermanos que hace falta para reconstruir la raíz partiendo solo
        de esa hoja, sin necesitar el resto de certificados del bloque.
        """
        if not lista_hashes:
            self.root = calcular_sha256("Bloque Vacio")
            self.proofs = []
            return

        self.hojas = list(lista_hashes)
        # Guardamos cada nivel del árbol (hojas -> ... -> raíz) para
        # poder reconstruir después el camino de cada hoja.
        self.niveles = [self.hojas]
        self.root = self._construir_arbol(list(lista_hashes))
        self.proofs = self._generar_pruebas()

    def _construir_arbol(self, nodos: List[str]) -> str:
        # Caso base: cuando solo queda un nodo, esa es la Raíz de Merkle (Merkle Root)
        if len(nodos) == 1:
            return nodos[0]
        
        nuevo_nivel = []
        
        # Iteramos de 2 en 2 para emparejar los nodos
        for i in range(0, len(nodos), 2):
            nodo_izquierdo = nodos[i]
            
            # Si el número de nodos es impar, duplicamos el último nodo para balancear el árbol
            if i + 1 < len(nodos):
                nodo_derecho = nodos[i+1]
            else:
                nodo_derecho = nodos[i]
            
            # Combinamos ambos hashes y calculamos el hash del padre
            hash_padre = calcular_sha256(nodo_izquierdo + nodo_derecho)
            nuevo_nivel.append(hash_padre)

        self.niveles.append(nuevo_nivel)
        # Llamada recursiva para procesar el siguiente nivel hacia arriba
        return self._construir_arbol(nuevo_nivel)

    def _generar_pruebas(self) -> List[List[dict]]:
        """
        Para cada hoja original, arma la lista de "hermanos" que hacen
        falta para recalcular la raíz subiendo nivel por nivel.
        Cada paso indica el hash del hermano y si va a la izquierda o
        a la derecha al concatenar (el orden importa para SHA-256).
        """
        total_hojas = len(self.hojas)
        pruebas = [[] for _ in range(total_hojas)]
        # posicion_actual[i] = índice de la hoja i dentro del nivel actual
        posicion_actual = list(range(total_hojas))

        # Recorremos todos los niveles menos el último (la raíz no tiene hermano)
        for nivel in self.niveles[:-1]:
            nuevas_posiciones = []
            for hoja_idx, pos in enumerate(posicion_actual):
                es_posicion_par = pos % 2 == 0
                idx_hermano = pos + 1 if es_posicion_par else pos - 1

                if idx_hermano < len(nivel):
                    hash_hermano = nivel[idx_hermano]
                else:
                    # Caso de nodo impar duplicado (ver _construir_arbol)
                    hash_hermano = nivel[pos]

                pruebas[hoja_idx].append({
                    'hash': hash_hermano,
                    # Si mi posición es par, mi hermano queda a mi derecha
                    'posicion': 'derecha' if es_posicion_par else 'izquierda'
                })
                nuevas_posiciones.append(pos // 2)

            posicion_actual = nuevas_posiciones

        return pruebas


def verificar_prueba_merkle(hash_hoja: str, prueba: List[dict], raiz_esperada: str) -> bool:
    """
    Reconstruye la raíz de Merkle subiendo desde una única hoja usando
    su prueba (lista de hermanos), y confirma que coincide con la raíz
    guardada en el bloque. Esto es lo que realmente demuestra que un
    certificado pertenece a ese bloque, sin tener que consultar ni
    confiar en los demás certificados del lote.
    """
    hash_actual = hash_hoja

    for paso in prueba:
        hash_hermano = paso.get('hash', '')
        if paso.get('posicion') == 'derecha':
            hash_actual = calcular_sha256(hash_actual + hash_hermano)
        else:
            hash_actual = calcular_sha256(hash_hermano + hash_actual)

    return hash_actual == raiz_esperada

def validar_cadena() -> dict:
    """
    Recorre toda la blockchain (de génesis hacia adelante) y confirma
    que sigue siendo una cadena válida e inmutable:

    1. El block_hash de cada bloque coincide con el que se obtiene al
       recalcularlo desde su propio contenido (index + merkle_root +
       previous_hash). Si alguien editó el merkle_root de un bloque
       directo en MySQL, esto lo detecta.
    2. El previous_hash de cada bloque coincide exactamente con el
       block_hash del bloque anterior. Si alguien borró, insertó o
       reordenó un bloque, el eslabón se rompe y esto lo detecta.
    3. Si el bloque tiene firma digital (Proof of Authority, nivel 2),
       confirma que la firma corresponde efectivamente al block_hash y
       a la llave pública de quien aparece como firmante. Si alguien
       cambiara el 'firmante' de un bloque directo en MySQL (para
       adjudicarle el sello a otra autoridad), esto lo detecta: la
       firma solo es válida con la llave privada original.

    Es una verificación rápida: O(número de bloques), no recalcula
    los Merkle roots desde los certificados (para eso existe una
    auditoría más profunda y más costosa, aparte).
    """
    bloques = list(BloqueModel.objects.select_related('firmante').order_by('index'))
    errores = []
    detalle_bloques = []

    if not bloques:
        return {'valida': True, 'bloques_verificados': 0, 'errores': [], 'bloques': []}

    bloque_anterior = None
    for bloque in bloques:
        # 1. Recalcular el hash propio del bloque y compararlo
        string_contenido = f"{bloque.index}{bloque.merkle_root}{bloque.previous_hash}"
        hash_recalculado = calcular_sha256(string_contenido)

        if hash_recalculado != bloque.block_hash:
            errores.append({
                'bloque_index': bloque.index,
                'tipo': 'block_hash_no_coincide',
                'detalle': 'El hash guardado del bloque no corresponde a su contenido actual (merkle_root, index o previous_hash pudieron ser alterados).'
            })

        # 2. Confirmar el eslabón con el bloque anterior
        if bloque_anterior is None:
            # Debe ser el génesis
            if bloque.index != 0 or bloque.previous_hash != "0" * 64:
                errores.append({
                    'bloque_index': bloque.index,
                    'tipo': 'genesis_invalido',
                    'detalle': 'El primer bloque de la cadena no es un génesis válido.'
                })
        else:
            if bloque.previous_hash != bloque_anterior.block_hash:
                errores.append({
                    'bloque_index': bloque.index,
                    'tipo': 'eslabon_roto',
                    'detalle': f'El previous_hash del bloque {bloque.index} no coincide con el block_hash del bloque {bloque_anterior.index}.'
                })
            if bloque.index != bloque_anterior.index + 1:
                errores.append({
                    'bloque_index': bloque.index,
                    'tipo': 'indice_no_consecutivo',
                    'detalle': f'Se esperaba el índice {bloque_anterior.index + 1} y se encontró {bloque.index}.'
                })

        # 3. Verificar la firma digital (Proof of Authority), si existe
        firma_valida = None  # None = bloque sin firma (no aplica, no es error)
        if bloque.firmante and bloque.firma_digital:
            clave = AutoridadClave.objects.filter(user=bloque.firmante).first()
            if not clave:
                firma_valida = False
                errores.append({
                    'bloque_index': bloque.index,
                    'tipo': 'llave_publica_no_encontrada',
                    'detalle': f'El bloque dice estar firmado por "{bloque.firmante.username}", pero no se encontró su llave pública registrada.'
                })
            else:
                firma_valida = firma_digital.verificar_firma(
                    clave.llave_publica_pem, bloque.block_hash, bloque.firma_digital
                )
                if not firma_valida:
                    errores.append({
                        'bloque_index': bloque.index,
                        'tipo': 'firma_invalida',
                        'detalle': f'La firma digital del bloque no corresponde a la llave pública de "{bloque.firmante.username}". El firmante pudo haber sido alterado.'
                    })

        detalle_bloques.append({
            'index': bloque.index,
            'firmante': bloque.firmante.username if bloque.firmante else None,
            'firma_valida': firma_valida
        })

        bloque_anterior = bloque

    return {
        'valida': len(errores) == 0,
        'bloques_verificados': len(bloques),
        'errores': errores,
        'bloques': detalle_bloques
    }


def obtener_o_crear_genesis() -> BloqueModel:
    """Garantiza la existencia del Bloque 0 en la base de datos MySQL."""
    # Buscamos si ya existe el bloque 0
    genesis = BloqueModel.objects.filter(index=0).first()
    
    if not genesis:
        # Si no existe, lo creamos con valores por defecto
        root_genesis = calcular_sha256("Genesis Root Certichain")
        prev_hash_genesis = "0" * 64
        
        # El hash del propio bloque combina sus datos
        string_bloque = f"0{root_genesis}{prev_hash_genesis}"
        hash_bloque = calcular_sha256(string_bloque)
        
        genesis = BloqueModel.objects.create(
            index=0,
            merkle_root=root_genesis,
            previous_hash=prev_hash_genesis,
            block_hash=hash_bloque
        )
    return genesis


def obtener_o_crear_llaves(usuario: User) -> AutoridadClave:
    """
    Devuelve el par de llaves RSA de una autoridad, generándolo la
    primera vez que esa autoridad mina un bloque. Las llaves persisten
    en la base de datos para que se puedan reutilizar en futuros
    minados y para que validar_cadena() pueda verificar firmas de
    bloques ya sellados en el pasado.
    """
    autoridad_clave = AutoridadClave.objects.filter(user=usuario).first()
    if autoridad_clave:
        return autoridad_clave

    pem_privada, pem_publica = firma_digital.generar_par_llaves()
    return AutoridadClave.objects.create(
        user=usuario,
        llave_privada_pem=pem_privada,
        llave_publica_pem=pem_publica
    )


def ejecutar_minado(tamano_lote: int = 1000, usuario: User = None) -> dict:
    """
    Agrupa los certificados pendientes (bloque=None) en bloques nuevos,
    de a lo más 'tamano_lote' por bloque. Es la misma lógica que usa el
    comando de terminal 'python manage.py minar_bloques', extraída aquí
    para que también la pueda llamar el endpoint de la API (ambos deben
    comportarse exactamente igual, así que no se duplica el código).

    Si se pasa 'usuario' (una autoridad autenticada, is_staff=True),
    cada bloque nuevo queda firmado digitalmente con la llave privada
    de esa autoridad (Proof of Authority, nivel 2). Si no se pasa
    ningún usuario, el bloque se crea sin firma (firmante=None).
    """
    obtener_o_crear_genesis()

    certificados_pendientes = CertificadoModel.objects.filter(bloque__isnull=True).order_by('id')
    total_pendientes = certificados_pendientes.count()

    if total_pendientes == 0:
        return {'bloques_creados': 0, 'certificados_procesados': 0, 'bloques': []}

    autoridad_clave = obtener_o_crear_llaves(usuario) if usuario else None

    lista_certificados = list(certificados_pendientes)
    bloques_creados = []

    for i in range(0, len(lista_certificados), tamano_lote):
        lote_actual = lista_certificados[i:i + tamano_lote]
        lista_hashes = [cert.hash_certificado for cert in lote_actual]

        arbol_merkle = MerkleTree(lista_hashes)
        merkle_root_actual = arbol_merkle.root

        ultimo_bloque = BloqueModel.objects.order_by('-index').first()
        nuevo_index = ultimo_bloque.index + 1
        previous_hash = ultimo_bloque.block_hash

        string_contenido_bloque = f"{nuevo_index}{merkle_root_actual}{previous_hash}"
        hash_bloque_actual = calcular_sha256(string_contenido_bloque)

        firma_bloque = None
        if autoridad_clave:
            firma_bloque = firma_digital.firmar(autoridad_clave.llave_privada_pem, hash_bloque_actual)

        nuevo_bloque = BloqueModel.objects.create(
            index=nuevo_index,
            merkle_root=merkle_root_actual,
            previous_hash=previous_hash,
            block_hash=hash_bloque_actual,
            firmante=usuario,
            firma_digital=firma_bloque
        )

        for cert, prueba_cert in zip(lote_actual, arbol_merkle.proofs):
            cert.bloque = nuevo_bloque
            cert.merkle_proof = prueba_cert

        CertificadoModel.objects.bulk_update(lote_actual, ['bloque', 'merkle_proof'])

        bloques_creados.append({
            'index': nuevo_index,
            'block_hash': hash_bloque_actual,
            'total_certificados': len(lote_actual),
            'firmante': usuario.username if usuario else None
        })

    return {
        'bloques_creados': len(bloques_creados),
        'certificados_procesados': len(lista_certificados),
        'bloques': bloques_creados
    }