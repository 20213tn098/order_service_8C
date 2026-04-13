from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
import requests

from identity_service.api_response import success_response

from .models import Pedido
from .serializers import PedidoSerializer, PedidoCreateSerializer

_EJ_TIMESTAMP = '2026-04-11T20:15:30Z'


@extend_schema(
    request=PedidoCreateSerializer,
    responses={201: PedidoSerializer},
    examples=[
        OpenApiExample(
            'Solicitud - crear pedido',
            summary='Crear un pedido con lista de productos',
            value={
                'productos': [
                    {'producto_id': 7, 'cantidad': 2, 'precio_unitario': '199.00'},
                    {'producto_id': 15, 'cantidad': 1, 'precio_unitario': '799.00'},
                ]
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
                    'usuario': 42,
                    'estado': 'PENDIENTE',
                    'productos': [
                        {'producto_id': 7, 'cantidad': 2, 'precio_unitario': '199.00'},
                        {'producto_id': 15, 'cantidad': 1, 'precio_unitario': '799.00'},
                    ],
                    'created_at': '2026-04-11T20:15:30Z',
                    'updated_at': '2026-04-11T20:15:30Z',
                },
                'timestamp': _EJ_TIMESTAMP,
            },
            response_only=True,
            status_codes=['201'],
        )
    ],
)
class PedidoCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PedidoCreateSerializer

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        
        # Hacer petición POST para reducir stock
        productos = request.data.get('productos', [])
        if productos:
            try:
                # Asumir URL del servicio de productos
                product_service_url = 'http://localhost:8000/api/products/reduce-stock/'
                #Data de la API para reducir stock
                data_to_send = {
                    'usuario_id': request.user.id,
                    'productos': productos
                }
                resp = requests.post(product_service_url, json=data_to_send, timeout=10)
                if resp.status_code != 200:
                    # Si falla, eliminar el pedido creado
                    pedido_id = response.data.get('id')
                    if pedido_id:
                        Pedido.objects.filter(id=pedido_id).delete()
                    return Response(
                        {'error': 'No se pudo reducir el stock de los productos.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except requests.RequestException:
                # Si hay error de conexión, eliminar pedido
                pedido_id = response.data.get('id')
                if pedido_id:
                    Pedido.objects.filter(id=pedido_id).delete()
                return Response(
                    {'error': 'Error al conectar con el servicio de productos.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # Personalizar la respuesta usando success_response
        serializer = PedidoSerializer(response.data)
        return success_response(
            message='Pedido creado correctamente.',
            data=serializer.data,
            status=201
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
                    'usuario': 42,
                    'estado': 'PENDIENTE',
                    'productos': [
                        {'producto_id': 7, 'cantidad': 2, 'precio_unitario': '199.00'},
                        {'producto_id': 15, 'cantidad': 1, 'precio_unitario': '799.00'},
                    ],
                },
                'timestamp': _EJ_TIMESTAMP,
            },
            response_only=True,
            status_codes=['200'],
        )
    ],
)
class PedidoDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Pedido.objects.select_related('usuario').all()
    serializer_class = PedidoSerializer
    lookup_url_kwarg = 'id'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(
            message='Pedido obtenido correctamente.',
            data=serializer.data,
        )
