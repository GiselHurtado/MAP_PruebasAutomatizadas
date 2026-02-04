# pages/forms/f10_firma_gerencia_page.py
from ..base_page import BasePage
from utils.elements import seleccion_simple, enviar_y_confirmar
from utils.elements import campo_firma  # ya lo tienes en utils.elements

class F10FirmaGerenciaPage(BasePage):
    """TEBSA - F10. Firma Gerencia"""

    def completar(self, data: dict | None = None):
        data = data or {}
        # Autoriza (select simple)
        if "autoriza" in data:
            seleccion_simple(self.d, self.wait, "Autoriza", data["autoriza"])
        # Firma en canvas (label: "Firma gerente" por lo que indicaste)
        etiqueta = data.get("etiqueta_firma", "Firma gerente")
        campo_firma(self.d, self.wait, etiqueta)

    def completar_y_enviar(self, data: dict | None = None):
        self.completar(data)
        enviar_y_confirmar(self.d, self.wait)
