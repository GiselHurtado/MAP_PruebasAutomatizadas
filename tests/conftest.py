# conftest.py
import os
import pytest
from utils.browser import build_driver
from dotenv import load_dotenv
from datetime import datetime

# carga .env en APP_EMAIL / APP_PASSWORD
load_dotenv()

ARTIF_DIR = "artifacts"
os.makedirs(ARTIF_DIR, exist_ok=True)

@pytest.fixture(scope="session")
def creds():
    return {
        "email": os.getenv("APP_EMAIL", "usuario@tebsa.com"),
        "password": os.getenv("APP_PASSWORD", "Tebsa2023!"),
    }

@pytest.fixture
def driver():
    d = build_driver(headless=False)
    yield d
    d.quit()

# Hook para guardar evidencia si falla la fase "call"
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()

    if rep.when == "call":
        # Adjunta también user_properties si el test las definió
        if hasattr(item, "user_properties"):
            rep.user_properties = getattr(item, "user_properties")

        if rep.failed and "driver" in item.fixturenames:
            drv = item.funcargs["driver"]
            # nombres seguros para archivo
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            node = item.nodeid.replace("::", "__").replace("/", "_").replace("\\", "_")
            png = os.path.join(ARTIF_DIR, f"{node}_{ts}.png")
            html = os.path.join(ARTIF_DIR, f"{node}_{ts}.html")

            try:
                drv.save_screenshot(png)
                with open(html, "w", encoding="utf-8") as f:
                    f.write(drv.page_source)
                # si usas pytest-html, adjunta como extra
                if hasattr(rep, "extra"):
                    from pytest_html import extras
                    rep.extra.append(extras.png(png))
                    rep.extra.append(extras.html(f'<a href="{html}">HTML source</a>'))
            except Exception as e:
                print(f"⚠️ No se pudo guardar evidencia: {e}")
