# pages/forms/f10_2_trabajador_autorizado_info_page.py
from ..base_page import BasePage
from utils.elements import enviar_y_confirmar

class F10_2TrabajadorAutorizadoInfoPage(BasePage):
    """Formulario intermedio: 'Trabajador autorizado' (solo enviar/confirmar)."""
    def completar_y_enviar(self, _data: dict | None = None):
        enviar_y_confirmar(self.d, self.wait)
