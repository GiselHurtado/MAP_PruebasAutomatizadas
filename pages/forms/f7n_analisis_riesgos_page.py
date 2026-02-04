from ..base_page import BasePage
from utils.elements import seleccion_simple, campo_texto_por_label, marcar_tabla_riesgos,  campo_numerico

class F7nAnalisisRiesgosPage(BasePage):
    """TEBSA - F7n. Análisis de Riesgos"""

    def completar(self, data: dict):
        tabla_xpath = '//*[@id="auto-fields"]/div[1]/div[1]/div/div/table'
        respuestas = data.get("tabla_riesgos", {})
        marcar_tabla_riesgos(self.d, self.wait, tabla_xpath, respuestas, default="No")

        # Temperaturas extremas
        if "temp_extremas" in data:
            seleccion_simple(self.d, self.wait, "Temperaturas extremas", data["temp_extremas"])
            if str(data["temp_extremas"]).strip().lower() == "si" and "temp_c" in data:
                campo_numerico(self.d, self.wait, "°C", data["temp_c"])

        # Presiones
        if "presiones" in data:
            seleccion_simple(self.d, self.wait, "Presiones", data["presiones"])
            if str(data["presiones"]).strip().lower() == "si" and "presion_bar" in data:
                campo_numerico(self.d, self.wait, "Bar", data["presion_bar"])

        # Eléctrico
        if "electrico" in data:
            seleccion_simple(self.d, self.wait, "Eléctrico", data["electrico"])
            if str(data["electrico"]).strip().lower() == "si" and "volt" in data:
                campo_numerico(self.d, self.wait, "Volt", data["volt"])

        # Otros
        if "otros" in data:
            seleccion_simple(self.d, self.wait, "Otros", data["otros"])
            if str(data["otros"]).strip().lower() == "si" and "otros_cuales" in data:
                campo_texto_por_label(self.d, self.wait, "¿Cuáles?", data["otros_cuales"])
