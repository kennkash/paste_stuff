"""
KS Superset configuration overrides

Loaded via Helm `configOverrides` / mounted into /app/pythonpath.
Keep this file import-safe (no heavy imports / no network calls at import time).
"""
import os
from datetime import timedelta
import sys
sys.path.append("/app")
import ssl

# os.environ["REQUESTS_CA_BUNDLE"] = "/app/certs/gitlab_ca.crt"
# os.environ["SSL_CERT_FILE"] = "/app/certs/gitlab_ca.crt"
from superset.tasks.types import FixedExecutor
from flask_appbuilder.security.manager import AUTH_OAUTH
#from superset.security import SupersetSecurityManager
#from flask_appbuilder.security.manager import AUTH_DB,AUTH_LDAP
from custom_security_manager import CustomSecurityManager

# -----------------------------------------------------------------------------
# 1) Branding / UI
# -----------------------------------------------------------------------------
APP_NAME = "KS Superset 6.0.0"
CUSTOM_FOOTER_TEXT = "brought to you by Knowledge Solutions"
DEBUG = True


# -----------------------------------------------------------------------------
# 2) App safety / headers (embedding)
# -----------------------------------------------------------------------------
TALISMAN_CONFIG = {
    "content_security_policy": {
        # Allow embedding in *.samsungaustin.com
        "frame-ancestors": ["'self'", "*.samsungaustin.com"],
    }
}


# -----------------------------------------------------------------------------
# 3) Limits / timeouts
# -----------------------------------------------------------------------------
ROW_LIMIT = 1_000_000
SUPERSET_WEBSERVER_TIMEOUT = int(timedelta(minutes=1).total_seconds())


# -----------------------------------------------------------------------------
# 4) Feature flags
# -----------------------------------------------------------------------------
FEATURE_FLAGS = {
    "EMBEDDED_SUPERSET": True,
    "ESTIMATE_QUERY_COST": True,
    "DASHBOARD_RBAC": True,
    "THUMBNAILS": True,
    "TAGGING_SYSTEM": True,
    "ALERT_REPORTS": True,
    "ALLOW_CSV_UPLOAD": True,
    "PLAYWRIGHT_REPORTS_AND_THUMBNAILS": True,
}


# -----------------------------------------------------------------------------
# 5) CSV upload defaults
# -----------------------------------------------------------------------------
CSV_TO_DATABASE = {
    "database_id": 14,
    "schema": "uploads",
}


# -----------------------------------------------------------------------------
# 6) Alerts & Reports (email + screenshots)
# -----------------------------------------------------------------------------
# Ensure reports actually send (not dry-run)
ALERT_REPORTS_NOTIFICATION_DRY_RUN = False

# Run reports as a fixed user (optional)
# (If you want per-owner execution, remove this line.)
#ALERT_REPORTS_EXECUTORS = [FixedExecutor("admin")]

# Celery workers must be able to reach Superset via an internal URL
WEBDRIVER_BASEURL = "http://superset.superset.svc.cluster.local:8088"

# Screenshot waits (Playwright/Selenium timing knobs)
SCREENSHOT_LOCATE_WAIT = 100
SCREENSHOT_LOAD_WAIT = 600

# Optional: throttle/report cadence safety rails
ALERT_MINIMUM_INTERVAL = int(timedelta(minutes=10).total_seconds())
REPORT_MINIMUM_INTERVAL = int(timedelta(minutes=5).total_seconds())


# -----------------------------------------------------------------------------
# 7) SMTP (SAS relay) — NO TLS, NO AUTH
# -----------------------------------------------------------------------------
SMTP_HOST = "192.30.190.232"
SMTP_PORT = 25

# No TLS/SSL
SMTP_STARTTLS = False
SMTP_SSL = False

# No auth
SMTP_USER = ""
SMTP_PASSWORD = ""

# The "from" address shown to recipients (your relay allows anything)
SMTP_MAIL_FROM = "superset-no-reply@samsung.com"

# Optional: make email subjects recognizable
EMAIL_REPORTS_SUBJECT_PREFIX = "[Superset] "


#WEBDRIVER_TYPE = "chrome"

#WEBDRIVER_OPTION_ARGS = [
#    "--headless=new",
#    "--no-sandbox",
#    "--disable-dev-shm-usage",
#    "--disable-gpu",
#    "--window-size=1920,1080",
#]

# These two are the important “no internet” knobs:
#WEBDRIVER_BINARY = "/usr/local/bin/google-chrome"   # or /usr/bin/chromium
#WEBDRIVER_DRIVER_PATH = "/usr/local/bin/chromedriver"

# -------------------------------------------------------------------------
# 8) Webdriver backend for Reports/Thumbnails (AIRGAP: Playwright + baked Chromium)
# -------------------------------------------------------------------------

# Force Playwright (do NOT rely on defaults)
#WEBDRIVER_TYPE = "playwright"

# Celery workers must be able to reach Superset via an internal URL
WEBDRIVER_BASEURL = "http://superset.superset.svc.cluster.local:8088"

# Optional: external URL shown in emails
WEBDRIVER_BASEURL_USER_FRIENDLY = "https://supersetvc.smartcloud.samsungaustin.com/"

# Timing knobs
SCREENSHOT_LOCATE_WAIT = 100
SCREENSHOT_LOAD_WAIT = 600

# # LDAP server configuration
# AUTH_TYPE = AUTH_LDAP

# # Allow users to self‑register (they will be given the role below)
# AUTH_USER_REGISTRATION = True
# AUTH_USER_REGISTRATION_ROLE = "Gamma"
# AUTH_LDAP_SERVER = "ldap://192.30.105.211:9100"
# AUTH_LDAP_USE_TLS = False                      # TLS disabled (LDAPS already encrypted)
# AUTH_LDAP_BIND_USER = "CN=svc_superset,OU=Service Accounts,OU=Admins,OU=SAS,OU=Locations,DC=samsungds,DC=net"
# AUTH_LDAP_BIND_PASSWORD = "8J22KW6$8+3l$cnq6Q.pQ^hc*9"           # <-- replace with the real secret in a secure vault
# AUTH_LDAP_SEARCH = "DC=samsungds,DC=net"
# AUTH_LDAP_UID_FIELD = "sAMAccountName"
# AUTH_LDAP_EMAIL_FIELD = "mail"
# # Optional LDAP attribute mapping
# AUTH_LDAP_FIRSTNAME_FIELD = "givenName"
# AUTH_LDAP_LASTNAME_FIELD = "sn"

# # Additional LDAP flags
# AUTH_LDAP_ALLOW_SELF_SIGNED = True
# AUTH_LDAP_APPEND_DOMAIN = False
# AUTH_LDAP_USE_TLS = False  # keep consistent with AUTH_LDAP_USE_TLS above
# RECAPTCHA_PUBLIC_KEY = None
# RECAPTCHA_PRIVATE_KEY = None

# # Use the custom security manager that you have implemented in `custom_security_manager.py`
# CUSTOM_SECURITY_MANAGER = CustomSecurityManager
from flask import Blueprint, redirect, request, flash, render_template_string
from flask_login import login_user
import logging

log = logging.getLogger(__name__)


ENABLE_PROXY_FIX = True
# OAUTH server configuration
SESSION_COOKIE_SECURE = True  # if using HTTPS
SESSION_COOKIE_SAMESITE = "None"  # if cross-domain or HTTPS

AUTH_TYPE = AUTH_OAUTH
CUSTOM_SECURITY_MANAGER = CustomSecurityManager
FAB_ADD_SECURITY_VIEWS = True

OAUTH_PROVIDERS = [
 {
  "name": "gitlab",
  "icon": "superset-gitlab",
  "token_key": "access_token",
  "button_name": "Sign in with Global AD",
  "remote_app": {
       "client_id": "5f3399c0b04518b0eff9413c3509eeb0ddc5d5cd1c334b1137b70cfd2beaa4e1",
       "client_secret": "gloas-174dfa4b8c5c077b95ca67947282019b1530ab325bcf0c583e7f1bb18bb397a1",
        "api_base_url": "https://gitlab.smartcloud.samsungds.net/api/v4",
        "access_token_url": "https://gitlab.smartcloud.samsungds.net/oauth/token",
        "authorize_url": "https://gitlab.smartcloud.samsungds.net/oauth/authorize",   
        "client_kwargs": {
             "scope": "read_user"
        },     
   },
  }
 ]

#  Load the HTML template that will be rendered for the admin login page.
TEMPLATE_PATH = "/app/admin_login.html"
with open(TEMPLATE_PATH, "r") as f:
    ADMIN_LOGIN_TEMPLATE = f.read()

#  Create a Flask *Blueprint* that will hold the admin‑login routes.
#  Using a blueprint keeps the admin‑specific code isolated from the
#  main Superset app, and makes it easy to register/unregister later.
admin_bp = Blueprint("admin_auth", __name__)


#  Route: /admin-login
#  Methods allowed: GET (show login form) and POST (process credentials). This view is a **stand‑alone** login that bypasses Superset’s default OAuth (GitLab) flow and authenticates 
#  directly against the Superset user database.
@admin_bp.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    from flask import current_app
    from flask_wtf.csrf import generate_csrf

    # Grab the submitted username/password from the HTML form.
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        # Superset stores a reference to its security manager on the app
        # (``appbuilder.sm``).  We use the manager's ``auth_user_db`` method
        # to check the credentials against the internal user DB
        sm = current_app.appbuilder.sm
        user = sm.auth_user_db(username, password)
        #  Invalid credentials → show an error and re‑render the form.
        if user is None:
            flash("Invalid username or password entered", "error")
            return render_template_string(ADMIN_LOGIN_TEMPLATE)
        #  Valid credentials but not an admin → deny access.
        # user_roles = [r.name for r in user.roles]
        # if "Admin" not in user_roles:
        #     flash("This login is restricted to admin-users only.", "error")
        #     return render_template_string(ADMIN_LOGIN_TEMPLATE)
        #  Credentials ok and user has the *Admin* role. Log the user in.
        login_user(user)
        log.info("DB login: %s", username)
        return redirect(current_app.appbuilder.get_url_for_index)

    return render_template_string(ADMIN_LOGIN_TEMPLATE)
#  Helper that is called from the main Superset factory (``create_app``).  It makes sure the admin blueprint is attached to the Flask app exactly once.
def FLASK_APP_MUTATOR(app):
    if "admin_auth" not in app.blueprints:
        app.register_blueprint(admin_bp)
        log.info("admin_auth blueprint registered")
        
AUTH_USER_REGISTRATION = True
AUTH_USER_REGISTRATION_ROLE = "Alpha"
#  AUTH_ROLES_SYNC_AT_LOGIN = True

# Enable Jinja templating
FEATURE_FLAGS = {
    'ENABLE_TEMPLATE_PROCESSING': True,
    # Other feature flags...
}

#PLAYWRIGHT_REPORTS_AND_THUMBNAILS= True


from celery.schedules import crontab

from celery.schedules import crontab

class SupersetCeleryConfig:
    broker_url = "redis://superset-redis-master:6379/0"
    result_backend = "redis://superset-redis-master:6379/1"

    imports = (
        "superset.tasks.scheduler",
        "superset.tasks.thumbnails",
    )

    beat_schedule = {
        "reports.scheduler": {
            "task": "reports.scheduler",
            "schedule": crontab(minute="*", hour="*"),
        },
        "reports.prune_log": {
            "task": "reports.prune_log",
            "schedule": crontab(minute=0, hour=0),
        },
    }

CELERY_CONFIG = SupersetCeleryConfig


