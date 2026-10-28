
import uuid

from django.http import JsonResponse


class RequestIdMiddleware:
    """Attach a server-generated correlation ID to each request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.request_id = uuid.uuid4().hex
        response = self.get_response(request)
        response["X-Request-ID"] = request.request_id
        return response


class SuspendedAccountMiddleware:
    """Deny protected API and admin access to inactive or suspended accounts."""

    LOGOUT_PATH = "/api/auth/logout/"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == self.LOGOUT_PATH:
            return self.get_response(request)

        user = request.user
        if (
            user.is_authenticated
            and (
                not user.is_active
                or getattr(user, "is_suspended", False)
            )
            and (
                request.path.startswith("/api/")
                or request.path.startswith("/admin/")
            )
        ):
            return JsonResponse(
                {"detail": "Account is inactive or suspended."},
                status=403,
            )

        return self.get_response(request)
