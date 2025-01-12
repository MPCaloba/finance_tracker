from .base import *

DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("PROD_DATABASE_NAME"),
        "USER": env("PROD_DATABASE_USER"),
        "PASSWORD": env("PROD_DATABASE_PASSWORD"),
        "HOST": env("PROD_DATABASE_HOST"),
        "PORT": env("PROD_DATABASE_PORT", default="5432"),
    }
}
