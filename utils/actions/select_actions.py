# utils/actions/select_actions.py
"""
STRATEGY PATTERN - Estrategia para Campos de Selección

Esta clase implementa el patrón Strategy para manejar todos los tipos de campos
de selección en la aplicación:
- Dropdowns nativos (<select>)
- Autocomplete de Material-UI
- Campos con chips múltiples
- Campos endpoint (con botón lupa)

Forma parte del conjunto de estrategias especializadas en utils/actions/ que
son utilizadas a través del Facade Pattern en utils/elements.py.

Uso desde Page Objects (a través de la facade):
    from utils.elements import seleccion_simple, seleccion_multiple
    seleccion_simple(driver, wait, "Empresa", "IBISA")
    seleccion_multiple(driver, wait, "Tags", ["Tag1", "Tag2"])
"""
from typing import List, Optional
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from utils.actions.base_action import BaseAction


def _label_exact(etiqueta: str) -> str:
    return f"//label[normalize-space(translate(., '*', ''))='{etiqueta}']"


def _label_xpath_preciso(etiqueta: str) -> str:
    normalized = etiqueta.strip().lower()
    exacto = f"//label[normalize-space(translate(., '*', ''))='{etiqueta}']"

    if normalized == "anclaje":
        contains = (
            f"//label[contains(normalize-space(.), '{etiqueta}') and "
            f"not(contains(normalize-space(.), 'Punto de'))]"
        )
    elif normalized == "otros":
        contains = (
            f"//label[contains(normalize-space(.), '{etiqueta}') and "
            f"not(contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'conectores'))]"
        )
    else:
        contains = f"//label[contains(normalize-space(.), '{etiqueta}')]"

    return f"({exacto} | {contains})[1]"


class SelectActions(BaseAction):
    """Hereda de BaseAction para aprovechar métodos helper comunes."""
    pass  # __init__ heredado de BaseAction

    # --- helpers ported from utils/elements.py ---
    def _find_option_by_text(self, texto: str, timeout: float = 5.0):
        opciones_xp = [
            f"//div[@role='listbox']//li[@role='option' and normalize-space(.)='{texto}']",
            f"//div[@role='listbox']//li[normalize-space(.)='{texto}']",
            f"//ul//li[@role='option' and normalize-space(.)='{texto}']",
            f"//ul//li[normalize-space(.)='{texto}']",
        ]
        fin = time.time() + timeout
        while time.time() < fin:
            for xp in opciones_xp:
                els = self.driver.find_elements(By.XPATH, xp)
                if els:
                    return els[0]
            time.sleep(0.15)
        return None

    def _chips_actuales(self, cont):
        try:
            return {s.text.strip()
                    for s in cont.find_elements(By.CSS_SELECTOR, "span.MuiChip-label")
                    if s.text.strip()}
        except Exception:
            return set()

    def _ensure_focus_on_input(self, etiqueta: str):
        driver = self.driver
        wait = self.wait
        try:
            driver.switch_to.active_element.send_keys(Keys.ESCAPE)
        except Exception:
            pass

        label_xpath = _label_xpath_preciso(etiqueta)
        cont = wait.until(EC.presence_of_element_located((
            By.XPATH, f"{label_xpath}/ancestor::div[contains(@class,'MuiFormControl-root')][1]"
        )))
        inp = cont.find_element(By.CSS_SELECTOR, "input[role='combobox'], input")

        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", inp)
        try:
            inp.click()
        except Exception:
            driver.execute_script("arguments[0].click();", inp)

        if driver.switch_to.active_element != inp:
            from selenium.webdriver.common.action_chains import ActionChains
            ActionChains(driver).move_to_element(inp).click().perform()
            if driver.switch_to.active_element != inp:
                raise TimeoutError(f"No se pudo enfocar el input de '{etiqueta}'")

        return cont, inp

    # --- public methods ---
    def seleccion_multiple(self, etiqueta: str, opciones: List[str] | str, delay_typing=0.10):
        if isinstance(opciones, str):
            opciones = [opciones]

        cont, inp = self._ensure_focus_on_input(etiqueta)

        for valor in opciones:
            objetivo = (valor or "").strip()
            if not objetivo:
                continue

            if objetivo in self._chips_actuales(cont):
                continue

            try:
                inp.send_keys(Keys.CONTROL, "a")
                inp.send_keys(Keys.DELETE)
            except Exception:
                pass
            for ch in objetivo:
                inp.send_keys(ch)
                time.sleep(delay_typing)
            time.sleep(0.2)

            opcion_el = self._find_option_by_text(objetivo, timeout=3.0)
            if opcion_el is not None:
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", opcion_el)
                try:
                    opcion_el.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", opcion_el)
            else:
                ok = False
                for _ in range(3):
                    inp.send_keys(Keys.ARROW_DOWN)
                    time.sleep(0.15)
                    inp.send_keys(Keys.ENTER)
                    time.sleep(0.25)
                    if objetivo in self._chips_actuales(cont):
                        ok = True
                        break
                if not ok:
                    opcion_el = self._find_option_by_text(objetivo, timeout=2.0)
                    if opcion_el is not None:
                        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", opcion_el)
                        try:
                            opcion_el.click()
                        except Exception:
                            self.driver.execute_script("arguments[0].click();", opcion_el)

            try:
                WebDriverWait(self.driver, 4).until(
                    EC.presence_of_element_located((
                        By.XPATH, f".//span[contains(@class,'MuiChip-label') and normalize-space(.)='{objetivo}']"
                    ))
                )
            except Exception:
                raise TimeoutError(
                    f"⚠️ El chip '{objetivo}' NO apareció en {etiqueta}. Probable menú sin opciones o foco en otro input."
                )

            cont, inp = self._ensure_focus_on_input(etiqueta)

    def assert_chips(self, etiqueta: str, esperados: List[str]):
        cont, _ = self._ensure_focus_on_input(etiqueta)
        reales = self._chips_actuales(cont)
        faltan = set(esperados) - reales
        if faltan:
            raise AssertionError(f"Faltan chips en {etiqueta}: {faltan}. Reales={reales}")

    def seleccion_simple(self, etiqueta: str, texto: str, opcion: int = 1):
        driver = self.driver
        wait = self.wait

        label_xpath = _label_xpath_preciso(etiqueta)
        cont = wait.until(EC.presence_of_element_located((
            By.XPATH, f"{label_xpath}/ancestor::div[contains(@class,'MuiFormControl-root')][1]"
        )))

        inp = cont.find_element(By.CSS_SELECTOR, "input[role='combobox'], input")
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", inp)
        try:
            inp.click()
        except Exception:
            driver.execute_script("arguments[0].click();", inp)

        try:
            inp.send_keys(Keys.CONTROL, "a")
            inp.send_keys(Keys.DELETE)
        except Exception:
            pass
        inp.send_keys(texto)

        time.sleep(0.15)
        inp.send_keys(Keys.ARROW_DOWN)
        time.sleep(0.10)

        opcion_elem = None
        for xp in (
            f"//div[@role='listbox']//li[@role='option' and normalize-space(.)='{texto}']",
            f"//ul//li[@role='option' and normalize-space(.)='{texto}']",
            f"//ul//li[normalize-space(.)='{texto}']",
        ):
            try:
                opcion_elem = WebDriverWait(driver, 2).until(
                    EC.visibility_of_element_located((By.XPATH, xp))
                )
                break
            except Exception:
                continue

        if opcion_elem is None:
            try:
                inp.send_keys(Keys.ENTER)
                return
            except Exception:
                try:
                    opcion_css = f"ul li:nth-child({opcion})"
                    opcion_elem = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, opcion_css)))
                except Exception:
                    raise TimeoutError(f"No se pudo seleccionar '{texto}' en {etiqueta}")

        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", opcion_elem)
        try:
            opcion_elem.click()
        except Exception:
            driver.execute_script("arguments[0].click();", opcion_elem)

    def campo_endpoint(self, xpath_boton_lupa: str, label_dropdown: str, opcion_texto: str, label_input: str = None, valor_input: str = None, opcion: int = 1, delay: float = 2.0):
        if label_input and valor_input:
            try:
                input_xpath = f"//label[contains(normalize-space(.), '{label_input}')]/following::input[1]"
                campo = self.wait.until(EC.element_to_be_clickable((By.XPATH, input_xpath)))
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", campo)
                campo.clear()
                campo.send_keys(valor_input)
                time.sleep(0.3)
            except Exception:
                print(f"⚠️ No se encontró input para {label_input}")

        try:
            boton_lupa = self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath_boton_lupa)))
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", boton_lupa)
            self.driver.execute_script("arguments[0].click();", boton_lupa)
        except Exception:
            print(f"⚠️ No se encontró lupa en {xpath_boton_lupa}")
            return

        time.sleep(delay)
        self.seleccion_simple(label_dropdown, opcion_texto, opcion=opcion)
