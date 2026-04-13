from django.urls import path

from .views import PedidoCreateView, PedidoDetailView, PedidoStatusUpdateView

urlpatterns = [
    path('', PedidoCreateView.as_view(), name='pedido-create'),
    path('<int:id>/', PedidoDetailView.as_view(), name='pedido-detail'),
    path('<int:id>/status/', PedidoStatusUpdateView.as_view(), name='pedido-status-update'),
]
