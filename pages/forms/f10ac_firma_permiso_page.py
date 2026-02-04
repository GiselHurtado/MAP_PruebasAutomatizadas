# pages/forms/f10ac_firma_permiso_page.py
from ..base_page import BasePage
from utils.elements import (
    campo_texto_por_label,
    seleccion_simple,
    campo_firma,
    enviar_y_confirmar,
)

class F10acFirmaPermisoPage(BasePage):
    """TEBSA - F10a.c. Firma Permiso de Trabajo (Trabajador autorizado)"""

    def completar(self, data: dict | None = None):
        data = data or {}

        # 1) Firma en canvas + click al botón verde "Firma"
        etiqueta = data.get("etiqueta_firma", "Firma")
        campo_firma(self.d, self.wait, etiqueta)

    def completar_y_enviar(self, data: dict | None = None):
        self.completar(data)
        enviar_y_confirmar(self.d, self.wait)
