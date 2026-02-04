# utils/actions/signature_actions.py
"""
STRATEGY PATTERN - Estrategia para Campos de Firma

Esta clase implementa el patrón Strategy para manejar campos de firma digital
mediante canvas HTML5:
- Dibuja trazos en el canvas
- Busca canvas por label asociado
- Hace click en botón "Firmar" automáticamente

Forma parte del conjunto de estrategias especializadas en utils/actions/ que
son utilizadas a través del Facade Pattern en utils/elements.py.

Uso desde Page Objects (a través de la facade):
    from utils.elements import campo_firma
    campo_firma(driver, wait, "Firma", trazos=3)
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
import time
from utils.actions.base_action import BaseAction

class SignatureActions(BaseAction):
    """Hereda de BaseAction para aprovechar métodos helper comunes."""
    pass  # __init__ heredado de BaseAction

    def _label_exact_local(self, etiqueta: str) -> str:
        return f"//label[normalize-space(translate(., '*', ''))='{etiqueta}']"

    def _buscar_canvas_firma(self, etiqueta: str | None):
        """Intenta encontrar el <canvas> de firma (mismos heurísticos que antes)."""
        candidatos = []

        if etiqueta:
            lbl = (
                f"({self._label_exact_local(etiqueta)}"
                f" | //span[normalize-space(translate(., '*',''))='{etiqueta}'])[1]"
            )
            candidatos.append(f"{lbl}/following::canvas[1]")
            candidatos.append(
                f"{lbl}/ancestor::div[contains(@class,'signature-field') or "
                f"contains(@class,'signature-container')][1]//canvas"
            )

        candidatos.append("//div[contains(@class,'signature-field') or contains(@class,'signature-container')]//canvas")
        candidatos.append("(//canvas)[last()]")

        last_exc = None
        for xp in candidatos:
            try:
                el = self.wait.until(EC.presence_of_element_located((By.XPATH, xp)))
                return el
            except Exception as e:
                last_exc = e
                continue

        raise last_exc if last_exc else TimeoutException("No se encontró ningún canvas de firma")

    def campo_firma(self, etiqueta: str | None = "Firma", *, trazos: int = 1, click_boton_firmar: bool = True):
        """Dibuja en el canvas y pulsa 'Firmar' si procede."""
        driver = self.driver
        canvas = self._buscar_canvas_firma(etiqueta)

        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", canvas)
        time.sleep(0.2)

        try:
            w = int(canvas.get_attribute("width") or 600)
            h = int(canvas.get_attribute("height") or 300)
        except Exception:
            rect = driver.execute_script("return arguments[0].getBoundingClientRect();", canvas)
            w = int(rect.get("width", 600))
            h = int(rect.get("height", 300))

        act = ActionChains(driver)
        start_x = max(10, int(w * 0.15))
        y = max(10, int(h * 0.5))
        for i in range(trazos):
            dx = max(10, int(w * 0.20))
            offset_x = start_x + i * 12
            try:
                act.move_to_element_with_offset(canvas, offset_x, y)\
                   .click_and_hold()\
                   .move_by_offset(dx, 0)\
                   .release()\
                   .pause(0.05)
            except Exception:
                act.move_to_element_with_offset(canvas, offset_x, y).click().pause(0.02).click()
        act.perform()
        time.sleep(0.15)

        if click_boton_firmar:
            btn_xpaths = [
                ".//button[contains(@class,'btn-green') and contains(normalize-space(.), 'Firmar')]",
                ".//button[contains(@class,'btn-green')]",
            ]
            cont = canvas
            for _ in range(4):
                try:
                    cont = cont.find_element(By.XPATH, "./..")
                except Exception:
                    break
            for xp in btn_xpaths:
                try:
                    btn = cont.find_element(By.XPATH, xp)
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                    try:
                        btn.click()
                    except Exception:
                        driver.execute_script("arguments[0].click();", btn)
                    print("✅ Click en botón 'Firmar'")
                    break
                except Exception:
                    continue
