# utils/elements.py
"""
FACADE PATTERN - Interfaz Simplificada para Interacciones con Elementos Web

Este módulo implementa el patrón de diseño **Facade** (Fachada), proporcionando una API
simplificada y unificada para interactuar con elementos web en las pruebas de Selenium.

## Arquitectura

La fachada oculta la complejidad de 7 clases especializadas (Strategy Pattern) que
manejan diferentes tipos de campos:

    Page Objects (F1aPermisoTrabajoPage, etc.)
          ↓ (usa funciones públicas)
    elements.py (FACADE) ← Este módulo
          ↓ (delega a)
    Action Classes (STRATEGIES):
        - SelectActions      → dropdowns, autocomplete, chips
        - TextActions        → inputs de texto, textareas
        - DateActions        → campos de fecha con máscaras
        - NumericActions     → campos numéricos
        - SignatureActions   → canvas de firma
        - TableActions       → tablas interactivas (F7n)
        - FileActions        → subida de archivos


## Cómo Agregar Nuevas Interacciones

1. Crear una nueva action class en `utils/actions/` (ej: `VideoActions`)
2. Importarla aquí: `from utils.actions.video_actions import VideoActions`
3. Crear una función wrapper facade:
   ```python
   def reproducir_video(driver, wait, etiqueta: str):
       '''Facade wrapper: delega en VideoActions.reproducir_video.'''
       va = VideoActions(driver, wait)
       return va.reproducir_video(etiqueta)
   ```
4. Los Page Objects ya pueden usar `reproducir_video()` directamente

## Nota Importante

Este módulo NO debe contener lógica de negocio compleja. Solo debe:
- Instanciar la action class apropiada (Factory Pattern implícito)
- Delegar la llamada
- Retornar el resultado

La lógica real vive en `utils/actions/*.py`.
"""
import time
from typing import Dict, Optional, List

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime
import re
from selenium.common.exceptions import ElementClickInterceptedException
from utils.actions.table_actions import TableActions
from utils.actions.signature_actions import SignatureActions
from utils.actions.select_actions import SelectActions
from utils.actions.file_actions import FileActions
from utils.actions.text_actions import TextActions
from utils.actions.numeric_actions import NumericActions
from utils.actions.date_actions import DateActions


# =========================
# XPaths de labels (robusto)
# =========================

def _label_exact(etiqueta: str) -> str:
    """Label EXACTO ignorando asteriscos."""
    return f"//label[normalize-space(translate(., '*', ''))='{etiqueta}']"
def _label_xpath_preciso(etiqueta: str) -> str:
    """
    Devuelve un XPath que prioriza el label EXACTO (ignorando '*')
    y como fallback usa contains(...). Evita confundir:
      - 'Anclaje' con 'Punto de Anclaje'
      - 'Otros' con 'Otros conectores'
    """
    normalized = etiqueta.strip().lower()
    exacto = f"//label[normalize-space(translate(., '*', ''))='{etiqueta}']"

    if normalized == "anclaje":
        contains = (
            f"//label[contains(normalize-space(.), '{etiqueta}') and "
            f"not(contains(normalize-space(.), 'Punto de'))]"
        )
    elif normalized == "otros":
        # Evita 'Otros conectores'
        contains = (
            f"//label[contains(normalize-space(.), '{etiqueta}') and "
            f"not(contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'conectores'))]"
        )
    else:
        contains = f"//label[contains(normalize-space(.), '{etiqueta}')]"

    return f"({exacto} | {contains})[1]"


# ============================
# Autocomplete / chips (MUI)
# ============================

def _find_option_by_text(driver, texto: str, timeout: float = 5.0):
    """Facade wrapper: delega a SelectActions._find_option_by_text."""
    sa = SelectActions(driver, WebDriverWait(driver, 5))
    return sa._find_option_by_text(texto, timeout=timeout)

def _chips_actuales(cont):
    """Facade wrapper: delega a SelectActions._chips_actuales."""
    sa = SelectActions(None, None)
    return sa._chips_actuales(cont)

def _ensure_focus_on_input(driver, wait, etiqueta: str):
    """Facade wrapper: delega a SelectActions._ensure_focus_on_input."""
    sa = SelectActions(driver, wait)
    return sa._ensure_focus_on_input(etiqueta)

def seleccion_multiple(driver, wait, etiqueta: str, opciones: List[str] | str, delay_typing=0.10):
    """Facade wrapper: delega en SelectActions.seleccion_multiple."""
    sa = SelectActions(driver, wait)
    return sa.seleccion_multiple(etiqueta, opciones, delay_typing=delay_typing)

def assert_chips(driver, wait, etiqueta: str, esperados: List[str]):
    """Aserción útil para los tests."""
    sa = SelectActions(driver, wait)
    return sa.assert_chips(etiqueta, esperados)

def seleccion_simple(driver, wait, etiqueta, texto, opcion=1):
    """Facade wrapper: delega en SelectActions.seleccion_simple."""
    sa = SelectActions(driver, wait)
    return sa.seleccion_simple(etiqueta, texto, opcion=opcion)

def campo_endpoint(
    driver, wait: WebDriverWait,
    xpath_boton_lupa: str,
    label_dropdown: str, opcion_texto: str,
    label_input: str = None, valor_input: str = None,
    opcion: int = 1,
    delay: float = 2.0
):
    """Facade wrapper: delega en SelectActions.campo_endpoint."""
    sa = SelectActions(driver, wait)
    return sa.campo_endpoint(xpath_boton_lupa, label_dropdown, opcion_texto, label_input=label_input, valor_input=valor_input, opcion=opcion, delay=delay)


# =========================
# Helpers básicos de elemento
# =========================

def click_xpath(driver, wait, xpath: str, timeout: int = 15):
    locator = (By.XPATH, xpath)
    el = wait.until(EC.element_to_be_clickable(locator))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    try:
        el.click()
        return
    except ElementClickInterceptedException:
        # 1) Oculta overlays
        _ocultar_overlays_notificaciones(driver)
        # 2) Espera a que desaparezcan notificaciones visibles
        try:
            wait.until(EC.invisibility_of_element_located(
                (By.CSS_SELECTOR, ".push-notification-container.pushing")
            ))
        except Exception:
            pass
        # 3) Reintenta click normal, si falla, click por JS
        try:
            el = wait.until(EC.element_to_be_clickable(locator))
            el.click()
            return
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", el)
            return

def escribir_xpath(driver, wait: WebDriverWait, xpath: str, texto: str):
    elem = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", elem)
    elem.clear()
    elem.send_keys(texto)
    return elem


# =========================
# Esperas “inteligentes”
# =========================

def esperar_notificaciones_y_cargas(driver, wait: WebDriverWait, timeout: int = 20):
    fin = time.time() + timeout
    while time.time() < fin:
        try:
            pushing = driver.find_elements(By.CLASS_NAME, "pushing")
            toasts = driver.find_elements(By.CLASS_NAME, "push-notification-container")
            spinners = driver.find_elements(
                By.CSS_SELECTOR,
                ".MuiBackdrop-root, .loading, .spinner, .MuiCircularProgress-root"
            )
            if not pushing and not spinners:
                return
        except Exception:
            pass
        time.sleep(0.3)

def esperar_notificacion(driver, timeout: int = 20):
    w = WebDriverWait(driver, timeout)
    w.until(EC.presence_of_element_located((By.CLASS_NAME, "push-notification-container")))
    w.until_not(EC.presence_of_element_located((By.CLASS_NAME, "pushing")))

def esperar_formulario_por_label(driver, wait: WebDriverWait, etiqueta: str, timeout_extra: int = 0):
    if timeout_extra:
        wait._timeout = max(wait._timeout, wait._timeout + timeout_extra)
    wait.until(EC.presence_of_element_located(
        (By.XPATH, f"//label[contains(normalize-space(.), '{etiqueta}')]")
    ))


# =========================
# Inputs por label
# =========================

def campo_texto_por_label(driver, wait: WebDriverWait, etiqueta: str, texto: str):
    """Facade wrapper: delega en TextActions.campo_texto_por_label."""
    ta = TextActions(driver, wait)
    return ta.campo_texto_por_label(etiqueta, texto)

def campo_texto_por_label_index(driver, wait, etiqueta: str, texto: str, index: int = 1):
    """Facade wrapper: delega en TextActions.campo_texto_por_label_index."""
    ta = TextActions(driver, wait)
    return ta.campo_texto_por_label_index(etiqueta, texto, index=index)

def assert_input_value_by_label_index(driver, wait, etiqueta: str, expected: str, index: int = 1):
    """Facade wrapper: delega en TextActions.assert_input_value_by_label_index."""
    ta = TextActions(driver, wait)
    return ta.assert_input_value_by_label_index(etiqueta, expected, index=index)

def campo_texto_por_label_despues_de(driver, wait, base_label: str, target_label: str, texto: str):
    """Facade wrapper: delega en TextActions.campo_texto_por_label_despues_de."""
    ta = TextActions(driver, wait)
    return ta.campo_texto_por_label_despues_de(base_label, target_label, texto)


# =========================
# Otros campos comunes
# =========================

def escribir_fecha(driver, wait, label: str, dt_text: str, timeout: int = 10):
    """Wrapper delegating to DateActions."""
    actions = DateActions(driver, wait)
    actions.escribir_fecha(label, dt_text, timeout=timeout)

def _to_formats(dt_text):
    """Wrapper delegating to DateActions."""
    actions = DateActions(None, None)  # no needed for this method
    return actions._to_formats(dt_text)

def set_date_like_a_pro(driver, locator, dt_text, timeout=10):
    """Wrapper delegating to DateActions."""
    actions = DateActions(driver, None)
    actions.set_date_like_a_pro(locator, dt_text, timeout=timeout)




def campo_numerico(driver, wait, etiqueta: str, valor):
    """Facade wrapper: delega en NumericActions.campo_numerico."""
    na = NumericActions(driver, wait)
    return na.campo_numerico(etiqueta, valor)


# =========================
# Envío / navegación
# =========================

def enviar_y_confirmar(driver, wait: WebDriverWait):
    botones = wait.until(
        EC.presence_of_all_elements_located((By.XPATH, "//button[contains(@class,'btn-green')]"))
    )
    if not botones:
        raise Exception("❌ No se encontró botón verde (enviar).")
    boton_enviar = botones[-1]
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", boton_enviar)
    boton_enviar.click()
    print("✅ Formulario enviado")

    try:
        boton_confirmar = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class,'btn-blue')]"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", boton_confirmar)
        boton_confirmar.click()
        print("✅ Confirmación enviada")
    except TimeoutException:
        print("⚠️ No se encontró botón azul de confirmación (posible confirmación automática).")

def abrir_siguiente_formulario(driver, wait: WebDriverWait, xpath_tarea: str, descripcion: str = "Formulario"):
    esperar_notificacion(driver)
    print("🔔 Notificación cerrada")
    elem = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_tarea)))
    driver.execute_script("arguments[0].click();", elem)
    print(f"✅ Se abrió {descripcion}")

def abrir_tarea_por_texto(driver, wait: WebDriverWait, texto_formulario: str, descripcion: str | None = None):
    esperar_notificaciones_y_cargas(driver, wait, timeout=20)
    xpaths = [
        f"//div[contains(@class,'task-item')]//span[contains(normalize-space(.), \"{texto_formulario}\")]",
        f"//div[contains(@class,'form') and contains(normalize-space(.), \"{texto_formulario}\")]",
        f"//*[@id='task-info']//span[contains(normalize-space(.), \"{texto_formulario}\")]",
    ]
    last_exc: Optional[Exception] = None
    for xp in xpaths:
        try:
            el = wait.until(EC.element_to_be_clickable((By.XPATH, xp)))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            driver.execute_script("arguments[0].click();", el)
            print(f"✅ Se abrió {descripcion or texto_formulario}")
            return
        except Exception as e:
            last_exc = e
            continue
    print(f"⚠️ No se pudo abrir la tarea por texto: '{texto_formulario}'. Último error: {last_exc}")
    if last_exc:
        raise last_exc
    raise TimeoutException(f"No se encontró tarea con texto '{texto_formulario}'")


# =========================
# Tabla de riesgos (F7n)
# =========================

def marcar_tabla_riesgos(
    driver,
    wait: WebDriverWait,
    tabla_xpath: str,
    respuestas: Dict[str, str],
    default: str = "No"
):
    """Facade wrapper: delega en TableActions.marcar_tabla_riesgos.

    Mantiene la firma original para compatibilidad con Pages.
    """
    ta = TableActions(driver, wait)
    return ta.marcar_tabla_riesgos(tabla_xpath, respuestas, default=default)

def esperar_label_flexible(driver, etiqueta: str, timeout: float = 12.0):
    """
    Espera a que exista un control identificado por 'etiqueta' aunque el render sea perezoso.
    Intenta:
      - label EXACTO (ignorando '*')
      - label contains(...)
      - placeholder/aria-label con el texto
    Hace pequeños scrolls y TAB para forzar montaje.
    """
    fin = time.time() + timeout
    xp_exacto = f"//label[normalize-space(translate(., '*', ''))='{etiqueta}']"
    if etiqueta.strip().lower() == "anclaje":
        xp_contains = ("//label[contains(normalize-space(.), 'Anclaje') and "
                       "not(contains(normalize-space(.), 'Punto de'))]")
    else:
        xp_contains = f"//label[contains(normalize-space(.), '{etiqueta}')]"

    xp_input = (
        f"//input[@placeholder='{etiqueta}' or @aria-label='{etiqueta}']"
        f"|//div[@placeholder='{etiqueta}']"
    )

    while time.time() < fin:
        try:
            els = driver.find_elements(By.XPATH, xp_exacto) or driver.find_elements(By.XPATH, xp_contains)
            if not els:
                els = driver.find_elements(By.XPATH, xp_input)
            if els:
                return els[0]
        except Exception:
            pass

        # forzar montaje
        try:
            driver.switch_to.active_element.send_keys(Keys.TAB)
        except Exception:
            pass
        driver.execute_script("window.scrollBy(0, 220);")
        time.sleep(0.4)

    raise TimeoutException(f"No apareció el campo con etiqueta '{etiqueta}' dentro del tiempo.")

def campo_cuales_para(driver, wait, base_label: str, valor: str, timeout: int = 10):
    """Facade wrapper: delega en TextActions.campo_cuales_para."""
    ta = TextActions(driver, wait)
    return ta.campo_cuales_para(base_label, valor, timeout=timeout)

def _buscar_canvas_firma(driver, wait, etiqueta: str | None):
    """Wrapper: delega en SignatureActions._buscar_canvas_firma."""
    sa = SignatureActions(driver, wait)
    return sa._buscar_canvas_firma(etiqueta)


def campo_firma(
    driver,
    wait,
    etiqueta: str | None = "Firma",
    *,
    trazos: int = 1,
    click_boton_firmar: bool = True
):
    """Wrapper: delega en SignatureActions.campo_firma (firma en canvas)."""
    sa = SignatureActions(driver, wait)
    return sa.campo_firma(etiqueta=etiqueta, trazos=trazos, click_boton_firmar=click_boton_firmar)


def subir_archivo(driver, wait, etiqueta_boton: str, ruta_archivo: str, timeout: int = 30):
    """Facade wrapper: delega en FileActions.subir_archivo.

    Mantiene la firma original para compatibilidad con Pages.
    """
    fa = FileActions(driver, wait)
    return fa.subir_archivo(etiqueta_boton, ruta_archivo, timeout=timeout)


def _buscar_input_file_en_dom(driver):
    """Facade wrapper: delega en FileActions._buscar_input_file_en_dom."""
    fa = FileActions(driver, None)
    return fa._buscar_input_file_en_dom()


def subir_archivo_por_boton(driver, wait, etiqueta_boton: str, ruta_archivo: str, timeout: int = 6):
    """Facade wrapper: delega en FileActions.subir_archivo_por_boton."""
    fa = FileActions(driver, wait)
    return fa.subir_archivo_por_boton(etiqueta_boton, ruta_archivo, timeout=timeout)


def _ocultar_overlays_notificaciones(driver):
    # Oculta overlays molestos (notificaciones, popovers, etc.)
    driver.execute_script("""
        const sels = [
            '.push-notification-container.pushing',
            '.MuiBackdrop-root','.MuiModal-root','.MuiPopover-root','.MuiMenu-root',
            '[role="dialog"]','[role="menu"]','.popup','.dialog'
        ];
        document.querySelectorAll(sels.join(',')).forEach(el => { try { el.style.display='none'; } catch(_){} });
        if (document.activeElement && document.activeElement.blur) { document.activeElement.blur(); }
        window.dispatchEvent(new Event('resize'));
    """)

def _type_masked_datetime_es(el, dt: datetime, timeout_ok=5):
    """
    Escribe dd/mm/aaaa hh:mm a. m./p. m. en inputs con máscara ES.
    Controla el caret con flechas para saltar separadores y fuerza blur.
    """
    hour_24 = dt.hour
    am = hour_24 < 12
    hour_12 = hour_24 % 12 or 12

    dd   = f"{dt.day:02d}"
    mm   = f"{dt.month:02d}"
    yyyy = f"{dt.year:04d}"
    hh   = f"{hour_12:02d}"
    mi   = f"{dt.minute:02d}"
    suf  = "a. m." if am else "p. m."

    # limpiar y llevar caret al inicio
    el.click()
    el.send_keys(Keys.CONTROL, 'a')
    el.send_keys(Keys.DELETE)
    el.send_keys(Keys.HOME)

    def slow(txt, delay=0.015):
        for ch in txt:
            el.send_keys(ch); time.sleep(delay)

    # dd
    slow(dd)
    el.send_keys(Keys.ARROW_RIGHT)  # salta '/'
    # mm
    slow(mm)
    el.send_keys(Keys.ARROW_RIGHT)  # salta '/'
    # yyyy
    slow(yyyy)
    # algunas máscaras requieren 3 flechas hasta hora (espacio + separadores invisibles)
    el.send_keys(Keys.ARROW_RIGHT)
    el.send_keys(Keys.ARROW_RIGHT)
    el.send_keys(Keys.ARROW_RIGHT)
    # hh
    slow(hh)
    el.send_keys(Keys.ARROW_RIGHT)  # salta ':'
    # mm
    slow(mi)
    # sufijo
    el.send_keys(Keys.SPACE)
    slow(suf)


    rx = re.compile(r"\b\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}\s+(a\. m\.|p\. m\.)\b", re.I)
    fin = time.time() + timeout_ok
    while time.time() < fin:
        val = (el.get_attribute("value") or "").strip()
        if rx.search(val):
            return True
        time.sleep(0.05)
    return False
