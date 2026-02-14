from apps.auditlog.models import AuditEvent

SENSITIVE_KEYS = {"password", "token", "refresh", "access"}

class AuditLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        try:
            user = getattr(request, "user", None)
            tenant = getattr(request, "tenant", None)
            ip = request.META.get("REMOTE_ADDR", "")
            ua = request.META.get("HTTP_USER_AGENT", "")[:300]

            body_meta = {}
            if request.method in ["POST", "PUT", "PATCH"]:
                # best-effort: don’t crash if body isn’t JSON
                try:
                    data = getattr(request, "data", None)
                    if isinstance(data, dict):
                        body_meta = {k: ("***" if k in SENSITIVE_KEYS else v) for k, v in data.items()}
                except Exception:
                    body_meta = {}

            AuditEvent.objects.create(
                hotel=tenant,
                user=user if (user and user.is_authenticated) else None,
                method=request.method,
                path=request.path[:300],
                status_code=getattr(response, "status_code", 0) or 0,
                ip=ip,
                user_agent=ua,
                metadata={"body": body_meta},
            )
        except Exception:
            # never break the app due to audit logging
            pass

        return response
