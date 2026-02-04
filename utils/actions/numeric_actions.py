# utils/actions/numeric_actions.py
"""
STRATEGY PATTERN - Estrategia para Campos Numéricos

Esta clase implementa el patrón Strategy para manejar campos numéricos:
- Input type="number"
- Inputs de texto que solo aceptan números
- Validación básica de valores

Forma parte del conjunto de estrategias especializadas en utils/actions/ que
son utilizadas a través del Facade Pattern en utils/elements.py.

Uso desde Page Objects (a través de la facade):
    from utils.elements import campo_numerico
    campo_numerico(driver, wait, "Cantidad", 5)
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from utils.actions.base_action import BaseAction


class NumericActions(BaseAction):
    """Hereda de BaseAction para aprovechar métodos helper comunes."""
    pass  # __init__ heredado de BaseAction

    def campo_numerico(self, etiqueta: str, valor):
        """Escribe un valor numérico en el input asociado al label."""
        driver = self.driver
        wait = self.wait
        
        svalor = str(valor).strip()
        if svalor == "":
            raise ValueError(f"Valor vacío para campo numérico '{etiqueta}'")

        label_xpath = f"(//label[contains(normalize-space(.), '{etiqueta}')])[1]"
        candidates = [
            f"{label_xpath}/following::input[not(@type='hidden')][1]",
            f"{label_xpath}/ancestor::tr[1]//input[not(@type='hidden')]",
            f"{label_xpath}/ancestor::*[self::div or self::td][1]//input[not(@type='hidden')]",
        ]

        last_exc = None
        for xp in candidates:
            try:
                el = wait.until(EC.element_to_be_clickable((By.XPATH, xp)))
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                el.click()
                el.clear()
                el.send_keys(Keys.CONTROL, "a")
                el.send_keys(Keys.DELETE)
                el.send_keys(svalor)
                return el
            except Exception as e:
                last_exc = e
                continue

        print(f"⚠️ No se pudo ubicar input numérico para label '{etiqueta}'. Último error: {last_exc}")
        raise last_exc if last_exc else TimeoutException(f"No se encontró input numérico para '{etiqueta}'")
