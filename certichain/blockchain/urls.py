# blockchain/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('api/blockchain/', views.listar_blockchain, name='listar_blockchain'),
    path('api/verificar/', views.verificar_certificado, name='verificar_certificado'),
    path('api/verificar-pdf/', views.verificar_certificado_pdf, name='verificar_certificado_pdf'),
    path('api/registrar-certificado/', views.registrar_certificado, name='registrar_certificado'),
    path('api/certificado/<str:codigo_unico>/pdf/', views.descargar_certificado_pdf, name='descargar_certificado_pdf'),
    path('api/validar-cadena/', views.validar_integridad_cadena, name='validar_integridad_cadena'),
    path('api/login/', views.login_view, name='login_view'),
    path('api/logout/', views.logout_view, name='logout_view'),
    path('api/minar/', views.minar_bloques_view, name='minar_bloques_view'),
]