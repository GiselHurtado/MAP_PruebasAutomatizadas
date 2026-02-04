# utils/actions/date_actions.py
"""
STRATEGY PATTERN - Estrategia para Campos de Fecha/Hora

Esta clase implementa el patrón Strategy para manejar campos de fecha y hora:
- Input type="datetime-local"
- Inputs con máscaras de fecha en español (dd/mm/aaaa hh:mm a. m./p. m.)
- Conversión entre formatos de fecha

Forma parte del conjunto de estrategias especializadas en utils/actions/ que
son utilizadas a través del Facade Pattern en utils/elements.py.

Uso desde Page Objects (a través de la facade):
    from utils.elements import escribir_fecha
    escribir_fecha(driver, wait, "Fecha inicio", "01/12/2024 08:00 AM")
"""
from datetime import datetime
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from utils.actions.base_action import BaseAction


class DateActions(BaseAction):
    """Hereda de BaseAction para aprovechar métodos helper comunes."""
    pass  # __init__ heredado de BaseAction

    def _to_formats(self, dt_text: str):
        """Convierte datetime string a varios formatos."""
        dt = datetime.strptime(dt_text, "%d/%m/%Y %I:%M %p")
        return {
            "date": dt.strftime("%Y-%m-%d"),
            "time": dt.strftime("%H:%M"),
            "datetime-local": dt.strftime("%Y-%m-%dT%H:%M"),
            "text_ddMMyyyy_hhmm_a": dt.strftime("%d/%m/%Y %I:%M %p"),
            "text_ddMMyyyy_HHmm": dt.strftime("%d/%m/%Y %H:%M"),
        }

    def set_date_like_a_pro(self, locator, dt_text, timeout=10):
        """Establece fecha en input type=datetime-local o similar."""
        driver = self.driver
        el = WebDriverWait(driver, timeout).until(EC.visibility_of_element_located(locator))
        input_type  = (el.get_attribute("type") or "").lower()
        placeholder = (el.get_attribute("placeholder") or "").lower()

        # --- 1) Caso nativo: datetime-local ---
        if input_type == "datetime-local":
            fmts = self._to_formats(dt_text)
            iso = fmts["datetime-local"]

            min_attr = (el.get_attribute("min") or "").strip()
            if min_attr and iso < min_attr:
                iso = min_attr

            driver.execute_script("""
                const el = arguments[0], val = arguments[1];
                el.focus();
                const proto = Object.getPrototypeOf(el);
                const desc  = Object.getOwnPropertyDescriptor(proto, 'value');
                if (desc && desc.set) {
                    desc.set.call(el, '');
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    desc.set.call(el, val);
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                } else {
                    el.value = val;
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                }
            """, el, iso)

            el.send_keys(Keys.TAB)

            WebDriverWait(driver, timeout).until(
                lambda d: (el.get_attribute("value") or "").strip() == iso
            )
            return

    def escribir_fecha(self, label: str, dt_text: str, timeout: int = 10):
        """Escribe una fecha en el input etiquetado por label."""
        driver = self.driver
        wait = self.wait
        
        xp = f"(//label[contains(normalize-space(.), '{label}')]/following::input[1])"
        self.set_date_like_a_pro((By.XPATH, xp), dt_text, timeout=timeout)
        
        # blur explícito en otra etiqueta del formulario
        try:
            lbl = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//label[contains(normalize-space(.), 'Lugar de trabajo')]")
            ))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", lbl)
            driver.execute_script("arguments[0].click();", lbl)
        except Exception:
            try:
                driver.execute_script("if(document.activeElement&&document.activeElement.blur){document.activeElement.blur();}")
            except Exception:
                pass

    def _type_masked_datetime_es(self, el, dt: datetime, timeout_ok=5):
        """Escribe dd/mm/aaaa hh:mm a. m./p. m. en inputs con máscara ES."""
        hour_24 = dt.hour
        am = hour_24 < 12
        hour_12 = hour_24 % 12 or 12

        dd   = f"{dt.day:02d}"
        mm   = f"{dt.month:02d}"
        yyyy = f"{dt.year:04d}"
        hh   = f"{hour_12:02d}"
        mi   = f"{dt.minute:02d}"
        suf  = "a. m." if am else "p. m."

        el.click()
        el.send_keys(Keys.CONTROL, 'a')
        el.send_keys(Keys.DELETE)
        el.send_keys(Keys.HOME)

        def slow(txt, delay=0.015):
            for ch in txt:
                el.send_keys(ch); time.sleep(delay)

        slow(dd)
        el.send_keys(Keys.ARROW_RIGHT)
        slow(mm)
        el.send_keys(Keys.ARROW_RIGHT)
        slow(yyyy)
        el.send_keys(Keys.ARROW_RIGHT)
        el.send_keys(Keys.ARROW_RIGHT)
        el.send_keys(Keys.ARROW_RIGHT)
        slow(hh)
        el.send_keys(Keys.ARROW_RIGHT)
        slow(mi)
        el.send_keys(Keys.SPACE)
        slow(suf)

        el.send_keys(Keys.TAB)
        try:
            el._parent.execute_script("if(document.activeElement&&document.activeElement.blur){document.activeElement.blur();}")
        except Exception:
            pass

        rx = re.compile(r"\b\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}\s+(a\. m\.|p\. m\.)\b", re.I)
        fin = time.time() + timeout_ok
        while time.time() < fin:
            val = (el.get_attribute("value") or "").strip()
            if rx.search(val):
                return True
            time.sleep(0.05)
        return False
