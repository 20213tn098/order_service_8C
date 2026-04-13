from datetime import UTC

from django.utils import timezone
from rest_framework.response import Response


def utc_timestamp() -> str:
    """Return an ISO-8601 timestamp in UTC with Z suffix."""
    return timezone.now().astimezone(UTC).isoformat().replace('+00:00', 'Z')


def success_response(message: str, data, status_code: int = 200) -> Response:
    return Response(
        {
            'success': True,
            'message': message,
            'data': data,
            'timestamp': utc_timestamp(),
        },
        status=status_code,
    )


def error_response(code: str, message: str, status_code: int, details=None) -> Response:
    error_body = {
        'code': code,
        'message': message,
    }
    if details is not None:
        error_body['details'] = details

    return Response(
        {
            'success': False,
            'error': error_body,
            'timestamp': utc_timestamp(),
        },
        status=status_code,
    )
