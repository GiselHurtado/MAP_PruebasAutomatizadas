# utils/actions/base_action.py
"""
BaseAction - Clase Base para Estrategias de Interacción

Clase base abstracta que define la interfaz común para todas las action classes
del patrón Strategy.

Proporciona:
- Inicialización común (driver, wait)
- Métodos helper comunes
- Contrato/interfaz para subclases

Todas las action classes (SelectActions, TextActions, etc.) deben heredar de esta clase.

Uso:
    from utils.actions.base_action import BaseAction

    class CustomActions(BaseAction):
        def execute_custom_action(self, elemento):
            # Tiene acceso a self.driver y self.wait
            el = self.find_element(By.ID, elemento)
            el.click()
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from typing import Tuple


class BaseAction:
    """
    Clase base abstracta para todas las action classes.

    Proporciona infraestructura común y define la interfaz que todas
    las estrategias deben implementar.
    """

    def __init__(self, driver, wait):
        """
        Inicialización común para todas las action classes.

        Args:
            driver: WebDriver de Selenium
            wait: WebDriverWait configurado
        """
        self.driver = driver
        self.wait = wait

    def find_element(self, by: By, value: str, timeout: int = None):
        """
        Encuentra un elemento con espera explícita.

        Args:
            by: Estrategia de búsqueda (By.ID, By.XPATH, etc.)
            value: Valor a buscar
            timeout: Timeout opcional (usa self.wait._timeout si no se especifica)

        Returns:
            WebElement encontrado

        Raises:
            TimeoutException: Si el elemento no se encuentra en el tiempo especificado
        """
        if timeout and timeout != self.wait._timeout:
            from selenium.webdriver.support.ui import WebDriverWait
            wait = WebDriverWait(self.driver, timeout)
        else:
            wait = self.wait

        return wait.until(EC.presence_of_element_located((by, value)))

    def find_clickable_element(self, by: By, value: str, timeout: int = None):
        """
        Encuentra un elemento clickeable con espera explícita.

        Args:
            by: Estrategia de búsqueda (By.ID, By.XPATH, etc.)
            value: Valor a buscar
            timeout: Timeout opcional

        Returns:
            WebElement clickeable

        Raises:
            TimeoutException: Si el elemento no es clickeable en el tiempo especificado
        """
        if timeout and timeout != self.wait._timeout:
            from selenium.webdriver.support.ui import WebDriverWait
            wait = WebDriverWait(self.driver, timeout)
        else:
            wait = self.wait

        return wait.until(EC.element_to_be_clickable((by, value)))

    def scroll_into_view(self, element):
        """
        Hace scroll para que el elemento sea visible en el viewport.

        Args:
            element: WebElement a hacer visible
        """
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)

    def safe_click(self, element):
        """
        Hace click en un elemento con fallback a JavaScript si falla el click normal.

        Args:
            element: WebElement a clickear
        """
        try:
            element.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", element)

    def safe_send_keys(self, element, text: str):
        """
        Envía texto a un elemento limpiándolo primero.

        Args:
            element: WebElement input/textarea
            text: Texto a enviar
        """
        from selenium.webdriver.common.keys import Keys

        try:
            element.clear()
        except Exception:
            # Fallback: seleccionar todo y borrar
            element.send_keys(Keys.CONTROL, "a")
            element.send_keys(Keys.DELETE)

        element.send_keys(text)

    def get_label_xpath(self, etiqueta: str, exact: bool = False) -> str:
        """
        Genera XPath para encontrar un label por texto.

        Args:
            etiqueta: Texto del label a buscar
            exact: Si True, busca match exacto; si False, usa contains()

        Returns:
            XPath string
        """
        if exact:
            return f"//label[normalize-space(translate(., '*', ''))='{etiqueta}']"
        else:
            return f"//label[contains(normalize-space(.), '{etiqueta}')]"

    def find_input_by_label(self, etiqueta: str) -> Tuple[str, str]:
        """
        Genera XPaths candidatos para encontrar input asociado a un label.

        Args:
            etiqueta: Texto del label

        Returns:
            Tupla de (label_xpath, input_xpath_candidates)
        """
        label_xpath = self.get_label_xpath(etiqueta)

        candidates = [
            f"{label_xpath}/following::input[not(@type='hidden')][1]",
            f"{label_xpath}/ancestor::tr[1]//input[not(@type='hidden')]",
            f"{label_xpath}/ancestor::*[self::div or self::td][1]//input[not(@type='hidden')]",
            f"{label_xpath}/following::textarea[1]",
        ]

        return label_xpath, candidates
