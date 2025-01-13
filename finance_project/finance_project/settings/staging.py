from .base import *

DEBUG = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("STAGING_DATABASE_NAME"),
        "USER": env("STAGING_DATABASE_USER"),
        "PASSWORD": env("STAGING_DATABASE_PASSWORD"),
        "HOST": env("STAGING_DATABASE_HOST"),
        "PORT": env("STAGING_DATABASE_PORT", default="5432"),
    }
}
