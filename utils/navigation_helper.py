# utils/navigation_helper.py
"""
NavigationHelper - Asistente de Navegación y Esperas

Clase especializada para manejar navegación entre vistas, esperas de tareas,
y sincronización de estados en la aplicación.

Esta clase fue extraída de FlowP1 como parte del patrón de refactorización
"Single Responsibility Principle".

Responsabilidades:
- Esperar que aparezca/desaparezca una tarea en la lista
- Volver a la vista de tareas después de enviar
- Refrescar y sincronizar estado de la UI

Uso:
    from utils.navigation_helper import NavigationHelper

    nav = NavigationHelper(driver, wait, base_url)
    nav.wait_for_task_to_appear("TEBSA - F1a", timeout=90)
    nav.wait_for_task_to_disappear("TEBSA - F10a", timeout=60)
"""
import time
from typing import Optional
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


class NavigationHelper:
    """Asistente para navegación y esperas en la aplicación."""

    def __init__(self, driver, wait, base_url: str):
        """
        Args:
            driver: WebDriver de Selenium
            wait: WebDriverWait configurado
            base_url: URL base de la aplicación (normalmente página de tareas)
        """
        self.driver = driver
        self.wait = wait
        self.base_url = base_url

    def wait_for_tasks_list(self, texto_expected: Optional[str] = None, timeout: int = 30):
        """
        Vuelve a la vista de tareas (si ya estamos ahí solo refresca) y espera estabilidad.

        Args:
            texto_expected: Si se proporciona, espera que exista ese texto clickeable
            timeout: Tiempo máximo de espera en segundos
        """
        from utils.elements import esperar_notificaciones_y_cargas

        # Asegura que estamos en /home (o página de tareas)
        try:
            self.driver.get(self.base_url)
        except Exception:
            pass

        esperar_notificaciones_y_cargas(self.driver, self.wait, timeout=timeout)

        if texto_expected:
            xp = (
                f"//div[contains(@class,'task-item')]//span[contains(normalize-space(.), \"{texto_expected}\")]"
                f"|//div[contains(@class,'form') and contains(normalize-space(.), \"{texto_expected}\")]"
                f"|//*[@id='task-info']//span[contains(normalize-space(.), \"{texto_expected}\")]"
            )
            self.wait.until(EC.element_to_be_clickable((By.XPATH, xp)))

    def wait_for_task_to_appear(self, texto: str, timeout: int = 90, refresh_cada: float = 3.0):
        """
        Refresca la home y espera a que la tarea con 'texto' sea clickeable.

        Útil para esperar que una tarea se asigne al usuario actual.

        Args:
            texto: Texto de la tarea a buscar
            timeout: Tiempo máximo de espera en segundos
            refresh_cada: Frecuencia de refresco en segundos

        Raises:
            TimeoutException: Si la tarea no aparece en el tiempo especificado
        """
        from utils.elements import esperar_notificaciones_y_cargas

        xp = (
            f"//div[contains(@class,'task-item')]//span[contains(normalize-space(.), \"{texto}\")]"
            f"|//div[contains(@class,'form') and contains(normalize-space(.), \"{texto}\")]"
            f"|//*[@id='task-info']//span[contains(normalize-space(.), \"{texto}\")]"
        )

        fin = time.time() + timeout
        while time.time() < fin:
            try:
                self.driver.get(self.base_url)
            except Exception:
                pass

            esperar_notificaciones_y_cargas(self.driver, self.wait, timeout=20)

            try:
                self.wait.until(EC.element_to_be_clickable((By.XPATH, xp)))
                return
            except Exception:
                time.sleep(refresh_cada)

        raise TimeoutException(f"No apareció la tarea '{texto}' en {timeout}s")

    def wait_for_task_to_disappear(self, texto: str, timeout: int = 60, refresh_cada: float = 2.0):
        """
        Refresca la home y espera a que la tarea con 'texto' YA NO se vea (desasignación).

        Útil para verificar que una tarea fue reasignada a otro usuario.

        Args:
            texto: Texto de la tarea a buscar
            timeout: Tiempo máximo de espera en segundos
            refresh_cada: Frecuencia de refresco en segundos
        """
        from utils.elements import esperar_notificaciones_y_cargas

        xp = (
            f"//div[contains(@class,'task-item')]//span[contains(normalize-space(.), \"{texto}\")]"
            f"|//div[contains(@class,'form') and contains(normalize-space(.), \"{texto}\")]"
            f"|//*[@id='task-info']//span[contains(normalize-space(.), \"{texto}\")]"
        )

        fin = time.time() + timeout
        while time.time() < fin:
            try:
                self.driver.get(self.base_url)
            except Exception:
                pass

            esperar_notificaciones_y_cargas(self.driver, self.wait, timeout=20)

            if not self.driver.find_elements(By.XPATH, xp):
                return

            time.sleep(refresh_cada)

    def send_and_return_to_list(
        self,
        texto_expected: Optional[str] = None,
        timeout: int = 30,
        max_reintentos: int = 2
    ):
        """
        Intenta (re)enviar y confirma que volvimos a la lista.

        Si se pasa texto_expected, además espera que esa tarea esté visible/clickeable.

        Args:
            texto_expected: Texto de tarea que debe estar visible tras enviar
            timeout: Tiempo máximo de espera en segundos
            max_reintentos: Número máximo de intentos de envío

        Raises:
            TimeoutException: Si no se logra volver a la lista tras todos los intentos
        """
        from utils.elements import enviar_y_confirmar, esperar_notificaciones_y_cargas

        for intento in range(max_reintentos):
            try:
                enviar_y_confirmar(self.driver, self.wait)  # botón verde + azul (si aparece)
            except Exception:
                pass

            esperar_notificaciones_y_cargas(self.driver, self.wait, timeout=25)

            # ¿Ya estamos en la lista/vista de tareas?
            try:
                self.wait.until(EC.presence_of_element_located((
                    By.XPATH, "//*[@id='task-info' or contains(@class,'tasks') or contains(@class,'task-list')]"
                )))
                print("✅ Volvimos a la lista de tareas")

                # Si debemos verificar que una tarea concreta ya esté visible:
                if texto_expected:
                    self.wait_for_tasks_list(texto_expected, timeout=timeout)
                return

            except TimeoutException:
                # Seguimos dentro: intenta pulsar el ÚLTIMO botón verde visible y repite
                self._try_click_last_green_button()

        raise TimeoutException("No se consiguió volver a la lista tras enviar.")

    def _try_click_last_green_button(self):
        """Intenta hacer click en el último botón verde visible."""
        try:
            greens = self.driver.find_elements(By.XPATH, "//button[contains(@class,'btn-green')]")
            if greens:
                btn = greens[-1]
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                self.driver.execute_script("arguments[0].click();", btn)
        except Exception:
            pass
