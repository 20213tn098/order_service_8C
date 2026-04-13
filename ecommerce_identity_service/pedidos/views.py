from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from identity_service.api_response import success_response

from .models import Pedido
from .serializers import PedidoSerializer, PedidoCreateSerializer, PedidoStatusUpdateSerializer

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

@extend_schema(
    request=PedidoStatusUpdateSerializer,
    responses={200: PedidoSerializer},
    examples=[
        OpenApiExample(
            'Solicitud - actualizar estado',
            summary='Actualizar solo el estado del pedido',
            value={'estado': 'PAGADO'},
            request_only=True,
        ),
        OpenApiExample(
            'Respuesta - estado actualizado',
            summary='Pedido actualizado correctamente',
            value={
                'success': True,
                'message': 'Estado del pedido actualizado correctamente.',
                'data': {
                    'id': 101,
                    'usuario': 42,
                    'estado': 'PAGADO',
                    'productos': [
                        {'producto_id': 7, 'cantidad': 2, 'precio_unitario': '199.00'},
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
class PedidoStatusUpdateView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Pedido.objects.select_related('usuario').all()
    serializer_class = PedidoStatusUpdateSerializer
    lookup_url_kwarg = 'id'
    http_method_names = ['patch']

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        response = super().update(request, *args, **kwargs)
        return success_response(
            message='Estado del pedido actualizado correctamente.',
            data=response.data,
        )