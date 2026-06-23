"""
Settings package.

By default we load development settings. Override in any environment with::

    DJANGO_SETTINGS_MODULE=config.settings.prod
"""
import os

_env = os.environ.get("DJANGO_ENV", "dev").lower()

if _env in ("prod", "production"):
    from .prod import *  # noqa: F401,F403
else:
    from .dev import *  # noqa: F401,F403
