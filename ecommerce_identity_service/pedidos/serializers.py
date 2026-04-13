from rest_framework import serializers

from .models import Pedido


class PedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pedido
        fields = ['id', 'usuario', 'estado', 'productos']


class PedidoCreateSerializer(serializers.ModelSerializer):
    productos = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
        help_text="Lista de productos con 'producto_id', 'cantidad' y 'precio_unitario'."
    )

    class Meta:
        model = Pedido
        fields = ['productos']

    def validate_productos(self, value):
        for producto in value:
            if not all(key in producto for key in ['producto_id', 'cantidad', 'precio_unitario']):
                raise serializers.ValidationError(
                    "Cada producto debe tener 'producto_id', 'cantidad' y 'precio_unitario'."
                )
            if not isinstance(producto['cantidad'], int) or producto['cantidad'] <= 0:
                raise serializers.ValidationError("La cantidad debe ser un entero positivo.")
        return value
