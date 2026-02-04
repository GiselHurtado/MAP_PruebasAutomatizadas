# utils/actions/text_actions.py
"""
STRATEGY PATTERN - Estrategia para Campos de Texto

Esta clase implementa el patrón Strategy para manejar todos los tipos de campos
de entrada de texto:
- Inputs de texto (<input type="text">)
- Textareas (<textarea>)
- Campos condicionales (que aparecen según respuesta de otro campo)

Forma parte del conjunto de estrategias especializadas en utils/actions/ que
son utilizadas a través del Facade Pattern en utils/elements.py.

Uso desde Page Objects (a través de la facade):
    from utils.elements import campo_texto_por_label
    campo_texto_por_label(driver, wait, "Descripción", "Trabajo de mantenimiento")
"""
from typing import Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from utils.actions.base_action import BaseAction


def _label_exact(etiqueta: str) -> str:
    return f"//label[normalize-space(translate(., '*', ''))='{etiqueta}']"


class TextActions(BaseAction):
    """Hereda de BaseAction para aprovechar métodos helper comunes."""
    pass  # __init__ heredado de BaseAction

    def campo_texto_por_label(self, etiqueta: str, texto: str):
        """Escribe en el input/textarea asociado al label exacto."""
        driver = self.driver
        wait = self.wait
        
        label_xpath = f"(//label[contains(normalize-space(.), '{etiqueta}')])[1]"
        wait.until(EC.presence_of_element_located((By.XPATH, label_xpath)))

        candidates = [
            f"{label_xpath}/following::input[not(@type='hidden')][1]",
            f"{label_xpath}/ancestor::tr[1]//input[not(@type='hidden')]",
            f"{label_xpath}/ancestor::*[self::div or self::td][1]//input[not(@type='hidden')]",
            f"{label_xpath}/following::textarea[1]",
            f"{label_xpath}/ancestor::tr[1]//textarea",
        ]

        last_exc: Optional[Exception] = None
        for xp in candidates:
            try:
                el = wait.until(EC.element_to_be_clickable((By.XPATH, xp)))
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                el.clear()
                el.send_keys(texto)
                return el
            except Exception as e:
                last_exc = e
                continue

        print(f"⚠️ No se pudo ubicar input para label '{etiqueta}'. Último error: {last_exc}")
        if last_exc:
            raise last_exc
        raise TimeoutException(f"No se encontró control para '{etiqueta}'")

    def campo_texto_por_label_index(self, etiqueta: str, texto: str, index: int = 1):
        """Escribe en el N-ésimo input/textarea asociado al label indicado."""
        driver = self.driver
        wait = self.wait
        
        label_xpath = f"(//label[normalize-space(translate(., '*', ''))='{etiqueta}'])[{index}]"
        candidates = [
            f"{label_xpath}/following::input[not(@type='hidden')][1]",
            f"{label_xpath}/ancestor::tr[1]//input[not(@type='hidden')]",
            f"{label_xpath}/ancestor::*[self::div or self::td][1]//input[not(@type='hidden')]",
            f"{label_xpath}/following::textarea[1]",
            f"{label_xpath}/ancestor::tr[1]//textarea",
        ]
        last_exc = None
        for xp in candidates:
            try:
                el = wait.until(EC.element_to_be_clickable((By.XPATH, xp)))
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                el.clear()
                el.send_keys(texto)
                return el
            except Exception as e:
                last_exc = e
                continue
        raise last_exc if last_exc else TimeoutException(f"No se encontró control para '{etiqueta}' (index={index})")

    def assert_input_value_by_label_index(self, etiqueta: str, expected: str, index: int = 1):
        """Asserta el valor del N-ésimo input/textarea asociado al label indicado."""
        wait = self.wait
        
        label_xpath = f"(//label[normalize-space(translate(., '*', ''))='{etiqueta}'])[{index}]"
        try:
            el = wait.until(EC.presence_of_element_located(
                (By.XPATH, f"{label_xpath}/following::input[not(@type='hidden')][1]")))
        except TimeoutException:
            el = wait.until(EC.presence_of_element_located(
                (By.XPATH, f"{label_xpath}/following::textarea[1]")))
        val = (el.get_attribute("value") or "").strip()
        assert val == expected.strip(), f"Esperaba '{expected}' en '{etiqueta}' index {index}, obtuve '{val}'"

    def campo_texto_por_label_despues_de(self, base_label: str, target_label: str, texto: str):
        """Escribe en el 'target_label' que aparece DESPUÉS del 'base_label'."""
        driver = self.driver
        wait = self.wait
        
        # aseguramos que existe el base
        wait.until(EC.presence_of_element_located((By.XPATH, _label_exact(base_label))))
        # target que viene después del base
        tlabel = f"({_label_exact(target_label)}[preceding::{_label_exact(base_label)}])[1]"
        candidates = [
            f"{tlabel}/following::input[not(@type='hidden')][1]",
            f"{tlabel}/ancestor::tr[1]//input[not(@type='hidden')]",
            f"{tlabel}/ancestor::*[self::div or self::td][1]//input[not(@type='hidden')]",
            f"{tlabel}/following::textarea[1]",
            f"{tlabel}/ancestor::tr[1]//textarea",
        ]
        last_exc: Optional[Exception] = None
        for xp in candidates:
            try:
                el = wait.until(EC.element_to_be_clickable((By.XPATH, xp)))
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                el.clear()
                el.send_keys(texto)
                return el
            except Exception as e:
                last_exc = e
                continue
        raise last_exc if last_exc else TimeoutException(
            f"No se encontró input/textarea para '{target_label}' después de '{base_label}'"
        )

    def campo_cuales_para(self, base_label: str, valor: str, timeout: int = 10):
        """Escribe en el input '¿Cuales?/¿Cuáles?' que aparece DESPUÉS del label base."""
        driver = self.driver
        wait = self.wait
        
        # label base (exacto, ignorando '*') y su contenedor FormControl
        base_label_xpath = f"//label[normalize-space(translate(., '*', ''))='{base_label}']"
        base_cont_xpath = f"{base_label_xpath}/ancestor::div[contains(@class,'MuiFormControl-root')][1]"
        base_cont = wait.until(EC.presence_of_element_located((By.XPATH, base_cont_xpath)))

        # input '¿Cuales?/¿Cuáles?' que aparezca DESPUÉS del contenedor base
        cuales_xpath = (
            f"({base_cont_xpath}/following::div[contains(@class,'MuiFormControl-root')]"
            f"//input[(@placeholder='¿Cuales?' or @placeholder='¿Cuáles?') and not(@type='hidden')])[1]"
        )

        # a veces es textarea, añadimos fallback
        cuales_textarea_xpath = (
            f"({base_cont_xpath}/following::div[contains(@class,'MuiFormControl-root')]"
            f"//textarea[(@placeholder='¿Cuales?' or @placeholder='¿Cuáles?')])[1]"
        )

        target = None
        last_exc = None
        for xp in (cuales_xpath, cuales_textarea_xpath):
            try:
                target = wait.until(EC.element_to_be_clickable((By.XPATH, xp)))
                break
            except Exception as e:
                last_exc = e
                continue

        if target is None:
            raise TimeoutException(f"No encontré '¿Cuales?/¿Cuáles?' después de '{base_label}'. Último error: {last_exc}")

        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", target)
        try:
            target.click()
        except Exception:
            driver.execute_script("arguments[0].click();", target)

        # limpiar y escribir
        try:
            target.clear()
        except Exception:
            pass
        target.send_keys(Keys.CONTROL, "a")
        target.send_keys(Keys.DELETE)
        target.send_keys(valor)
        return target
