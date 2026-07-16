from django.contrib import admin
from .models import BloqueModel, CertificadoModel, AuthToken, AutoridadClave


@admin.register(BloqueModel)
class BloqueAdmin(admin.ModelAdmin):
    list_display = ('index', 'timestamp', 'firmante', 'firmado', 'merkle_root', 'previous_hash', 'block_hash', 'total_certificados')
    ordering = ('index',)
    search_fields = ('block_hash', 'previous_hash', 'merkle_root')
    readonly_fields = ('index', 'timestamp', 'merkle_root', 'previous_hash', 'block_hash', 'firmante', 'firma_digital')

    def total_certificados(self, obj):
        return obj.certificados.count()
    total_certificados.short_description = 'Certificados en el bloque'

    def firmado(self, obj):
        return bool(obj.firma_digital)
    firmado.boolean = True
    firmado.short_description = 'Firmado'


@admin.register(CertificadoModel)
class CertificadoAdmin(admin.ModelAdmin):
    list_display = ('codigo_unico', 'nombre_alumno', 'carrera', 'bloque', 'fecha_registro')
    list_filter = ('carrera', 'bloque')
    search_fields = ('codigo_unico', 'nombre_alumno', 'hash_certificado')
    ordering = ('-fecha_registro',)
    readonly_fields = ('hash_certificado', 'merkle_proof', 'fecha_registro')


@admin.register(AuthToken)
class AuthTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'creado', 'token_corto')
    readonly_fields = ('user', 'token', 'creado')
    search_fields = ('user__username',)

    def token_corto(self, obj):
        return f"{obj.token[:12]}..."
    token_corto.short_description = 'Token (parcial)'

    def has_add_permission(self, request):
        # Los tokens solo se crean vía /api/login/, no a mano desde el admin
        return False


@admin.register(AutoridadClave)
class AutoridadClaveAdmin(admin.ModelAdmin):
    # IMPORTANTE: 'fields' aquí lista explícitamente qué se muestra.
    # llave_privada_pem NUNCA aparece, ni siquiera como solo lectura,
    # para que jamás sea visible desde el admin.
    list_display = ('user', 'creado')
    fields = ('user', 'creado', 'llave_publica_corta')
    readonly_fields = ('user', 'creado', 'llave_publica_corta')
    search_fields = ('user__username',)

    def llave_publica_corta(self, obj):
        return obj.llave_publica_pem[:60] + '...'
    llave_publica_corta.short_description = 'Llave pública (extracto)'

    def has_add_permission(self, request):
        # Las llaves solo se generan automáticamente al minar, no a mano
        return False
