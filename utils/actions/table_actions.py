# utils/actions/table_actions.py
"""
STRATEGY PATTERN - Estrategia para Tablas Interactivas

Esta clase implementa el patrón Strategy para manejar tablas con elementos
interactivos, específicamente:
- Tabla de riesgos del formulario F7n (checkboxes/radios por fila)
- Tablas con switches/toggles
- Tablas donde cada fila requiere marcar Sí/No

Forma parte del conjunto de estrategias especializadas en utils/actions/ que
son utilizadas a través del Facade Pattern en utils/elements.py.

Uso desde Page Objects (a través de la facade):
    from utils.elements import marcar_tabla_riesgos
    respuestas = {"Riesgo 1": "Si", "Riesgo 2": "No"}
    marcar_tabla_riesgos(driver, wait, "//table[@id='riesgos']", respuestas)
"""
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import time
from typing import Dict
from utils.actions.base_action import BaseAction

class TableActions(BaseAction):
    """Hereda de BaseAction para aprovechar métodos helper comunes."""
    pass  # __init__ heredado de BaseAction

    def marcar_tabla_riesgos(self, tabla_xpath: str, respuestas: Dict[str, str], default: str = "No"):
        """Marca filas de tabla según el dict `respuestas`.
        Esta implementación fue migrada desde utils/elements.py (Fase 1).
        """
        driver = self.driver
        filas = driver.find_elements(By.XPATH, f"{tabla_xpath}//tbody/tr")

        for fila in filas:
            try:
                texto = fila.find_element(By.XPATH, "./td[1]").text.strip()
            except Exception:
                continue

            valor = (respuestas.get(texto, default) or default).strip().lower()
            es_si = valor == "si"
            col_xpath = ".//td[2]" if es_si else ".//td[3]"

            boton = None
            try:
                boton = fila.find_element(By.XPATH, f"{col_xpath}//input[@type='checkbox' or @type='radio']")
            except Exception:
                try:
                    boton = fila.find_element(
                        By.XPATH, f"{col_xpath}//*[@role='switch' or @aria-checked or self::button or self::div]"
                    )
                except Exception:
                    print(f"⚠️ No se pudo localizar switch para '{texto}'")
                    continue

            try:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", boton)
                driver.execute_script("arguments[0].click();", boton)
            except Exception as e:
                print(f"⚠️ No se pudo marcar {texto}: {e}")
