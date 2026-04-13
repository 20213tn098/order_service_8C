from django.conf import settings
from django.db import models


class Pedido(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        PAGADO = 'PAGADO', 'Pagado'
        ENVIADO = 'ENVIADO', 'Enviado'

    usuario_id = models.IntegerField(help_text="ID del usuario del servicio de identidad")
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    productos = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pedidos'

    def __str__(self):
        return f'Pedido #{self.pk} - {self.estado}'
