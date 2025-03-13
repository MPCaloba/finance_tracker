from pathlib import Path
import environ


# Initialize environment variables
BASE_DIR = Path(__file__).resolve().parent.parent.parent
env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')  # reads .env file if exists


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')


ALLOWED_HOSTS = ['127.0.0.1', 'localhost']


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    'django.contrib.sites',
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    
    # external apps
    "django_extensions",
    "debug_toolbar",
    "widget_tweaks",
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'django_filters',
    'django_htmx',
    'import_export',
    
    # project apps
    "tracker",
]

SITE_ID = 1

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

ROOT_URLCONF = "finance_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / 'finance_project' / 'templates'],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "finance_project.wsgi.application"


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

INTERNAL_IPS = ["127.0.0.1"]

AUTH_USER_MODEL = 'tracker.User'
LOGIN_REDIRECT_URL = 'index'

PAGE_SIZE = 10
