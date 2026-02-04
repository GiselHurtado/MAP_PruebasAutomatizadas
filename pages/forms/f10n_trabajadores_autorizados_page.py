# pages/forms/f10n_trabajadores_autorizados_page.py
from ..base_page import BasePage
from utils.elements import seleccion_multiple, enviar_y_confirmar

class F10nTrabajadoresAutorizadosPage(BasePage):
    """TEBSA - F10n. Trabajadores autorizados"""

    def completar_y_enviar(self, data: dict | None = None):
        """
        data:
          trabajadores: list[str]  # e.g. ["KATE BULA - 123654"]
        """
        valores = (data or {}).get("trabajadores", [])
        if isinstance(valores, str):
            valores = [valores]

        # Campo multiselección etiquetado “Trabajadores”
        if valores:
            seleccion_multiple(self.d, self.wait, "Trabajadores", valores)

        enviar_y_confirmar(self.d, self.wait)
