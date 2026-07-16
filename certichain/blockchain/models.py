from django.db import models
from django.contrib.auth.models import User

class BloqueModel(models.Model):
    """
    Representa un nodo dentro de la Lista Enlazada (Blockchain).
    """
    index = models.IntegerField(unique=True, verbose_name="Número de Bloque")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    merkle_root = models.CharField(max_length=64, verbose_name="Raíz de Merkle")
    previous_hash = models.CharField(max_length=64, verbose_name="Hash del Bloque Anterior")
    block_hash = models.CharField(max_length=64, unique=True, verbose_name="Hash del Bloque Actual")

    # Proof of Authority (nivel 2): qué autoridad selló este bloque, y su
    # firma digital sobre el block_hash. Quedan en null para bloques
    # minados sin una autoridad autenticada de por medio (por ejemplo,
    # desde la terminal sin el flag --usuario). Un bloque sin firma no
    # es necesariamente inválido, pero validar_cadena() sí distingue
    # bloques firmados de los que no lo están.
    firmante = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bloques_firmados",
        verbose_name="Autoridad que selló el bloque"
    )
    firma_digital = models.TextField(null=True, blank=True, editable=False, verbose_name="Firma digital (base64)")

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

    # El PDF real del certificado, guardado como binario directo en la
    # fila de MySQL (columna LONGBLOB). Es un dato aparte del hash: no
    # participa en el árbol de Merkle ni en la blockchain, solo se
    # conserva como respaldo del documento original. editable=False
    # porque no tiene sentido editarlo desde el admin de Django.
    archivo_pdf = models.BinaryField(null=True, blank=True, editable=False, verbose_name="Archivo PDF (binario)")
    
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


class AuthToken(models.Model):
    """
    Token simple de autenticación (Proof of Authority, nivel 1): representa
    una sesión activa de un usuario autorizado (is_staff=True). Se genera
    al hacer login y se exige en el header 'Authorization: Bearer <token>'
    para las operaciones sensibles (registrar certificados, minar bloques).

    Es OneToOne a propósito: cada login nuevo reemplaza el token anterior,
    así que solo puede haber una sesión activa por usuario a la vez.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="auth_token")
    token = models.CharField(max_length=64, unique=True)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Token de {self.user.username} (creado {self.creado:%Y-%m-%d %H:%M})"


class AutoridadClave(models.Model):
    """
    Proof of Authority (nivel 2): par de llaves RSA de una autoridad
    (un usuario is_staff). La llave privada se usa para firmar los
    bloques que esa autoridad mina; la pública sirve para que cualquiera
    (incluida validar_cadena) pueda comprobar esa firma después.

    La llave privada NUNCA se expone por ningún endpoint ni se muestra
    en el admin de Django (ver AutoridadClaveAdmin) — es la única razón
    de ser de este modelo separado, en vez de guardarlo en AuthToken.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="autoridad_clave")
    llave_privada_pem = models.TextField(editable=False)
    llave_publica_pem = models.TextField(editable=False)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Llaves de {self.user.username}"