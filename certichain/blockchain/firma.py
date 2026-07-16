import base64

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization


def generar_par_llaves():
    """
    Genera un par de llaves RSA-2048 nuevo. Devuelve (llave_privada_pem,
    llave_publica_pem), ambas como texto (formato PEM), listas para
    guardarse en la base de datos.
    """
    llave_privada = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    llave_publica = llave_privada.public_key()

    pem_privada = llave_privada.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')

    pem_publica = llave_publica.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')

    return pem_privada, pem_publica


def firmar(pem_privada: str, mensaje: str) -> str:
    """
    Firma 'mensaje' (normalmente el block_hash) con la llave privada de
    una autoridad. Devuelve la firma codificada en base64, lista para
    guardarse como texto en MySQL.
    """
    llave_privada = serialization.load_pem_private_key(pem_privada.encode('utf-8'), password=None)

    firma_bytes = llave_privada.sign(
        mensaje.encode('utf-8'),
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256()
    )

    return base64.b64encode(firma_bytes).decode('utf-8')


def verificar_firma(pem_publica: str, mensaje: str, firma_b64: str) -> bool:
    """
    Verifica que 'firma_b64' corresponde efectivamente a 'mensaje',
    usando la llave pública de la autoridad que supuestamente firmó.
    Devuelve False ante cualquier fallo (firma inválida, formato
    corrupto, llave incorrecta, etc.) en vez de lanzar una excepción,
    para que se pueda usar directo en validaciones.
    """
    try:
        llave_publica = serialization.load_pem_public_key(pem_publica.encode('utf-8'))
        firma_bytes = base64.b64decode(firma_b64)

        llave_publica.verify(
            firma_bytes,
            mensaje.encode('utf-8'),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False
