from rest_framework import status
from rest_framework.exceptions import (
    AuthenticationFailed,
    MethodNotAllowed,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    ValidationError,
)
from rest_framework.views import exception_handler
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from .api_response import error_response


def _message_from_data(data, fallback: str) -> str:
    if isinstance(data, dict):
        detail = data.get('detail')
        if isinstance(detail, str):
            return detail
        first_value = next(iter(data.values()), None)
        if isinstance(first_value, list) and first_value:
            return str(first_value[0])
        if isinstance(first_value, str):
            return first_value
    if isinstance(data, list) and data:
        return str(data[0])
    return fallback


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        return error_response(
            code='INTERNAL_ERROR',
            message='Ocurrió un error interno en el servidor.',
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    request = context.get('request')
    is_profile_endpoint = bool(request and '/profile/' in request.path)

    if isinstance(exc, ValidationError):
        return error_response(
            code='VALIDATION_ERROR',
            message='Los datos enviados no son válidos.',
            details=response.data,
            status_code=response.status_code,
        )

    if isinstance(exc, AuthenticationFailed):
        return error_response(
            code='INVALID_CREDENTIALS',
            message='Correo o contraseña inválidos.',
            status_code=response.status_code,
        )

    if isinstance(exc, (NotAuthenticated, InvalidToken, TokenError)):
        return error_response(
            code='UNAUTHORIZED',
            message='Debes autenticarte con un token válido.',
            status_code=response.status_code,
        )

    if isinstance(exc, PermissionDenied):
        return error_response(
            code='FORBIDDEN',
            message='No tienes permisos para realizar esta acción.',
            status_code=response.status_code,
        )

    if isinstance(exc, NotFound):
        return error_response(
            code='USER_NOT_FOUND' if is_profile_endpoint else 'NOT_FOUND',
            message='Usuario no encontrado.' if is_profile_endpoint else 'Recurso no encontrado.',
            status_code=response.status_code,
        )

    if isinstance(exc, MethodNotAllowed):
        return error_response(
            code='METHOD_NOT_ALLOWED',
            message='Método HTTP no permitido para este endpoint.',
            status_code=response.status_code,
        )

    return error_response(
        code='API_ERROR',
        message=_message_from_data(response.data, 'Error en la solicitud.'),
        details=response.data if isinstance(response.data, (dict, list)) else None,
        status_code=response.status_code,
    )
