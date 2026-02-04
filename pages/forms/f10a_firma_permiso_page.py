# pages/forms/f10a_firma_permiso_page.py
from ..base_page import BasePage
from utils.elements import campo_texto_por_label, seleccion_simple, campo_firma, enviar_y_confirmar
from selenium.webdriver.common.by import By

class F10aFirmaPermisoPage(BasePage):
    """TEBSA - F10a. Firma Permiso de Trabajo"""

    def completar(self, data: dict | None = None):
        data = data or {}

        if "nombre" in data:
            campo_texto_por_label(self.d, self.wait, "Nombre", data["nombre"])

        if "cargo" in data:
            print(f"🟡 Intentando seleccionar Cargo = '{data['cargo']}'")
            seleccion_simple(self.d, self.wait, "Cargo", data["cargo"])
            # Log del valor real en el input tras seleccionar
            try:
                el = self.d.find_element(By.XPATH, "(//label[contains(normalize-space(.), 'Cargo')])[1]/following::input[1]")
                print("🟢 Cargo en input =", el.get_attribute("value"))
            except Exception:
                pass

        etiqueta = data.get("etiqueta_firma", "Firma")
        campo_firma(self.d, self.wait, etiqueta)

    def completar_y_enviar(self, data: dict | None = None):
        self.completar(data)
        enviar_y_confirmar(self.d, self.wait)
