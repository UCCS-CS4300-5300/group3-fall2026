from pathlib import Path
import os
import dj_database_url

BASE_DIR=Path(__file__).resolve().parent.parent

ON_RENDER = "RENDER" in os.environ
SECRET_KEY = os.environ.get("SECRET_KEY") or ("" if ON_RENDER else "course-starter-development-key")
if ON_RENDER and not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is required on Render")
DEBUG = os.environ.get("DEBUG", "False" if ON_RENDER else "True").lower() == "true"
RENDER_HOST = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
ALLOWED_HOSTS = [RENDER_HOST] if ON_RENDER and RENDER_HOST else ["*"]

INSTALLED_APPS=["django.contrib.admin","django.contrib.auth","django.contrib.contenttypes","django.contrib.sessions","django.contrib.messages","django.contrib.staticfiles","core"]
MIDDLEWARE=["django.middleware.security.SecurityMiddleware","whitenoise.middleware.WhiteNoiseMiddleware","django.contrib.sessions.middleware.SessionMiddleware","django.middleware.common.CommonMiddleware","django.middleware.csrf.CsrfViewMiddleware","django.contrib.auth.middleware.AuthenticationMiddleware","django.contrib.messages.middleware.MessageMiddleware","django.middleware.clickjacking.XFrameOptionsMiddleware"]
ROOT_URLCONF="config.urls"
TEMPLATES=[{"BACKEND":"django.template.backends.django.DjangoTemplates","DIRS":[BASE_DIR/"templates"],"APP_DIRS":True,"OPTIONS":{"context_processors":["django.template.context_processors.request","django.contrib.auth.context_processors.auth","django.contrib.messages.context_processors.messages"]}}]
WSGI_APPLICATION="config.wsgi.application"

DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":BASE_DIR/"db.sqlite3"}}
if os.environ.get("DATABASE_URL"):
    DATABASES = {"default": dj_database_url.parse(os.environ["DATABASE_URL"], conn_max_age=0)}
elif ON_RENDER:
    raise RuntimeError("DATABASE_URL is required on Render")

AUTH_PASSWORD_VALIDATORS=[]
LANGUAGE_CODE="en-us"
TIME_ZONE="America/Denver"
USE_I18N=True
USE_TZ=True
STATIC_URL="static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS=[BASE_DIR / "gen", BASE_DIR / "assets", BASE_DIR / "assets" / "images"]
DEFAULT_AUTO_FIELD="django.db.models.BigAutoField"
CSRF_TRUSTED_ORIGINS=["https://localhost:8000","https://*.app.github.dev"]
if RENDER_HOST:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_HOST}")
