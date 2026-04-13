from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Pedido

Usuario = get_user_model()


class PedidoDetailAPITestCase(APITestCase):
    def setUp(self):
        # Crear un usuario ficticio para autenticación
        self.usuario = Usuario.objects.create_user(
            username='testuser',
            password='testpass',
        )
        self.pedido = Pedido.objects.create(
            usuario_id=1,  # Usar ID ficticio
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
        self.assertEqual(response.data['data']['usuario_id'], 1)
        self.assertEqual(response.data['data']['estado'], Pedido.Estado.PENDIENTE)

    def test_get_order_detail_not_found(self):
        self.client.force_authenticate(user=self.usuario)

        response = self.client.get('/api/orders/999999/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error']['code'], 'NOT_FOUND')
