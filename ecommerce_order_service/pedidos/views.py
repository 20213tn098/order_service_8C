from django.conf import settings as django_settings
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.response import Response
import requests

from order_service.api_response import success_response, error_response

from .models import Pedido
from .serializers import PedidoSerializer, PedidoCreateSerializer

_EJ_TIMESTAMP = '2026-04-11T20:15:30Z'

# URLs de los otros servicios — configuradas en settings.py / .env
IDENTITY_SERVICE_URL = getattr(django_settings, 'IDENTITY_SERVICE_URL', 'http://localhost:8001')
PRODUCT_SERVICE_URL  = getattr(django_settings, 'PRODUCT_SERVICE_URL',  'http://localhost:8002')


@extend_schema(
    request=PedidoCreateSerializer,
    responses={201: PedidoSerializer},
    examples=[
        OpenApiExample(
            'Solicitud - crear pedido',
            summary='Crear un pedido con lista de productos',
            value={
                'usuario_id': 42,
                'productos': [
                    {'producto_id': 7,  'cantidad': 2, 'precio_unitario': '199.00'},
                    {'producto_id': 15, 'cantidad': 1, 'precio_unitario': '799.00'},
                ],
            },
            request_only=True,
        ),
        OpenApiExample(
            'Respuesta - pedido creado',
            summary='Pedido creado exitosamente',
            value={
                'success': True,
                'message': 'Pedido creado correctamente.',
                'data': {
                    'id': 101,
                    'usuario_id': 42,
                    'estado': 'PENDIENTE',
                    'productos': [
                        {'producto_id': 7,  'cantidad': 2, 'precio_unitario': '199.00'},
                        {'producto_id': 15, 'cantidad': 1, 'precio_unitario': '799.00'},
                    ],
                    'created_at': '2026-04-11T20:15:30Z',
                    'updated_at': '2026-04-11T20:15:30Z',
                },
                'timestamp': _EJ_TIMESTAMP,
            },
            response_only=True,
            status_codes=['201'],
        ),
    ],
)
class PedidoCreateView(generics.CreateAPIView):
    # AllowAny porque la autenticacion la valida el Equipo 1 (Identity Service).
    # Este servicio no comparte la secret key JWT con ellos.
    permission_classes = [AllowAny]
    serializer_class = PedidoCreateSerializer

    def create(self, request, *args, **kwargs):
        usuario_id = request.data.get('usuario_id')
        if not usuario_id:
            return error_response(
                code='VALIDATION_ERROR',
                message='El campo usuario_id es requerido.',
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # 1. Validar que el usuario exista en el Identity Service (Equipo 1)
        try:
            auth_header = request.headers.get('Authorization', '')
            identity_url = f'{IDENTITY_SERVICE_URL}/api/users/{usuario_id}/profile/'
            resp = requests.get(
                identity_url,
                headers={'Authorization': auth_header},
                timeout=10,
            )
            if resp.status_code != 200:
                return error_response(
                    code='USER_NOT_FOUND',
                    message=f'Usuario {usuario_id} no valido o no encontrado en Identity Service.',
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
        except requests.RequestException:
            return error_response(
                code='SERVICE_UNAVAILABLE',
                message='No se pudo conectar con Identity Service. Intenta mas tarde.',
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # 2. Validar stock y precios en el Product Service (Equipo 2)
        productos = request.data.get('productos', [])
        if not productos:
            return error_response(
                code='VALIDATION_ERROR',
                message='Debe proporcionar al menos un producto.',
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        for producto in productos:
            producto_id     = producto.get('producto_id')
            cantidad        = producto.get('cantidad')
            precio_unitario = producto.get('precio_unitario')

            try:
                product_url = f'{PRODUCT_SERVICE_URL}/api/products/{producto_id}/'
                resp = requests.get(product_url, timeout=10)
                if resp.status_code != 200:
                    return error_response(
                        code='PRODUCT_NOT_FOUND',
                        message=f'Producto {producto_id} no encontrado en el catalogo.',
                        status_code=status.HTTP_400_BAD_REQUEST,
                    )
                product_data = resp.json()

                if product_data.get('stock', 0) < cantidad:
                    return error_response(
                        code='INSUFFICIENT_STOCK',
                        message=f'Stock insuficiente para el producto {producto_id}.',
                        status_code=status.HTTP_400_BAD_REQUEST,
                    )

                precio_real = product_data.get('precio')
                if float(precio_unitario) != float(precio_real):
                    return error_response(
                        code='PRICE_MISMATCH',
                        message=(
                            f'Precio incorrecto para el producto {producto_id}. '
                            f'Precio real: {precio_real}'
                        ),
                        status_code=status.HTTP_400_BAD_REQUEST,
                    )

            except requests.RequestException:
                return error_response(
                    code='SERVICE_UNAVAILABLE',
                    message='No se pudo conectar con Product Service. Intenta mas tarde.',
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

        # 3. Crear el pedido en la base de datos
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pedido = serializer.save(usuario_id=usuario_id)

        # 4. Reducir el stock en Product Service
        try:
            reduce_url = f'{PRODUCT_SERVICE_URL}/api/products/reduce-stock/'
            resp = requests.post(reduce_url, json={'productos': productos}, timeout=10)
            if resp.status_code != 200:
                pedido.delete()
                return error_response(
                    code='STOCK_REDUCTION_FAILED',
                    message='No se pudo reducir el stock. El pedido fue cancelado.',
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
        except requests.RequestException:
            pedido.delete()
            return error_response(
                code='SERVICE_UNAVAILABLE',
                message='Error al conectar con Product Service al reducir stock. Pedido cancelado.',
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # 5. Respuesta exitosa
        return success_response(
            message='Pedido creado correctamente.',
            data=PedidoSerializer(pedido).data,
            status_code=201,
        )


@extend_schema(
    responses={200: PedidoSerializer},
    examples=[
        OpenApiExample(
            'Respuesta - pedido encontrado',
            summary='Estado actual del pedido y lista de productos',
            value={
                'success': True,
                'message': 'Pedido obtenido correctamente.',
                'data': {
                    'id': 101,
                    'usuario_id': 42,
                    'estado': 'PENDIENTE',
                    'productos': [
                        {'producto_id': 7,  'cantidad': 2, 'precio_unitario': '199.00'},
                        {'producto_id': 15, 'cantidad': 1, 'precio_unitario': '799.00'},
                    ],
                },
                'timestamp': _EJ_TIMESTAMP,
            },
            response_only=True,
            status_codes=['200'],
        ),
    ],
)
class PedidoDetailView(generics.RetrieveAPIView):
    # AllowAny: el Equipo 4 (Pagos) y Equipo 5 (Envios) consultan este
    # endpoint desde sus propios servidores, sin token de usuario.
    permission_classes = [AllowAny]
    queryset = Pedido.objects.all()
    serializer_class = PedidoSerializer
    lookup_url_kwarg = 'id'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(
            message='Pedido obtenido correctamente.',
            data=serializer.data,
        )


@extend_schema(
    request=PedidoSerializer,
    responses={200: PedidoSerializer},
    examples=[
        OpenApiExample(
            'Solicitud - actualizar estado',
            summary='Cambiar estado del pedido (usado por Equipos 4 y 5)',
            value={'estado': 'PAGADO'},
            request_only=True,
        ),
        OpenApiExample(
            'Respuesta - estado actualizado',
            summary='Estado del pedido actualizado',
            value={
                'success': True,
                'message': 'Estado del pedido actualizado correctamente.',
                'data': {
                    'id': 101,
                    'usuario_id': 42,
                    'estado': 'PAGADO',
                    'productos': [
                        {'producto_id': 7, 'cantidad': 2, 'precio_unitario': '199.00'},
                    ],
                },
                'timestamp': _EJ_TIMESTAMP,
            },
            response_only=True,
            status_codes=['200'],
        ),
    ],
)
class PedidoStatusUpdateView(generics.UpdateAPIView):
    # AllowAny: los Equipos 4 y 5 llaman a este endpoint desde sus servidores.
    permission_classes = [AllowAny]
    queryset = Pedido.objects.all()
    serializer_class = PedidoSerializer
    lookup_url_kwarg = 'id'
    http_method_names = ['patch']

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        nuevo_estado = request.data.get('estado')

        if nuevo_estado not in dict(Pedido.Estado.choices):
            return error_response(
                code='INVALID_STATUS',
                message=(
                    f'Estado "{nuevo_estado}" invalido. '
                    f'Valores permitidos: {list(dict(Pedido.Estado.choices).keys())}'
                ),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        instance.estado = nuevo_estado
        instance.save()
        serializer = self.get_serializer(instance)
        return success_response(
            message='Estado del pedido actualizado correctamente.',
            data=serializer.data,
        )
