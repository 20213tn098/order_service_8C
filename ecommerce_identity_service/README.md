# Identity Service

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

- Modelo de usuario personalizado (`correo` como `USERNAME_FIELD`).
- Endpoints para:
  - Registro de usuario.
  - Login con JWT (solo `access`).
  - Consulta de perfil autenticado.
  - Consulta de pedido por ID (estado y productos).
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

Base path: `/api/users/`

- `POST /register/`  
  Registra un usuario.

- `POST /login/`  
  Autentica con `correo` y `password`. Devuelve `access` y `usuario_id`.

- `GET /<id>/profile/`  
  Devuelve perfil del usuario (requiere `Authorization: Bearer <token>`).

Base path: `/api/orders/`

- `POST /`  
  Crea un pedido para el usuario autenticado con una lista de productos (requiere `Authorization: Bearer <token>`).

- `GET /<id>/`  
  Devuelve detalle del pedido (id, usuario, estado, productos) y requiere `Authorization: Bearer <token>`.

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

- `VALIDATION_ERROR`
- `INVALID_CREDENTIALS`
- `UNAUTHORIZED`
- `FORBIDDEN`
- `USER_NOT_FOUND`
- `NOT_FOUND`
- `METHOD_NOT_ALLOWED`
- `INTERNAL_ERROR`

## Comandos útiles

Validaciones básicas:

```bash
python manage.py check
python manage.py spectacular --validate --file /tmp/schema.yml
```

