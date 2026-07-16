import functools
from django.http import JsonResponse
from .models import AuthToken


def requiere_autenticacion(vista):
    """
    Decorador para proteger endpoints que solo debe poder usar una
    autoridad universitaria autenticada (Proof of Authority, nivel 1).

    Exige el header:  Authorization: Bearer <token>

    El token se obtiene al hacer login (ver login_view en views.py) y
    debe corresponder a un usuario con is_staff=True.
    """
    @functools.wraps(vista)
    def wrapper(request, *args, **kwargs):
        header_auth = request.META.get('HTTP_AUTHORIZATION', '')

        if not header_auth.startswith('Bearer '):
            return JsonResponse({
                'error': 'Se requiere autenticación. Incluye el header "Authorization: Bearer <token>".'
            }, status=401)

        token_valor = header_auth.split(' ', 1)[1].strip()
        token_obj = AuthToken.objects.select_related('user').filter(token=token_valor).first()

        if not token_obj:
            return JsonResponse({
                'error': 'Token inválido o la sesión ya expiró. Inicia sesión de nuevo.'
            }, status=401)

        if not token_obj.user.is_staff:
            return JsonResponse({
                'error': 'Este usuario no tiene permisos de autoridad universitaria.'
            }, status=403)

        # Dejamos el usuario disponible por si la vista lo necesita
        request.usuario_autenticado = token_obj.user
        return vista(request, *args, **kwargs)

    return wrapper
