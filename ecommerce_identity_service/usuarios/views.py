from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from drf_spectacular.utils import OpenApiExample, extend_schema

from identity_service.api_response import success_response
from .serializers import (
    ErrorResponseSerializer,
    LoginSuccessResponseSerializer,
    PerfilSuccessResponseSerializer,
    RegistroSuccessResponseSerializer,
    PerfilSerializer,
    RegistroSerializer,
    TokenObtainAccessSerializer,
)

Usuario = get_user_model()

_EJ_CORREO = 'maria.lopez@gmail.com'
_EJ_PASSWORD = 'ClaveSegura1'
_EJ_DIRECCION = {
    'calle': 'Av. Universidad',
    'numero_exterior': '100',
    'numero_interior': 'B',
    'colonia': 'Centro',
    'ciudad': 'Puebla',
    'estado': 'Puebla',
    'codigo_postal': '72000',
    'pais': 'MX',
}
_EJ_TIMESTAMP = '2026-04-11T20:15:30Z'


@extend_schema(
    responses={
        201: RegistroSuccessResponseSerializer,
        400: ErrorResponseSerializer,
    },
    examples=[
        OpenApiExample(
            'Solicitud — alta de cuenta',
            summary='Cuerpo típico para registrarse',
            value={
                'nombre': 'María',
                'apellido': 'López',
                'correo': _EJ_CORREO,
                'password': _EJ_PASSWORD,
                **_EJ_DIRECCION,
            },
            request_only=True,
        ),
        OpenApiExample(
            'Respuesta — usuario creado',
            summary='201 con envelope de éxito',
            value={
                'success': True,
                'message': 'Usuario creado correctamente.',
                'data': {
                    'id': 42,
                    'nombre': 'María',
                    'apellido': 'López',
                    'correo': _EJ_CORREO,
                    'calle': _EJ_DIRECCION['calle'],
                    'numero_exterior': _EJ_DIRECCION['numero_exterior'],
                    'numero_interior': _EJ_DIRECCION['numero_interior'],
                    'colonia': _EJ_DIRECCION['colonia'],
                    'ciudad': _EJ_DIRECCION['ciudad'],
                    'estado': _EJ_DIRECCION['estado'],
                    'codigo_postal': _EJ_DIRECCION['codigo_postal'],
                    'pais': _EJ_DIRECCION['pais'],
                },
                'timestamp': _EJ_TIMESTAMP,
            },
            response_only=True,
            status_codes=['201'],
        ),
        OpenApiExample(
            'Error — validación de campos',
            summary='400 con envelope de error',
            value={
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Los datos enviados no son válidos.',
                    'details': {'correo': ['Este campo es obligatorio.']},
                },
                'timestamp': _EJ_TIMESTAMP,
            },
            response_only=True,
            status_codes=['400'],
        ),
    ],
)
class RegistroView(generics.CreateAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    queryset = Usuario.objects.all()
    serializer_class = RegistroSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return success_response(
            message='Usuario creado correctamente.',
            data=serializer.data,
            status_code=status.HTTP_201_CREATED,
        )


@extend_schema(
    description=(
        'Credenciales (`correo` y `password`). Devuelve solo un JWT de acceso y el id de usuario.'
    ),
    responses={
        200: LoginSuccessResponseSerializer,
        400: ErrorResponseSerializer,
        401: ErrorResponseSerializer,
    },
    examples=[
        OpenApiExample(
            'Solicitud — login',
            summary='Correo y contraseña',
            value={'correo': _EJ_CORREO, 'password': _EJ_PASSWORD},
            request_only=True,
        ),
        OpenApiExample(
            'Respuesta — tokens',
            summary='200 con envelope de éxito',
            value={
                'success': True,
                'message': 'Autenticación exitosa.',
                'data': {
                    'access': (
                        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIn0.'
                        'ejemplo_firma_no_valida'
                    ),
                    'usuario_id': 42,
                },
                'timestamp': _EJ_TIMESTAMP,
            },
            response_only=True,
            status_codes=['200'],
        ),
        OpenApiExample(
            'Error — validación de campos',
            summary='400 con envelope de error',
            value={
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Los datos enviados no son válidos.',
                    'details': {'password': ['Este campo es requerido.']},
                },
                'timestamp': _EJ_TIMESTAMP,
            },
            response_only=True,
            status_codes=['400'],
        ),
        OpenApiExample(
            'Error — credenciales inválidas',
            summary='401 con envelope de error',
            value={
                'success': False,
                'error': {
                    'code': 'INVALID_CREDENTIALS',
                    'message': 'Correo o contraseña inválidos.',
                },
                'timestamp': _EJ_TIMESTAMP,
            },
            response_only=True,
            status_codes=['401'],
        ),
    ],
)
class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = TokenObtainAccessSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as exc:
            raise InvalidToken(exc.args[0]) from exc

        return success_response(
            message='Autenticación exitosa.',
            data=serializer.validated_data,
        )


@extend_schema(
    responses={
        200: PerfilSuccessResponseSerializer,
        401: ErrorResponseSerializer,
        404: ErrorResponseSerializer,
    },
    examples=[
        OpenApiExample(
            'Respuesta — perfil con dirección',
            summary='Mismo usuario de ejemplo que en registro/login',
            value={
                'success': True,
                'message': 'Perfil obtenido correctamente.',
                'data': {
                    'id': 42,
                    'nombre': 'María',
                    'apellido': 'López',
                    'correo': _EJ_CORREO,
                    'direccion_envio': _EJ_DIRECCION,
                },
                'timestamp': _EJ_TIMESTAMP,
            },
            response_only=True,
            status_codes=['200'],
        ),
        OpenApiExample(
            'Error — usuario no encontrado',
            summary='404 con envelope de error',
            value={
                'success': False,
                'error': {
                    'code': 'USER_NOT_FOUND',
                    'message': 'Usuario no encontrado.',
                },
                'timestamp': _EJ_TIMESTAMP,
            },
            response_only=True,
            status_codes=['404'],
        ),
        OpenApiExample(
            'Error — sin autenticación',
            summary='401 con envelope de error',
            value={
                'success': False,
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Debes autenticarte con un token válido.',
                },
                'timestamp': _EJ_TIMESTAMP,
            },
            response_only=True,
            status_codes=['401'],
        ),
    ],
)
class PerfilView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Usuario.objects.all()
    serializer_class = PerfilSerializer
    lookup_url_kwarg = 'id'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(
            message='Perfil obtenido correctamente.',
            data=serializer.data,
        )
