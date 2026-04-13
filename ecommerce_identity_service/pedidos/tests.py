from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Pedido

Usuario = get_user_model()


class PedidoDetailAPITestCase(APITestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            correo='equipo3@test.com',
            password='ClaveSegura123',
            nombre='Equipo',
            apellido='Tres',
            calle='Av. Principal',
            numero_exterior='100',
            numero_interior='',
            colonia='Centro',
            ciudad='Puebla',
            estado='Puebla',
            codigo_postal='72000',
            pais='MX',
        )
        self.pedido = Pedido.objects.create(
            usuario=self.usuario,
            estado=Pedido.Estado.PENDIENTE,
            productos=[
                {'producto_id': 1, 'cantidad': 2, 'precio_unitario': '99.90'},
                {'producto_id': 2, 'cantidad': 1, 'precio_unitario': '249.00'},
            ],
        )

    def test_get_order_detail_requires_auth(self):
        response = self.client.get(f'/api/orders/{self.pedido.id}/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_order_detail_success(self):
        self.client.force_authenticate(user=self.usuario)

        response = self.client.get(f'/api/orders/{self.pedido.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['id'], self.pedido.id)
        self.assertEqual(response.data['data']['usuario'], self.usuario.id)
        self.assertEqual(response.data['data']['estado'], Pedido.Estado.PENDIENTE)

    def test_get_order_detail_not_found(self):
        self.client.force_authenticate(user=self.usuario)

        response = self.client.get('/api/orders/999999/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error']['code'], 'NOT_FOUND')


class PedidoStatusUpdateAPITestCase(APITestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            correo='equipo4@test.com',
            password='ClaveSegura123',
            nombre='Equipo',
            apellido='Cuatro',
            calle='Av. Principal',
            numero_exterior='100',
            numero_interior='',
            colonia='Centro',
            ciudad='Puebla',
            estado='Puebla',
            codigo_postal='72000',
            pais='MX',
        )
        self.pedido = Pedido.objects.create(
            usuario=self.usuario,
            estado=Pedido.Estado.PENDIENTE,
            productos=[
                {'producto_id': 1, 'cantidad': 2, 'precio_unitario': '99.90'},
            ],
        )

    def test_patch_order_status_requires_auth(self):
        response = self.client.patch(
            f'/api/orders/{self.pedido.id}/status/',
            {'estado': Pedido.Estado.PAGADO},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_order_status_success(self):
        self.client.force_authenticate(user=self.usuario)

        response = self.client.patch(
            f'/api/orders/{self.pedido.id}/status/',
            {'estado': Pedido.Estado.PAGADO},
            format='json',
        )

        self.pedido.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['id'], self.pedido.id)
        self.assertEqual(response.data['data']['estado'], Pedido.Estado.PAGADO)
        self.assertEqual(self.pedido.estado, Pedido.Estado.PAGADO)

    def test_patch_order_status_invalid_status(self):
        self.client.force_authenticate(user=self.usuario)

        response = self.client.patch(
            f'/api/orders/{self.pedido.id}/status/',
            {'estado': 'CANCELADO'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error']['code'], 'VALIDATION_ERROR')

    def test_patch_order_status_not_found(self):
        self.client.force_authenticate(user=self.usuario)

        response = self.client.patch(
            '/api/orders/999999/status/',
            {'estado': Pedido.Estado.PAGADO},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error']['code'], 'NOT_FOUND')