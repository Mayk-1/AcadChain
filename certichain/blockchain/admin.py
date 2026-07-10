from django.contrib import admin
from .models import BloqueModel, CertificadoModel


@admin.register(BloqueModel)
class BloqueAdmin(admin.ModelAdmin):
    list_display = ('index', 'timestamp', 'merkle_root', 'previous_hash', 'block_hash', 'total_certificados')
    ordering = ('index',)
    search_fields = ('block_hash', 'previous_hash', 'merkle_root')
    readonly_fields = ('index', 'timestamp', 'merkle_root', 'previous_hash', 'block_hash')

    def total_certificados(self, obj):
        return obj.certificados.count()
    total_certificados.short_description = 'Certificados en el bloque'


@admin.register(CertificadoModel)
class CertificadoAdmin(admin.ModelAdmin):
    list_display = ('codigo_unico', 'nombre_alumno', 'carrera', 'bloque', 'fecha_registro')
    list_filter = ('carrera', 'bloque')
    search_fields = ('codigo_unico', 'nombre_alumno', 'hash_certificado')
    ordering = ('-fecha_registro',)
    readonly_fields = ('hash_certificado', 'merkle_proof', 'fecha_registro')