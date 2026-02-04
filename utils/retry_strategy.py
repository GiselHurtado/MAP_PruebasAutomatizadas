# utils/retry_strategy.py
"""
RetryStrategy - Estrategias de Reintentos con Backoff

Clase especializada para manejar operaciones frágiles de Selenium con reintentos
inteligentes, backoff exponencial y recuperación de errores.

Esta clase fue extraída de FlowP1 como parte del patrón de refactorización
"Single Responsibility Principle".

Responsabilidades:
- Reintentos con backoff exponencial para abrir tareas
- Envío robusto con manejo de overlays y elementos no interactuables
- Recuperación de errores de UI (overlays, notificaciones, etc.)

Uso:
    from utils.retry_strategy import RetryStrategy

    retry = RetryStrategy(driver, wait)
    retry.retry_open_task("TEBSA - F1a. Permisos de Trabajo", intentos=3)
    retry.robust_send_confirm(max_reintentos=4)
"""
import time
from typing import Optional, Tuple
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


class RetryStrategy:
    """Estrategias de reintentos para operaciones frágiles de Selenium."""

    def __init__(self, driver, wait):
        """
        Args:
            driver: WebDriver de Selenium
            wait: WebDriverWait configurado
        """
        self.driver = driver
        self.wait = wait

    def retry_open_task(
        self,
        texto: str,
        descripcion: Optional[str] = None,
        intentos: int = 3,
        backoff: Tuple[float, ...] = (0.8, 1.2, 2.0)
    ):
        """
        Intenta abrir una tarea por texto con reintentos y backoff exponencial.

        Estrategia:
        1. Esperar que desaparezcan notificaciones/cargas
        2. Buscar y hacer click en la tarea
        3. Si falla, hacer scroll y esperar según backoff
        4. Reintentar hasta agotar intentos

        Args:
            texto: Texto de la tarea a buscar
            descripcion: Descripción para logs (opcional, usa texto por defecto)
            intentos: Número máximo de intentos
            backoff: Tupla con tiempos de espera en segundos para cada intento

        Raises:
            TimeoutException: Si no se pudo abrir tras todos los intentos
        """
        from utils.elements import esperar_notificaciones_y_cargas, abrir_tarea_por_texto

        last = None
        for i in range(intentos):
            try:
                esperar_notificaciones_y_cargas(self.driver, self.wait, timeout=30)
                abrir_tarea_por_texto(self.driver, self.wait, texto, descripcion or texto)
                return
            except TimeoutException as e:
                last = e
                # Intenta hacer scroll para revelar el elemento
                try:
                    self.driver.execute_script("window.scrollBy(0, 300);")
                except Exception:
                    pass
                # Espera según backoff exponencial
                time.sleep(backoff[min(i, len(backoff) - 1)])

        raise last or TimeoutException(f"No se pudo abrir '{texto}' tras {intentos} intentos")

    def robust_send_confirm(self, max_reintentos: int = 4):
        """
        Intenta enviar y confirmar con reintentos robustos.

        Si el botón no es interactuable, ejecuta estrategias de recuperación:
        - Cierra overlays y notificaciones
        - Hace scroll al pie de la página
        - Fuerza click con JavaScript sobre el último botón visible

        Args:
            max_reintentos: Número máximo de reintentos

        Raises:
            TimeoutException: Si no se pudo enviar/confirmar tras todos los reintentos
        """
        from utils.elements import enviar_y_confirmar, esperar_notificaciones_y_cargas

        for intento in range(1, max_reintentos + 1):
            try:
                # Intento normal
                enviar_y_confirmar(self.driver, self.wait)
                return
            except Exception as e:
                print(f"⚠️ Reintento enviar_y_confirmar (intento {intento}): {e.__class__.__name__}")

                # Estrategia 1: Cerrar overlays y quitar foco
                self._close_overlays()

                # Estrategia 2: Scroll al pie
                self._scroll_to_bottom()

                # Estrategia 3: Click forzado por JS al botón verde visible más profundo
                success = self._force_click_send_button()

                if success:
                    # Esperar fin de notificaciones/cargas y salir OK
                    esperar_notificaciones_y_cargas(self.driver, self.wait, timeout=20)
                    return

        raise TimeoutException(f"No se pudo enviar/confirmar tras {max_reintentos} reintentos.")

    def _close_overlays(self):
        """Cierra overlays molestos (notificaciones, popups, menús)."""
        try:
            self.driver.execute_script("""
                if (document.activeElement && document.activeElement.blur) {
                    document.activeElement.blur();
                }
                const sels = ['.MuiBackdrop-root','.MuiModal-root','.MuiPopover-root','.MuiMenu-root',
                            '[role="dialog"]','[role="menu"]','.popup','.dialog'];
                document.querySelectorAll(sels.join(',')).forEach(el => {
                    try { el.style.display='none'; } catch(_) { }
                });
                window.dispatchEvent(new Event('resize'));
            """)
        except Exception:
            pass

    def _scroll_to_bottom(self):
        """Hace scroll al final de la página."""
        try:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        except Exception:
            pass

    def _force_click_send_button(self) -> bool:
        """
        Fuerza click por JS al botón verde 'Enviar' visible más profundo.

        Returns:
            bool: True si se hizo click exitosamente, False en caso contrario
        """
        try:
            candidatos = self.driver.find_elements(
                By.XPATH,
                "//button[contains(@class,'btn-green') or contains(translate(., 'ENVIAR', 'enviar'), 'enviar')]"
            )
            visibles = [b for b in candidatos if b.is_displayed()]

            if not visibles:
                return False

            btn = visibles[-1]
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            self.driver.execute_script("arguments[0].click();", btn)

            # Confirmar si aparece diálogo azul
            self._click_confirm_button_if_present()

            return True

        except Exception:
            return False

    def _click_confirm_button_if_present(self):
        """Hace click en botón azul de confirmación si aparece."""
        try:
            confs = self.driver.find_elements(
                By.XPATH,
                "//button[contains(@class,'btn-blue') or contains(translate(., 'CONFIRMAR', 'confirmar'), 'confirmar')]"
            )
            confs_vis = [c for c in confs if c.is_displayed()]

            if confs_vis:
                self.driver.execute_script("arguments[0].click();", confs_vis[-1])

        except Exception:
            pass
