from ..base_page import BasePage
from utils.elements import enviar_y_confirmar

class F1NuevoPermisoPage(BasePage):
    """Primer formulario: típicamente solo enviar (según tu flujo)"""

    def completar_y_enviar(self):
        enviar_y_confirmar(self.d, self.wait)
