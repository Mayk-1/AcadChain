import hashlib
from typing import List, Union
from .models import BloqueModel

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

    Es una verificación rápida: O(número de bloques), no recalcula
    los Merkle roots desde los certificados (para eso existe una
    auditoría más profunda y más costosa, aparte).
    """
    bloques = list(BloqueModel.objects.order_by('index'))
    errores = []

    if not bloques:
        return {'valida': True, 'bloques_verificados': 0, 'errores': []}

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

        bloque_anterior = bloque

    return {
        'valida': len(errores) == 0,
        'bloques_verificados': len(bloques),
        'errores': errores
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