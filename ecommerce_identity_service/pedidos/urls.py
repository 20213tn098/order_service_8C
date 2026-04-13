from django.urls import path

from .views import PedidoCreateView, PedidoDetailView

urlpatterns = [
    path('', PedidoCreateView.as_view(), name='pedido-create'),
    path('<int:id>/', PedidoDetailView.as_view(), name='pedido-detail'),
]
