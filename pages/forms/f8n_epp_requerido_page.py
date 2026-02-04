# pages/forms/f8n_epp_requerido_page.py
from ..base_page import BasePage
from utils.elements import (
    marcar_tabla_riesgos,
    seleccion_simple,
    campo_texto_por_label,
    campo_numerico,
    seleccion_multiple,
    campo_cuales_para,   # <-- nuevo import
)

class F8nEppRequeridoPage(BasePage):
    """TEBSA - F8n. EPP Requerido"""

    def completar(self, data: dict):
        # Tabla principal EPP Requerido*
        tabla_xpath = '//*[@id="auto-fields"]/div[1]/div[1]/div/div/table'
        marcar_tabla_riesgos(self.d, self.wait, tabla_xpath, data.get("tabla_epp", {}), default="No")

        # Traje para uso de químicos -> Nivel (solo si es "Si")
        if "traje_quimicos" in data:
            seleccion_simple(self.d, self.wait, "Traje para uso de químicos", data["traje_quimicos"])
            if str(data["traje_quimicos"]).strip().lower() == "si" and "nivel_quimicos" in data:
                campo_texto_por_label(self.d, self.wait, "Nivel", data["nivel_quimicos"])

        # Punto de Anclaje -> Anclaje (multi)
        if "punto_anclaje" in data:
            seleccion_simple(self.d, self.wait, "Punto de Anclaje", data["punto_anclaje"])
            if "anclaje_tipo" in data:
                vals = data["anclaje_tipo"]
                if isinstance(vals, str):
                    vals = [vals]
                seleccion_multiple(self.d, self.wait, "Anclaje", vals)

        # Línea de vida (Si) + tipo (multi)
        if "linea_vida" in data:
            seleccion_simple(self.d, self.wait, "Línea de vida", data["linea_vida"])
        if "linea_vida_tipo" in data:
            vals = data["linea_vida_tipo"]
            if isinstance(vals, str):
                vals = [vals]
            try:
                seleccion_multiple(self.d, self.wait, "Linea de vida", vals)   # sin tilde
            except Exception:
                seleccion_multiple(self.d, self.wait, "Línea de vida", vals)   # con tilde

        # Arnés
        if "arnes" in data:
            seleccion_simple(self.d, self.wait, "Arnes", data["arnes"])

        # ¿Cuántas argollas? (numérico)
        if "argollas" in data:
            campo_numerico(self.d, self.wait, "¿Cuantas argollas?", data["argollas"])

        # Otros conectores -> ¿Cuales?
        if "otros_conectores" in data:
            seleccion_simple(self.d, self.wait, "Otros conectores", data["otros_conectores"])
            if str(data["otros_conectores"]).strip().lower() == "si" and "otros_conectores_cuales" in data:
                # escribe en el '¿Cuales?' que está DESPUÉS de 'Otros conectores'
                campo_cuales_para(self.d, self.wait, "Otros conectores", data["otros_conectores_cuales"])

        # Otros -> ¿Cuáles?
        if "otros" in data:
            seleccion_simple(self.d, self.wait, "Otros", data["otros"])
            if str(data["otros"]).strip().lower() == "si" and "otros_cuales" in data:
                # idem, pero relativo a 'Otros'
                campo_cuales_para(self.d, self.wait, "Otros", data["otros_cuales"])