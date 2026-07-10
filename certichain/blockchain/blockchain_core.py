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
        """
        if not lista_hashes:
            self.root = calcular_sha256("Bloque Vacio")
            return

        self.root = self._construir_arbol(lista_hashes)

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
            nuevo_level = nuevo_nivel.append(hash_padre)
            
        # Llamada recursiva para procesar el siguiente nivel hacia arriba
        return self._construir_arbol(nuevo_nivel)

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