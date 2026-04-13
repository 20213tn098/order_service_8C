# Order Service

Microservicio de identidad para e-commerce construido con Django + Django REST Framework.  
Gestiona registro, autenticación con JWT (access token) y consulta de perfil de usuario.

## Stack

- Python 3.13
- Django 6.0.4
- Django REST Framework 3.17.1
- SimpleJWT 5.5.1
- drf-spectacular 0.29.0 (OpenAPI/Swagger)
- MySQL (`mysqlclient`)

## Características principales

- Módulo de pedidos (Order Service):
  - Orquestador principal de compras: agrupa productos seleccionados por el cliente y genera órdenes de cobro.
  - Modelo de pedido con ID, usuario, estado (Pendiente, Pagado, Enviado) y lista de productos (JSON con producto_id, cantidad, precio_unitario).
  - Endpoints para crear pedido (con validación de usuario y productos), consultar estado y actualizar estado.
  - Interacciones con servicios externos:
    - Identity Service: Verifica que el usuario exista y sea válido.
    - Product Service: Verifica stock y precios de productos, y solicita reducción de stock tras creación exitosa.
- Documentación Swagger con ejemplos reales.
- Contrato de respuesta estandarizado:
  - Éxito: `success`, `message`, `data`, `timestamp`
  - Error: `success`, `error { code, message, details? }`, `timestamp`
- Manejador global de errores DRF (`EXCEPTION_HANDLER`).

## Estructura del proyecto

- `identity_service/`: configuración principal Django, responses y manejo global de errores.
- `usuarios/`: app de dominio de usuarios (modelo, serializers, vistas y rutas).
- `manage.py`: punto de entrada de comandos Django.

## Variables de entorno

El proyecto usa `python-decouple` y requiere un archivo `.env` en la raíz.

Ejemplo:

```env
SECRET_KEY=tu_clave_secreta
DEBUG=True

DB_NAME=ecommerce_identity_service
DB_USER=root
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=3306
```

## Instalación y ejecución local

1. Crear y activar entorno virtual:

```bash
python3 -m venv venv
source venv/bin/activate
```

2. Instalar dependencias:

```bash
pip install -r requirements.txt
```

3. Aplicar migraciones:

```bash
python manage.py migrate
```

4. Levantar servidor:

```bash
python manage.py runserver
```

## Documentación OpenAPI / Swagger

- Schema OpenAPI: `http://localhost:8000/api/schema/`
- Swagger UI: `http://localhost:8000/api/schema/swagger-ui/`
- Alias docs: `http://localhost:8000/api/docs/`

## Endpoints

Base path: `/api/orders/`

- `POST /`  
  Crea un pedido para el usuario autenticado con una lista de productos (requiere `Authorization: Bearer <token>`).  
  **Consumo:**  
  ```json
  {
    "productos": [
      {
        "producto_id": 7,
        "cantidad": 2,
        "precio_unitario": "199.00"
      },
      {
        "producto_id": 15,
        "cantidad": 1,
        "precio_unitario": "799.00"
      }
    ]
  }
  ```  
  **Respuesta (éxito):**  
  ```json
  {
    "success": true,
    "message": "Pedido creado correctamente.",
    "data": {
      "id": 101,
      "usuario": 42,
      "estado": "PENDIENTE",
      "productos": [
        {
          "producto_id": 7,
          "cantidad": 2,
          "precio_unitario": "199.00"
        },
        {
          "producto_id": 15,
          "cantidad": 1,
          "precio_unitario": "799.00"
        }
      ],
      "created_at": "2026-04-11T20:15:30Z",
      "updated_at": "2026-04-11T20:15:30Z"
    },
    "timestamp": "2026-04-11T20:15:30Z"
  }
  ```

- `GET /<id>/`  
  Devuelve detalle del pedido (id, usuario, estado, productos) y requiere `Authorization: Bearer <token>`.  
  **Consumo:** Ninguno (ID en URL).  
  **Respuesta (éxito):**  
  ```json
  {
    "success": true,
    "message": "Pedido obtenido correctamente.",
    "data": {
      "id": 101,
      "usuario": 42,
      "estado": "PENDIENTE",
      "productos": [
        {
          "producto_id": 7,
          "cantidad": 2,
          "precio_unitario": "199.00"
        },
        {
          "producto_id": 15,
          "cantidad": 1,
          "precio_unitario": "799.00"
        }
      ]
    },
    "timestamp": "2026-04-11T20:15:30Z"
  }
  ```

- `PATCH /<id>/status/`  
  Actualiza el estado del pedido (requiere `Authorization: Bearer <token>`).  
  **Consumo:**  
  ```json
  {
    "estado": "PAGADO"
  }
  ```  
  **Respuesta (éxito):**  
  ```json
  {
    "success": true,
    "message": "Estado del pedido actualizado correctamente.",
    "data": {
      "id": 101,
      "usuario": 42,
      "estado": "PAGADO",
      "productos": [
        {
          "producto_id": 7,
          "cantidad": 2,
          "precio_unitario": "199.00"
        }
      ]
    },
    "timestamp": "2026-04-11T20:15:30Z"
  }
  ```

## Formato de respuestas

### Éxito

```json
{
  "success": true,
  "message": "Autenticación exitosa.",
  "data": {
    "access": "jwt_access_token",
    "usuario_id": 42
  },
  "timestamp": "2026-04-11T18:40:49.803297Z"
}
```

### Error de validación

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Los datos enviados no son válidos.",
    "details": {
      "password": [
        "Este campo es requerido."
      ]
    }
  },
  "timestamp": "2026-04-11T18:40:49.803297Z"
}
```

## Códigos de error usados
- `USER_NOT_VALID` (Usuario no válido o no encontrado en Identity Service)
- `IDENTITY_SERVICE_ERROR` (Error al conectar con Identity Service)
- `PRODUCT_NOT_FOUND` (Producto no encontrado en Product Service)
- `INSUFFICIENT_STOCK` (Stock insuficiente para un producto)
- `INVALID_PRICE` (Precio unitario incorrecto para un producto)
- `PRODUCT_SERVICE_ERROR` (Error al conectar con Product Service)
- `STOCK_REDUCTION_FAILED` (No se pudo reducir el stock de los productos)
- `INVALID_STATUS` (Estado inválido para actualizar el pedido)

## Comandos útiles

Validaciones básicas:

```bash
python manage.py check
python manage.py spectacular --validate --file /tmp/schema.yml
```

