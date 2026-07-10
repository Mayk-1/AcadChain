from django.db import models

class BloqueModel(models.Model):
    """
    Representa un nodo dentro de la Lista Enlazada (Blockchain).
    """
    index = models.IntegerField(unique=True, verbose_name="Número de Bloque")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    merkle_root = models.CharField(max_length=64, verbose_name="Raíz de Merkle")
    previous_hash = models.CharField(max_length=64, verbose_name="Hash del Bloque Anterior")
    block_hash = models.CharField(max_length=64, unique=True, verbose_name="Hash del Bloque Actual")

    def __str__(self):
        return f"Bloque #{self.index} - Hash: {self.block_hash[:10]}..."


class CertificadoModel(models.Model):
    """
    Representa las hojas que forman el Árbol de Merkle.
    """
    codigo_unico = models.CharField(max_length=50, unique=True, verbose_name="Código del Certificado")
    nombre_alumno = models.CharField(max_length=150, verbose_name="Nombre del Alumno")
    carrera = models.CharField(max_length=100, verbose_name="Carrera Universitaria")
    hash_certificado = models.CharField(max_length=64, unique=True, verbose_name="SHA-256 del Certificado")
    fecha_registro = models.DateTimeField(auto_now_add=True)

    # Prueba de Merkle (lista de hashes hermanos + posición) generada al
    # momento de minar el bloque. Permite verificar criptográficamente
    # que este certificado pertenece al bloque, sin tener que confiar
    # ciegamente en la relación de base de datos ni recorrer los demás
    # certificados del lote.
    merkle_proof = models.JSONField(default=list, blank=True, verbose_name="Prueba de Merkle")
    
    # Relación: Un bloque puede tener muchos certificados (Árbol de Merkle).
    # null=True permite que el certificado se suba y quede "pendiente" hasta que se genere un bloque.
    bloque = models.ForeignKey(
        BloqueModel, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="certificados"
    )

    def __str__(self):
        return f"{self.codigo_unico} - {self.nombre_alumno}"