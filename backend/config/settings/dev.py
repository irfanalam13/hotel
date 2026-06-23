"""Development settings."""
from .base import *  # noqa: F401,F403
from .base import env

DEBUG = True

ALLOWED_HOSTS = ["*"]

# Browsable API is handy locally.
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = (  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
)

# Run Celery tasks inline unless a worker/broker is explicitly configured.
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=True)

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Avoid manifest static storage in dev (no collectstatic needed for the
# browsable API / admin assets).
STORAGES["staticfiles"]["BACKEND"] = (  # noqa: F405
    "django.contrib.staticfiles.storage.StaticFilesStorage"
)
