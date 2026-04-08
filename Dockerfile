FROM harbor.smartcloud.samsungaustin.com/library/hub/apache/superset:6.0.0
#knoxme==1.1.13 sas_auth_wrapper==1.0.1
COPY pip.conf resolv.conf login.defs /etc/
COPY sources.list /etc/apt/sources.list
COPY ms-playwright.tgz /tmp/ms-playwright.tgz
COPY python_utils/knoxme_mailer.py /app/knoxme_mailer.py
COPY python_utils/knoxme_patch.py /app/knoxme_patch.py

USER root

RUN mkdir -p /ms-playwright \
 && tar -xzf /tmp/ms-playwright.tgz -C /ms-playwright --strip-components=1 \
 && rm -f /tmp/ms-playwright.tgz

# Make Playwright use the baked bundle and never download
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 \
    HOME=/app/superset_home

# Install OS deps from internal apt mirror (add python3-venv/python3-pip for robustness)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      python3-venv python3-pip \
      fonts-liberation \
      libnss3 \
      libatk-bridge2.0-0 \
      libgtk-3-0 \
      libx11-xcb1 \
      libxcomposite1 \
      libxdamage1 \
      libxrandr2 \
      libgbm1 \
      libasound2 \
      libpangocairo-1.0-0 \
      libpango-1.0-0 \
      libcairo2 \
      libdrm2 \
      ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Bootstrap pip into Superset’s venv
RUN /app/.venv/bin/python -m ensurepip --upgrade \
 && /app/.venv/bin/python -m pip install --upgrade pip setuptools wheel \
 && /app/.venv/bin/python -m pip --version


 # Install packages using uv into the virtual environment
RUN /app/.venv/bin/python -m pip install --no-cache-dir \
    # install psycopg2 for using PostgreSQL metadata store - could be a MySQL package if using that backend:
    psycopg2-binary \
    # package needed for using single-sign on authentication:
    Authlib \
    # openpyxl to be able to upload Excel files
    openpyxl \
    # Pillow for Alerts & Reports to generate PDFs of dashboards
    Pillow \
    trino \
    impyla \
    sqlalchemy_dremio \
    cockroachdb \
    cx_Oracle \
    # install Playwright for taking screenshots for Alerts & Reports. This assumes the feature flag PLAYWRIGHT_REPORTS_AND_THUMBNAILS is enabled
    # Playwright works only with Chrome.
    # If you are still using Selenium instead of Playwright, you would instead install here the selenium package and a headless browser & webdriver
    "playwright==1.50.0" \
    "knoxme==1.1.13" \
    "sas_auth_wrapper==1.0.1" \
    && playwright install-deps 
    #&& PLAYWRIGHT_BROWSERS_PATH=/usr/local/share/playwright-browsers playwright install chromium

#RUN /app/.venv/bin/python -m pip install --no-cache-dir \
#    knoxme==1.1.13 sas_auth_wrapper==1.0.1 \

# Optional: verify Playwright can launch headless using baked browsers
RUN /app/.venv/bin/python -c "from playwright.sync_api import sync_playwright; \
p=sync_playwright().start(); \
b=p.chromium.launch(headless=True); \
page=b.new_page(); page.set_content('<h1>ok</h1>'); \
print('screenshot bytes', len(page.screenshot())); \
b.close(); p.stop(); \
print('OK')"

USER superset

CMD ["/app/docker/entrypoints/run-server.sh"]
