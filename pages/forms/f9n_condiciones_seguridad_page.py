# pages/forms/f9n_condiciones_seguridad_page.py
from ..base_page import BasePage
from utils.elements import marcar_tabla_riesgos, seleccion_simple

class F9nCondicionesSeguridadPage(BasePage):
    """TEBSA - F9n. Condiciones de Seguridad"""
    TABLA_XPATH = '//*[@id="auto-fields"]/div[1]/div[1]/div/div/table'  # ajusta si difiere

    def completar(self, data: dict | None = None):
        # marca toda la tabla en "Si" salvo overrides en data["tabla"]
        overrides = (data or {}).get("tabla", {})
        marcar_tabla_riesgos(self.d, self.wait, self.TABLA_XPATH, overrides, default="Si")

        # campo "Otros" (fuera de la tabla)
        otros_val = (data or {}).get("otros", "No")
        seleccion_simple(self.d, self.wait, "Otros", otros_val)
