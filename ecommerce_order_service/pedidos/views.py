from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
import requests

from order_service.api_response import success_response

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
                    'usuario_id': 42,
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
        serializer.save(usuario_id=self.request.user.id)

    def create(self, request, *args, **kwargs):
        # Verificar que el usuario exista en Identity Service
        try:
            identity_service_url = 'http://localhost:8000/api/users/{}/profile/'.format(request.user.id)
            resp = requests.get(identity_service_url, timeout=10)
            if resp.status_code != 200:
                return Response(
                    {'error': 'Usuario no válido o no encontrado en Identity Service.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except requests.RequestException:
            return Response(
                {'error': 'Error al conectar con Identity Service.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Verificar productos: stock y precios
        productos = request.data.get('productos', [])
        if not productos:
            return Response(
                {'error': 'Debe proporcionar al menos un producto.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        for producto in productos:
            producto_id = producto.get('producto_id')
            cantidad = producto.get('cantidad')
            precio_unitario = producto.get('precio_unitario')
            try:
                product_detail_url = 'http://localhost:8000/api/products/{}/'.format(producto_id)
                resp = requests.get(product_detail_url, timeout=10)
                if resp.status_code != 200:
                    return Response(
                        {'error': f'Producto {producto_id} no encontrado.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                product_data = resp.json()
                if product_data.get('stock', 0) < cantidad:
                    return Response(
                        {'error': f'Stock insuficiente para producto {producto_id}.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                precio_real = product_data.get('precio')
                if float(precio_unitario) != float(precio_real):
                    return Response(
                        {'error': f'Precio incorrecto para producto {producto_id}. Precio real: {precio_real}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except requests.RequestException:
                return Response(
                    {'error': 'Error al conectar con Product Service.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        # Crear el pedido
        response = super().create(request, *args, **kwargs)
        
        # Reducir stock
        try:
            product_service_url = 'http://localhost:8000/api/products/reduce-stock/'
            data_to_send = {
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
                    'usuario_id': 42,
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
    request=PedidoSerializer,  # Solo estado, pero usar PedidoSerializer
    responses={200: PedidoSerializer},
    examples=[
        OpenApiExample(
            'Solicitud - actualizar estado',
            summary='Cambiar estado del pedido',
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
        )
    ],
)
class PedidoStatusUpdateView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Pedido.objects.all()
    serializer_class = PedidoSerializer
    lookup_url_kwarg = 'id'
    http_method_names = ['patch']

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        nuevo_estado = request.data.get('estado')
        if nuevo_estado not in dict(Pedido.Estado.choices):
            return Response({'error': 'Estado inválido.'}, status=status.HTTP_400_BAD_REQUEST)
        instance.estado = nuevo_estado
        instance.save()
        serializer = self.get_serializer(instance)
        return success_response(
            message='Estado del pedido actualizado correctamente.',
            data=serializer.data,
        )
