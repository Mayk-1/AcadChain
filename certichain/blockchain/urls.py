# blockchain/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('api/blockchain/', views.listar_blockchain, name='listar_blockchain'),
    path('api/verificar/', views.verificar_certificado, name='verificar_certificado'),
    path('api/validar-cadena/', views.validar_integridad_cadena, name='validar_integridad_cadena'),
]